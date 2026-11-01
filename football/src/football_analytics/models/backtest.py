"""Backtest chronologique (« walk-forward ») des modèles 1X2.

Pour chaque semaine d'une saison de test, chaque modèle est ré-estimé avec les seuls matchs
joués AVANT le lundi de cette semaine, puis prévoit les matchs de la semaine. C'est ce qu'on
aurait pu faire en temps réel. Le marché (cotes) est évalué sur les mêmes matchs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .baseline import frequencies
from .evaluation import OUTCOMES, implied_probabilities, outcome_code
from .poisson import ModelParams, fit

POISSON = ModelParams(dixon_coles=False)
DIXON_COLES = ModelParams(dixon_coles=True)


def _put(out: pd.DataFrame, name: str, p: np.ndarray) -> None:
    for k, o in enumerate(OUTCOMES):
        out[f"{name}_{o}"] = p[:, k]


def add_market(matches: pd.DataFrame) -> pd.DataFrame:
    """Probabilités implicites des cotes avant-match (`market`) et de clôture (`closing`)."""
    out = matches.copy()
    for name, cols in (("market", ["odds_home", "odds_draw", "odds_away"]),
                       ("closing", ["close_home", "close_draw", "close_away"])):
        p, margin = implied_probabilities(out[cols].to_numpy(float))
        _put(out, name, p)
        out[f"{name}_margin"] = margin
    return out


def walk_forward(history: pd.DataFrame, league: str, test_seasons, train_seasons: int = 3,
                 models: dict[str, ModelParams] | None = None) -> pd.DataFrame:
    """Prévisions hors échantillon de chaque modèle pour un championnat.

    `train_seasons` : nombre de saisons complètes précédentes utilisées en plus des matchs
    déjà joués de la saison en cours.
    """
    models = models or {"poisson": POISSON, "dixon_coles": DIXON_COLES}
    lg = history[history["league"] == league].copy()
    lg["date"] = pd.to_datetime(lg["date"])
    preds = []
    for season in test_seasons:
        past = lg[(lg["season"] >= season - train_seasons) & (lg["season"] <= season)]
        test = past[past["season"] == season].copy()
        if test.empty:
            continue
        test["week"] = test["date"] - pd.to_timedelta(test["date"].dt.weekday, unit="D")
        for week, games in test.groupby("week", sort=True):
            train = past[past["date"] < week]
            out = games.copy()
            _put(out, "freq", np.tile(frequencies(train), (len(out), 1)))
            for name, params in models.items():
                m = fit(train, week, params)
                _put(out, name, m.predict(out["home_team"], out["away_team"]))
            preds.append(out)
    res = pd.concat(preds, ignore_index=True).drop(columns="week")
    res["result"] = outcome_code(res["home_goals"], res["away_goals"])
    return add_market(res)


def simulate_bets(pred: pd.DataFrame, model: str, odds_cols: list[str], min_edge: float = 0.05,
                  max_odds: float = 5.0) -> pd.DataFrame:
    """Paris fictifs de 1 unité, avec la même règle que le registre en direct (paper_trading).

    `odds_cols` : cotes auxquelles on suppose pouvoir parier (ex. cotes moyennes avant-match).
    Renvoie une ligne par pari : issue choisie, cote, espérance annoncée, gain.
    """
    from ..paper_trading import choose_bet  # import local : évite une dépendance circulaire

    d = pred.dropna(subset=odds_cols)
    p = d[[f"{model}_{o}" for o in OUTCOMES]].to_numpy(float)
    o = d[odds_cols].to_numpy(float)
    rows = []
    for k in range(len(d)):
        side, odds, ev = choose_bet(p[k], o[k], min_edge, max_odds)
        if side is None:
            continue
        won = OUTCOMES.index(side) == d["result"].iloc[k]
        rows.append({"league": d["league"].iloc[k], "season": d["season"].iloc[k], "side": side,
                     "odds": odds, "ev": ev, "profit": odds - 1 if won else -1.0})
    return pd.DataFrame(rows, columns=["league", "season", "side", "odds", "ev", "profit"])


def roi_summary(bets: pd.DataFrame) -> dict:
    """Nombre de paris, gain total, ROI et son erreur type (incertitude due au hasard)."""
    n = len(bets)
    if n == 0:
        return {"bets": 0}
    roi = bets["profit"].mean()
    se = bets["profit"].std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    return {"bets": n, "profit_units": round(float(bets["profit"].sum()), 1), "roi": round(float(roi), 4),
            "roi_std_error": round(float(se), 4)}
