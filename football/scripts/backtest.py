"""Backtest hors échantillon des modèles 1X2, comparés entre eux et aux cotes.

    python scripts/backtest.py            # saisons de test 2020 à 2026 (environ 5 minutes)

Les paramètres du modèle (xi, alpha) ont été choisis sur les saisons 2016-2019 seulement :
les saisons de test n'ont servi qu'à cette mesure finale.
Écrit le tableau dans reports/backtest.md (et dans le résumé GitHub Actions s'il existe).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_analytics.leagues import LEAGUES  # noqa: E402
from football_analytics.models import backtest as bt  # noqa: E402
from football_analytics.models import evaluation as ev  # noqa: E402
from football_analytics.sources import footballdata as fd  # noqa: E402

TEST_SEASONS = range(2020, 2027)


def md(df: pd.DataFrame) -> str:
    """Tableau Markdown simple (évite la dépendance `tabulate`)."""
    head = "| " + " | ".join([str(df.index.name or "")] + [str(c) for c in df.columns]) + " |"
    sep = "|" + "---|" * (len(df.columns) + 1)
    cell = lambda v: f"{v:g}" if isinstance(v, float) else str(v)  # noqa: E731
    body = ["| " + " | ".join([str(i)] + [cell(v) for v in row]) + " |" for i, row in zip(df.index, df.to_numpy())]
    return "\n".join([head, sep, *body])
TRAIN_SEASONS = 3


def main() -> None:
    seasons = range(min(TEST_SEASONS) - TRAIN_SEASONS, max(TEST_SEASONS) + 1)
    history = fd.load_history(LEAGUES, seasons, ROOT / "data/raw")
    pred = pd.concat([bt.walk_forward(history, lg, TEST_SEASONS, TRAIN_SEASONS) for lg in LEAGUES],
                     ignore_index=True)
    models = ["freq", "poisson", "dixon_coles"]
    lines = [f"# Backtest football ({min(TEST_SEASONS)}-{max(TEST_SEASONS)}, {len(pred)} matchs)", "",
             "Plus petit = meilleur pour RPS, Brier et log-loss. `market` : cotes moyennes relevées 1 à 3 jours",
             "avant le match ; `closing` : cotes de clôture Pinnacle (ou moyenne de clôture).", ""]

    both = pred.dropna(subset=["market_H", "closing_H"])
    lines += ["## Tous championnats (matchs ayant les deux jeux de cotes)", "",
              md(ev.summary(both, models + ["market", "closing"])), ""]
    by_league = both.groupby("league").apply(
        lambda d: ev.summary(d, models + ["market", "closing"])["rps"], include_groups=False)
    by_season = both.groupby("season").apply(
        lambda d: ev.summary(d, ["dixon_coles", "market", "closing"])["rps"], include_groups=False)
    lines += ["## RPS par championnat", "", md(by_league), ""]
    lines += ["## RPS par saison", "", md(by_season), ""]
    lines += ["## Calibration Dixon-Coles (les 3 issues confondues)", "",
              md(ev.calibration_table(pred, "dixon_coles")), ""]
    lines += ["## Paris fictifs simulés (règle du registre : espérance >= 5 %, cote <= 5)", "",
              "| Modèle | Cotes utilisées | Paris | Gain (unités) | ROI | Erreur type du ROI |", "|---|---|---|---|---|---|"]
    for model in ("poisson", "dixon_coles"):
        for label, cols in (("moyennes avant-match", ["odds_home", "odds_draw", "odds_away"]),
                            ("clôture", ["close_home", "close_draw", "close_away"])):
            r = bt.roi_summary(bt.simulate_bets(pred, model, cols))
            lines.append(f"| {model} | {label} | {r['bets']} | {r.get('profit_units')} | {r.get('roi')} | "
                         f"{r.get('roi_std_error')} |")
    lines += ["", "Un ROI n'est distinguable du hasard que s'il dépasse environ 2 fois son erreur type.",
              "Les cotes moyennes sont celles d'un bookmaker typique ; ce test ne compte ni limites de mise ni fermeture de compte."]

    text = "\n".join(lines) + "\n"
    out = ROOT / "reports/backtest.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
