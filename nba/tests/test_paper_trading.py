"""Tests de la chaîne de paris fictifs, sans appel réseau (réponses simulées)."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nba_analytics import paper_trading as pt
from nba_analytics import quality
from nba_analytics.models.elo import EloParams, elo_state, predict, run_elo
from nba_analytics.sources import balldontlie as bdl
from nba_analytics.sources import oddsapi
from nba_analytics.synthetic import generate_games
from nba_analytics.teams import abbr_from_full_name

NOW = pd.Timestamp("2026-10-22T15:00:00Z")


def bdl_game(i, date, home, away, hs, vs, status="Final", season=2026):
    return {"id": i, "date": date, "season": season, "status": status,
            "status_state": status.lower() if status == "Final" else "scheduled",
            "postseason": False, "home_team_score": hs, "visitor_team_score": vs,
            "home_team": {"abbreviation": home}, "visitor_team": {"abbreviation": away}}


def odds_event(eid, start, home, away, prices):
    return {"id": eid, "commence_time": start, "home_team": home, "away_team": away,
            "bookmakers": [{"key": f"b{j}", "markets": [{"key": "h2h", "outcomes": [
                {"name": home, "price": ph}, {"name": away, "price": pa}]}]}
                for j, (ph, pa) in enumerate(prices)]}


class FakeResponse:
    def __init__(self, body, headers=None):
        self._body, self.headers = body, headers or {}

    def raise_for_status(self):
        pass

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, pages):
        self.pages, self.calls = list(pages), []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(dict(params or {}))
        return self.pages.pop(0)


def test_noms_d_equipes():
    assert abbr_from_full_name("Los Angeles Clippers") == "LAC"
    assert abbr_from_full_name("LA Clippers") == "LAC"
    assert abbr_from_full_name("Portland Trail Blazers") == "POR"
    assert abbr_from_full_name("Philadelphia 76ers") == "PHI"
    with pytest.raises(KeyError):
        abbr_from_full_name("Seattle SuperSonics")


def test_balldontlie_pagination_et_conversion():
    pages = [FakeResponse({"data": [bdl_game(1, "2026-10-20", "BOS", "NYK", 110, 100)], "meta": {"next_cursor": 7}}),
             FakeResponse({"data": [bdl_game(2, "2026-10-21", "LAL", "GSW", 0, 0, status="7:30 pm ET")],
                           "meta": {"next_cursor": None}})]
    session, waits = FakeSession(pages), []
    raw = bdl.fetch_games("cle", "2026-10-20", "2026-10-21", session=session, sleep=waits.append)
    assert len(raw) == 2 and session.calls[1]["cursor"] == 7 and waits == [bdl.MIN_SECONDS_BETWEEN_CALLS]
    g = bdl.to_games(raw)
    assert g["game_id"].tolist() == ["BDL1"]          # le match non terminé est ignoré
    assert g.loc[0, "season"] == 2027                 # saison 2026-27
    assert g.loc[0, "home_franchise"] == "Celtics"


def test_odds_api_conversion():
    ev = [odds_event("e1", "2026-10-23T00:00:00Z", "Boston Celtics", "New York Knicks", [(1.5, 2.6), (1.55, 2.5)])]
    o = oddsapi.to_odds(ev, NOW.isoformat())
    assert o["home_team"].tolist() == ["BOS", "BOS"] and o["odds_away"].tolist() == [2.6, 2.5]


def test_predict_coherent_avec_run_elo():
    g, _ = quality.coerce_types(generate_games(seasons=[2023, 2024], seed=3))
    g = g.assign(home_franchise=g.home_team, away_franchise=g.away_team, neutral_site=False)
    params = EloParams(k=20, home_advantage=80)
    full = run_elo(g, params)
    _, ratings, last = elo_state(g.iloc[:-1], params)
    last_game = g.iloc[-1]
    p = predict(ratings, last, last_game.home_team, last_game.away_team, int(last_game.season), params)
    assert p == pytest.approx(full["p_elo"].iloc[-1])


def make_odds(start="2026-10-23T00:00:00Z", prices=((2.0, 1.9), (2.1, 1.8))):
    return oddsapi.to_odds([odds_event("e1", start, "Boston Celtics", "New York Knicks", prices)], NOW.isoformat())


def test_pari_si_esperance_suffisante():
    reg = pt.new_entries(make_odds(), pt.empty_registry(), lambda h, a, t: (0.60, 2027), NOW)
    row = reg.iloc[0]
    assert row["odds_home"] == pytest.approx(2.05)  # médiane des bookmakers
    assert row["bet_side"] == "home" and row["bet_ev"] == pytest.approx(0.6 * 2.05 - 1, abs=1e-4)


def test_pas_de_pari_sans_avantage():
    reg = pt.new_entries(make_odds(), pt.empty_registry(), lambda h, a, t: (0.48, 2027), NOW)
    assert pd.isna(reg.iloc[0]["bet_side"]) and reg.iloc[0]["stake"] == 0


def test_match_trop_proche_ou_deja_enregistre_ignore():
    soon = make_odds(start=(NOW + pd.Timedelta(minutes=10)).isoformat())
    assert pt.new_entries(soon, pt.empty_registry(), lambda h, a, t: (0.6, 2027), NOW).empty
    first = pt.new_entries(make_odds(), pt.empty_registry(), lambda h, a, t: (0.6, 2027), NOW)
    again = pt.new_entries(make_odds(prices=((3.0, 1.4),)), first, lambda h, a, t: (0.6, 2027), NOW)
    assert again.empty  # pas de deuxième chance avec une meilleure cote


def test_reglement_veille_americaine_et_gains():
    reg = pt.new_entries(make_odds(), pt.empty_registry(), lambda h, a, t: (0.60, 2027), NOW)
    results = bdl.to_games([bdl_game(9, "2026-10-22", "BOS", "NYK", 101, 99)])  # 00:00 UTC = veille aux USA
    done = pt.settle(reg, results)
    assert done.loc[0, "home_win"] == 1 and done.loc[0, "profit"] == pytest.approx(1.05)
    lost = pt.settle(reg, bdl.to_games([bdl_game(9, "2026-10-22", "BOS", "NYK", 90, 99)]))
    assert lost.loc[0, "profit"] == -1.0
    assert lost.loc[0, "p_model_home"] == reg.loc[0, "p_model_home"]  # prévision intacte


def test_bilan():
    reg = pt.new_entries(make_odds(), pt.empty_registry(), lambda h, a, t: (0.60, 2027), NOW)
    rep = pt.report(pt.settle(reg, bdl.to_games([bdl_game(9, "2026-10-22", "BOS", "NYK", 101, 99)])))
    assert rep["bets_settled"] == 1 and rep["profit_units"] == pytest.approx(1.05)
    assert rep["brier_model"] == pytest.approx(0.16)


def test_script_quotidien_de_bout_en_bout(tmp_path, monkeypatch):
    """Exécute le script avec des réponses simulées et un faux historique FiveThirtyEight."""
    spec = importlib.util.spec_from_file_location("daily", Path(__file__).parents[1] / "scripts" / "daily_update.py")
    daily = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(daily)
    monkeypatch.setenv("BDL_API_KEY", "x")
    monkeypatch.setenv("ODDS_API_KEY", "y")
    for name in ("REGISTRY_DIR", "GAMES_CACHE", "REGISTRY", "REPORT"):
        monkeypatch.setattr(daily, name, tmp_path / getattr(daily, name).name)
    old = generate_games(seasons=[2015], seed=1).assign(
        home_team="BOS", away_team="NYK", home_franchise="Celtics", away_franchise="Knicks",
        neutral_site=False, league="NBA", notes=None)
    old["game_date"] = old["game_date"].dt.strftime("%Y-%m-%d")
    monkeypatch.setattr(daily.f38, "download", lambda path: path)
    monkeypatch.setattr(daily.f38, "to_games", lambda raw: old.astype(str))
    monkeypatch.setattr(daily.pd, "read_csv", _read_csv_passthrough(pd.read_csv))
    monkeypatch.setattr(daily.bdl, "fetch_games",
                        lambda key, s, e: [bdl_game(5, "2026-10-21", "BOS", "NYK", 100, 90)])
    tomorrow = (pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    monkeypatch.setattr(daily.oddsapi, "fetch_odds", lambda key: (
        [odds_event("e9", tomorrow, "Boston Celtics", "New York Knicks", [(1.8, 2.1)])], {"x-requests-remaining": "499"}))
    daily.main()
    reg = pd.read_csv(tmp_path / "paper_bets.csv")
    assert reg["event_id"].tolist() == ["e9"] and 0 < reg.loc[0, "p_model_home"] < 1
    rep = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert rep["matches_logged"] == 1 and rep["odds_api_quota"]["x-requests-remaining"] == "499"


def _read_csv_passthrough(real):
    def fake(path, *a, **k):
        if str(path).endswith("nbaallelo.csv"):
            return None  # remplacé par le faux to_games
        return real(path, *a, **k)
    return fake
