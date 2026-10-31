"""Registre de paris FICTIFS 1X2, enregistrés avant les matchs, puis réglés après.

Règles qui rendent le test honnête (les mêmes que pour la NBA) :
1. Une prévision n'est enregistrée que si le match commence entre 30 minutes et 36 heures
   plus tard. Avec un passage par jour, chaque match est enregistré une fois, la veille ou le jour même.
2. Un match n'est enregistré qu'une fois (pas de choix a posteriori du « meilleur » moment).
3. Les lignes déjà écrites ne sont jamais modifiées, sauf les colonnes de résultat.
   L'historique Git (date de chaque commit) prouve que la prévision précédait le match.
4. La cote retenue est la médiane des bookmakers (plus prudent que la meilleure cote).
5. Mise fictive fixe de 1 unité sur l'issue à la plus forte espérance, si elle dépasse 5 %
   et si la cote ne dépasse pas 5,0 (les gros outsiders ont une variance énorme et sont
   souvent sur-cotés par les modèles). Aucune somme réelle n'est engagée.
6. Pas de pari si une des deux équipes n'a pas été reconnue avec certitude (teams.py).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .models.evaluation import OUTCOMES, brier, expected_value, implied_probabilities, log_loss, rps

MIN_LEAD = pd.Timedelta(minutes=30)
MAX_LEAD = pd.Timedelta(hours=36)
MIN_EDGE = 0.05
MAX_ODDS = 5.0

COLUMNS = ["event_id", "logged_at", "commence_time", "league", "season", "home_name", "away_name",
           "home_team", "away_team", "p_home", "p_draw", "p_away",
           "odds_home", "odds_draw", "odds_away", "n_bookmakers", "pm_home", "pm_draw", "pm_away", "margin",
           "bet_side", "bet_odds", "bet_ev", "stake", "home_goals", "away_goals", "result", "profit"]
P_MODEL, P_MARKET, ODDS = ["p_home", "p_draw", "p_away"], ["pm_home", "pm_draw", "pm_away"], \
    ["odds_home", "odds_draw", "odds_away"]


def empty_registry() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def choose_bet(p, odds, min_edge: float = MIN_EDGE, max_odds: float = MAX_ODDS):
    """(issue 'H'/'D'/'A', cote, espérance) du meilleur pari, ou (None, nan, nan)."""
    ev = expected_value(p, odds)
    ev = np.where(np.asarray(odds, float) <= max_odds, ev, -np.inf)
    k = int(np.argmax(ev))
    if ev[k] < min_edge:
        return None, np.nan, np.nan
    return OUTCOMES[k], float(odds[k]), float(ev[k])


def new_entries(odds: pd.DataFrame, registry: pd.DataFrame, predict, now: pd.Timestamp, league: str,
                min_edge: float = MIN_EDGE) -> pd.DataFrame:
    """Prévisions et paris fictifs pour les matchs à venir pas encore enregistrés.

    `predict(home_name, away_name, commence_time) -> (p[H, D, A], home_team, away_team, saison)`,
    où home_team / away_team valent None si l'équipe n'a pas été reconnue.
    """
    if odds.empty:
        return empty_registry()
    odds = odds.assign(commence_time=pd.to_datetime(odds["commence_time"], utc=True))
    lead = odds["commence_time"] - now
    odds = odds[(lead > MIN_LEAD) & (lead <= MAX_LEAD) & ~odds["event_id"].isin(registry["event_id"])]
    rows = []
    for event_id, g in odds.groupby("event_id", sort=False):
        first = g.iloc[0]
        o = g[ODDS].median().to_numpy(float)
        pm, margin = implied_probabilities(o)
        p, home, away, season = predict(first["home_name"], first["away_name"], first["commence_time"])
        p = np.asarray(p, float)
        side, bet_odds, bet_ev = (None, np.nan, np.nan) if home is None or away is None \
            else choose_bet(p, o, min_edge)
        rows.append({"event_id": event_id, "logged_at": now.isoformat(),
                     "commence_time": first["commence_time"].isoformat(), "league": league, "season": season,
                     "home_name": first["home_name"], "away_name": first["away_name"],
                     "home_team": home, "away_team": away,
                     **dict(zip(P_MODEL, np.round(p, 4))), **dict(zip(ODDS, o)), "n_bookmakers": len(g),
                     **dict(zip(P_MARKET, np.round(pm, 4))), "margin": round(float(margin), 4),
                     "bet_side": side, "bet_odds": bet_odds, "bet_ev": round(bet_ev, 4) if side else np.nan,
                     "stake": 1.0 if side else 0.0})
    return pd.DataFrame(rows, columns=COLUMNS)


def settle(registry: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    """Remplit les résultats des matchs terminés. Ne touche à aucune autre colonne.

    `results` : tableau football-data.co.uk (league, date, home_team, away_team, home_goals,
    away_goals). Les dates y sont locales ; on accepte J-1, J et J+1 par rapport à l'heure UTC.
    """
    reg = registry.copy()
    reg["result"] = reg["result"].astype(object)
    for c in ("home_goals", "away_goals", "profit"):
        reg[c] = reg[c].astype(float)
    res = results.assign(day=pd.to_datetime(results["date"]).dt.date)
    for i, row in reg[reg["result"].isna() & reg["home_team"].notna() & reg["away_team"].notna()].iterrows():
        day = pd.Timestamp(row["commence_time"]).tz_convert(None).normalize()
        days = {(day + pd.Timedelta(days=d)).date() for d in (-1, 0, 1)}
        m = res[(res["league"] == row["league"]) & (res["home_team"] == row["home_team"])
                & (res["away_team"] == row["away_team"]) & res["day"].isin(days)]
        if len(m) != 1:
            continue
        hg, ag = int(m.iloc[0]["home_goals"]), int(m.iloc[0]["away_goals"])
        result = "H" if hg > ag else ("D" if hg == ag else "A")
        profit = 0.0
        if row["bet_side"] in OUTCOMES:
            profit = float(row["stake"]) * (float(row["bet_odds"]) - 1) if row["bet_side"] == result \
                else -float(row["stake"])
        reg.loc[i, "home_goals"], reg.loc[i, "away_goals"] = hg, ag
        reg.loc[i, "result"], reg.loc[i, "profit"] = result, round(profit, 4)
    return reg


def _scores(done: pd.DataFrame) -> dict:
    y = done["result"].map({o: k for k, o in enumerate(OUTCOMES)}).to_numpy(int)
    out = {}
    for name, cols in (("model", P_MODEL), ("market", P_MARKET)):
        p = done[cols].to_numpy(float)
        out[f"rps_{name}"] = round(rps(p, y), 4)
        out[f"brier_{name}"] = round(brier(p, y), 4)
        out[f"log_loss_{name}"] = round(log_loss(p, y), 4)
    return out


def report(registry: pd.DataFrame) -> dict:
    """Bilan global et par championnat : le modèle bat-il le marché, les paris rapportent-ils ?"""
    def block(r: pd.DataFrame) -> dict:
        done = r.dropna(subset=["result"])
        bets = done[done["bet_side"].isin(OUTCOMES)]
        out = {"matches_logged": len(r), "matches_settled": len(done), "bets_settled": len(bets)}
        if len(done):
            out.update(_scores(done))
        if len(bets):
            profit = bets["profit"].astype(float)
            out["profit_units"] = round(profit.sum(), 2)
            out["roi"] = round(profit.sum() / bets["stake"].astype(float).sum(), 4)
            out["roi_std_error"] = round(profit.std(ddof=1) / np.sqrt(len(bets)), 4) if len(bets) > 1 else None
            out["win_rate"] = round(float((bets["bet_side"] == bets["result"]).mean()), 4)
        return out

    out = block(registry)
    out["by_league"] = {lg: block(g) for lg, g in registry.groupby("league")} if len(registry) else {}
    return out
