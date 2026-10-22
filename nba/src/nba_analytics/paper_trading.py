"""Registre de paris FICTIFS, enregistrés avant les matchs, puis réglés après.

Règles qui rendent le test honnête :
1. Une prévision n'est enregistrée que si le match commence plus de 30 minutes plus tard.
2. Un match n'est enregistré qu'une fois (pas de choix a posteriori du « meilleur » moment).
3. Les lignes déjà écrites ne sont jamais modifiées, sauf les colonnes de résultat.
   L'historique Git (date de chaque commit) prouve que la prévision précédait le match.
4. La cote retenue est la médiane des bookmakers (plus prudent que la meilleure cote,
   qui suppose des comptes chez tous les bookmakers).
5. Mise fictive fixe de 1 unité. Aucune somme réelle n'est engagée.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .models.evaluation import brier, expected_value, implied_probabilities

MIN_LEAD = pd.Timedelta(minutes=30)
MIN_EDGE = 0.03  # espérance minimale (3 %) pour placer un pari fictif

COLUMNS = ["event_id", "logged_at", "commence_time", "season", "home_team", "away_team",
           "p_model_home", "odds_home", "odds_away", "n_bookmakers", "p_market_home", "margin",
           "bet_side", "bet_odds", "bet_ev", "stake",
           "home_pts", "away_pts", "home_win", "profit"]


def empty_registry() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def new_entries(odds: pd.DataFrame, registry: pd.DataFrame, predict_home, now: pd.Timestamp,
                min_edge: float = MIN_EDGE) -> pd.DataFrame:
    """Prévisions et paris fictifs pour les matchs à venir pas encore enregistrés.

    `predict_home(home, away, commence_time) -> (probabilité, saison)`.
    """
    if odds.empty:
        return empty_registry()
    odds = odds.assign(commence_time=pd.to_datetime(odds["commence_time"], utc=True))
    odds = odds[(odds["commence_time"] - now > MIN_LEAD) & ~odds["event_id"].isin(registry["event_id"])]
    rows = []
    for event_id, g in odds.groupby("event_id", sort=False):
        first = g.iloc[0]
        o_home, o_away = float(g["odds_home"].median()), float(g["odds_away"].median())
        p_market, _, margin = implied_probabilities(o_home, o_away)
        p, season = predict_home(first["home_team"], first["away_team"], first["commence_time"])
        ev_home, ev_away = expected_value(p, o_home), expected_value(1 - p, o_away)
        side, bet_odds, bet_ev = None, np.nan, np.nan
        if max(ev_home, ev_away) >= min_edge:
            side, bet_odds, bet_ev = ("home", o_home, ev_home) if ev_home >= ev_away else ("away", o_away, ev_away)
        rows.append({"event_id": event_id, "logged_at": now.isoformat(),
                     "commence_time": first["commence_time"].isoformat(), "season": season,
                     "home_team": first["home_team"], "away_team": first["away_team"],
                     "p_model_home": round(p, 4), "odds_home": o_home, "odds_away": o_away,
                     "n_bookmakers": len(g), "p_market_home": round(p_market, 4), "margin": round(margin, 4),
                     "bet_side": side, "bet_odds": bet_odds,
                     "bet_ev": round(bet_ev, 4) if side else np.nan, "stake": 1.0 if side else 0.0})
    return pd.DataFrame(rows, columns=COLUMNS)


def settle(registry: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    """Remplit les résultats des matchs terminés. Ne touche à aucune autre colonne.

    Les heures de The Odds API sont en UTC ; les dates BALLDONTLIE sont des dates locales
    américaines : un match à 01:00 UTC a donc lieu la veille. On accepte J et J-1.
    """
    reg = registry.copy()
    res = results.assign(game_date=pd.to_datetime(results["game_date"]).dt.date)
    for i, row in reg[reg["home_win"].isna()].iterrows():
        utc_day = pd.Timestamp(row["commence_time"]).date()
        days = {utc_day, (pd.Timestamp(utc_day) - pd.Timedelta(days=1)).date()}
        m = res[(res["home_team"] == row["home_team"]) & (res["away_team"] == row["away_team"])
                & res["game_date"].isin(days)]
        if len(m) != 1:
            continue
        hp, ap = int(m.iloc[0]["home_pts"]), int(m.iloc[0]["away_pts"])
        home_win = int(hp > ap)
        profit = 0.0
        if row["bet_side"] in ("home", "away"):
            won = (row["bet_side"] == "home") == bool(home_win)
            profit = float(row["stake"]) * (float(row["bet_odds"]) - 1) if won else -float(row["stake"])
        reg.loc[i, ["home_pts", "away_pts", "home_win", "profit"]] = [hp, ap, home_win, round(profit, 4)]
    return reg


def report(registry: pd.DataFrame) -> dict:
    """Bilan : le modèle bat-il le marché, et les paris fictifs rapportent-ils ?"""
    done = registry.dropna(subset=["home_win"])
    bets = done[done["bet_side"].isin(["home", "away"])]
    out = {"matches_logged": len(registry), "matches_settled": len(done), "bets_settled": len(bets)}
    if len(done):
        y = done["home_win"].astype(float)
        out["brier_model"] = round(brier(done["p_model_home"].astype(float), y), 4)
        out["brier_market"] = round(brier(done["p_market_home"].astype(float), y), 4)
    if len(bets):
        profit = bets["profit"].astype(float)
        out["profit_units"] = round(profit.sum(), 2)
        out["roi"] = round(profit.sum() / bets["stake"].astype(float).sum(), 4)
        out["roi_std_error"] = round(profit.std(ddof=1) / np.sqrt(len(bets)), 4) if len(bets) > 1 else None
        out["win_rate"] = round(((bets["bet_side"] == "home") == bets["home_win"].astype(bool)).mean(), 4)
    return out
