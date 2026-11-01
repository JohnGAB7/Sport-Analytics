"""Chaîne de paris fictifs, sans appel réseau (réponses simulées)."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from conftest import simulate
from football_analytics import paper_trading as pt
from football_analytics.sources import oddsapi

NOW = pd.Timestamp("2026-10-31T08:00:00Z")


def event(eid, start, home, away, prices):
    return {"id": eid, "commence_time": start, "home_team": home, "away_team": away,
            "bookmakers": [{"key": f"b{j}", "markets": [{"key": "h2h", "outcomes": [
                {"name": home, "price": h}, {"name": away, "price": a}, {"name": "Draw", "price": d}]}]}
                for j, (h, d, a) in enumerate(prices)]}


def odds(start="2026-10-31T15:00:00Z", prices=((2.0, 3.4, 4.0), (2.1, 3.3, 3.8), (1.9, 3.5, 4.2)),
         home="Manchester United", away="Arsenal"):
    return oddsapi.to_odds([event("e1", start, home, away, prices)], NOW.isoformat())


def fixed(p, home="Man United", away="Arsenal"):
    return lambda h, a, t: (np.array(p), home, away, 2027)


def test_conversion_odds_api():
    o = odds()
    assert len(o) == 3 and o["odds_draw"].tolist() == [3.4, 3.3, 3.5]
    incomplete = event("e2", "2026-10-31T15:00:00Z", "A", "B", [(2.0, 3.0, 4.0)])
    incomplete["bookmakers"][0]["markets"][0]["outcomes"].pop()     # pas de cote « nul »
    assert oddsapi.to_odds([incomplete], NOW.isoformat()).empty


def test_pari_sur_la_meilleure_esperance():
    reg = pt.new_entries(odds(), pt.empty_registry(), fixed([0.56, 0.24, 0.20]), NOW, "EPL")
    row = reg.iloc[0]
    assert row["odds_home"] == 2.0 and row["odds_draw"] == 3.4     # médianes
    assert row["bet_side"] == "H" and row["bet_ev"] == pytest.approx(0.12)
    assert row["pm_home"] + row["pm_draw"] + row["pm_away"] == pytest.approx(1.0, abs=1e-3)
    assert row["n_bookmakers"] == 3 and row["stake"] == 1.0


def test_pas_de_pari_sans_avantage_ou_sur_gros_outsider():
    reg = pt.new_entries(odds(), pt.empty_registry(), fixed([0.48, 0.28, 0.24]), NOW, "EPL")
    assert pd.isna(reg.iloc[0]["bet_side"]) and reg.iloc[0]["stake"] == 0.0
    side, _, _ = pt.choose_bet(np.array([0.1, 0.1, 0.8]), np.array([1.2, 8.0, 6.0]))
    assert side is None                                              # cote > 5 : exclue


def test_pas_de_pari_si_equipe_non_reconnue():
    reg = pt.new_entries(odds(), pt.empty_registry(), fixed([0.7, 0.2, 0.1], home=None), NOW, "EPL")
    assert len(reg) == 1 and pd.isna(reg.iloc[0]["bet_side"])


def test_fenetre_et_enregistrement_unique():
    too_soon = odds(start="2026-10-31T08:20:00Z")
    too_far = odds(start="2026-11-02T08:00:00Z")
    assert pt.new_entries(too_soon, pt.empty_registry(), fixed([0.5, 0.3, 0.2]), NOW, "EPL").empty
    assert pt.new_entries(too_far, pt.empty_registry(), fixed([0.5, 0.3, 0.2]), NOW, "EPL").empty
    reg = pt.new_entries(odds(), pt.empty_registry(), fixed([0.5, 0.3, 0.2]), NOW, "EPL")
    assert pt.new_entries(odds(), reg, fixed([0.9, 0.05, 0.05]), NOW, "EPL").empty


def results(hg, ag, date="2026-10-31"):
    return pd.DataFrame({"league": ["EPL"], "date": [pd.Timestamp(date)], "home_team": ["Man United"],
                         "away_team": ["Arsenal"], "home_goals": [hg], "away_goals": [ag]})


def test_reglement_et_bilan():
    reg = pt.new_entries(odds(), pt.empty_registry(), fixed([0.56, 0.24, 0.20]), NOW, "EPL")
    before = reg.copy()
    settled = pt.settle(reg, results(2, 1))
    row = settled.iloc[0]
    assert row["result"] == "H" and row["profit"] == pytest.approx(1.0)
    keep = [c for c in pt.COLUMNS if c not in ("home_goals", "away_goals", "result", "profit")]
    pd.testing.assert_frame_equal(settled[keep], before[keep])      # rien d'autre n'a changé
    lost = pt.settle(reg, results(1, 1)).iloc[0]
    assert lost["result"] == "D" and lost["profit"] == -1.0
    assert pd.isna(pt.settle(reg, results(2, 1, date="2026-11-05")).iloc[0]["result"])  # autre date
    rep = pt.report(settled)
    assert rep["matches_settled"] == 1 and rep["roi"] == 1.0 and "rps_model" in rep
    assert rep["by_league"]["EPL"]["bets_settled"] == 1


def test_bilan_registre_vide():
    assert pt.report(pt.empty_registry())["matches_logged"] == 0


def test_script_quotidien_de_bout_en_bout(tmp_path, monkeypatch):
    """Le script complet, avec un historique simulé et des cotes simulées (aucun réseau)."""
    spec = importlib.util.spec_from_file_location("daily", Path(__file__).parents[1] / "scripts/daily_update.py")
    daily = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(daily)
    hist = simulate(seasons=(2025, 2026, 2027))
    hist = hist[hist["date"] < "2026-10-30"]
    monkeypatch.setenv("ODDS_API_KEY", "test")
    monkeypatch.setattr(daily, "REGISTRY_DIR", tmp_path)
    monkeypatch.setattr(daily, "REGISTRY", tmp_path / "paper_bets.csv")
    monkeypatch.setattr(daily, "REPORT", tmp_path / "report.json")
    monkeypatch.setattr(daily.fd, "load_history", lambda *a, **k: hist)
    monkeypatch.setattr(daily.pd.Timestamp, "now", staticmethod(lambda tz=None: NOW))
    calls = []

    def fake_fetch(key, sport):
        calls.append(sport)
        if sport != "soccer_epl":
            return [], {"x-requests-remaining": "490"}
        return [event("e1", "2026-10-31T15:00:00Z", "T11", "T00", [(1.5, 4.0, 6.0)]),
                event("e2", "2026-10-31T17:00:00Z", "Inconnu FC", "T03", [(2.5, 3.2, 2.9)])], {}

    monkeypatch.setattr(daily.oddsapi, "fetch_odds", fake_fetch)
    daily.main()
    reg = pd.read_csv(tmp_path / "paper_bets.csv")
    rep = json.loads((tmp_path / "report.json").read_text())
    assert calls == ["soccer_epl"] and len(reg) == 2                # pas d'historique ailleurs
    assert len(rep["errors"]) == 4
    assert rep["unmatched_teams"] == ["Inconnu FC"]
    assert reg.loc[reg["event_id"] == "e2", "bet_side"].isna().all()
    assert reg.loc[0, "p_home"] > 0.5 and reg.loc[0, "home_team"] == "T11"
    daily.main()                                                    # deuxième passage : rien de nouveau
    assert len(pd.read_csv(tmp_path / "paper_bets.csv")) == 2
