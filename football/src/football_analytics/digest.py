"""Bilan quotidien lisible (Markdown) : nouveaux résultats, paris à venir, bilan cumulé.

Publié chaque jour en commentaire d'une issue GitHub : GitHub l'envoie alors par e-mail à la
personne assignée à l'issue, sans aucun mot de passe ni adresse dans le code.
"""

from __future__ import annotations

import pandas as pd

from .leagues import LEAGUES

SIDE = {"H": "victoire domicile", "D": "nul", "A": "victoire extérieur"}


def _teams(row) -> str:
    home = row["home_team"] if isinstance(row["home_team"], str) else row["home_name"]
    away = row["away_team"] if isinstance(row["away_team"], str) else row["away_name"]
    return f"{home} - {away}"


def _league(code) -> str:
    return LEAGUES.get(code, {}).get("name", code)


def newly_settled(before: pd.DataFrame, after: pd.DataFrame) -> pd.DataFrame:
    """Matchs dont le résultat vient d'être rempli (absent avant, présent après)."""
    was_open = set(before.loc[before["result"].isna(), "event_id"]) if len(before) else set()
    return after[after["event_id"].isin(was_open) & after["result"].notna()]


def build(settled: pd.DataFrame, added: pd.DataFrame, report: dict, nba: dict | None = None) -> str:
    lines = [f"## Bilan du {pd.Timestamp.now(tz='UTC'):%d/%m/%Y}", "", "Paris **fictifs** (1 unité par pari, aucune mise réelle).", ""]
    if len(settled):
        lines += ["### Nouveaux résultats", "", "| Championnat | Match | Score | Notre pari | Gain |", "|---|---|---|---|---|"]
        for _, r in settled.sort_values("commence_time").iterrows():
            bet = f"{SIDE[r['bet_side']]} à {float(r['bet_odds']):.2f}" if r["bet_side"] in SIDE else "pas de pari"
            gain = f"{float(r['profit']):+.2f}" if r["bet_side"] in SIDE else ""
            lines.append(f"| {_league(r['league'])} | {_teams(r)} | {int(r['home_goals'])}-{int(r['away_goals'])} "
                         f"| {bet} | {gain} |")
        lines.append("")
    bets = added[added["bet_side"].isin(SIDE)] if len(added) else added
    if len(added):
        lines += [f"### Nouveaux matchs enregistrés : {len(added)}, dont {len(bets)} paris", ""]
        if len(bets):
            lines += ["| Coup d'envoi (UTC) | Match | Pari | Cote | Notre proba / marché |", "|---|---|---|---|---|"]
            for _, r in bets.sort_values("commence_time").iterrows():
                k = {"H": "home", "D": "draw", "A": "away"}[r["bet_side"]]
                lines.append(f"| {pd.Timestamp(r['commence_time']):%d/%m %H:%M} | {_teams(r)} | {SIDE[r['bet_side']]} "
                             f"| {float(r['bet_odds']):.2f} | {float(r['p_' + k]):.0%} / {float(r['pm_' + k]):.0%} |")
            lines.append("")
    lines += ["### Où on en est (football, depuis le début)", ""]
    n = report.get("bets_settled", 0)
    lines.append(f"- Matchs suivis : {report.get('matches_logged', 0)}, terminés : {report.get('matches_settled', 0)}")
    if n:
        lines.append(f"- Paris réglés : {n}, gagnés : {report['win_rate']:.0%}, gain : {report['profit_units']:+.2f} unités "
                     f"(ROI {report['roi']:+.1%})")
        se = report.get("roi_std_error")
        if se:
            verdict = "différence significative" if abs(report["roi"]) > 2 * se else "encore compatible avec le hasard"
            lines.append(f"- Incertitude du ROI : ±{se:.1%} ({verdict})")
    if "rps_model" in report:
        better = "notre modèle" if report["rps_model"] < report["rps_market"] else "le marché"
        lines.append(f"- Précision (RPS, plus petit = mieux) : modèle {report['rps_model']:.4f}, "
                     f"marché {report['rps_market']:.4f} : avantage {better}")
    if nba and nba.get("bets_settled"):
        lines += ["", f"NBA : {nba['bets_settled']} paris réglés, gain {nba['profit_units']:+.2f} unités "
                      f"(ROI {nba['roi']:+.1%})"]
    lines += ["", "Détail : `football/registry/paper_bets.csv`. Un bilan sur quelques dizaines de paris ne prouve rien."]
    return "\n".join(lines) + "\n"
