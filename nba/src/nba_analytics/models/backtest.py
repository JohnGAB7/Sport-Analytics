"""Backtest chronologique : réglage sur des saisons passées, mesure sur des saisons futures.

Le réglage des paramètres Elo (grille) n'utilise QUE les saisons d'entraînement. Les
saisons de test ne servent qu'une fois, pour la mesure finale. Le modèle Elo continue
d'apprendre match après match pendant le test, comme il le ferait en conditions réelles
(chaque prévision n'utilise que les matchs déjà joués).
"""

from __future__ import annotations

import itertools

import pandas as pd

from .baseline import home_rate_predictions
from .elo import EloParams, run_elo
from .evaluation import brier, log_loss


def prepare(games: pd.DataFrame) -> pd.DataFrame:
    """Ajoute la variable à prédire et trie chronologiquement."""
    g = games.sort_values(["game_date", "game_id"], kind="stable").copy()
    g["home_win"] = (g["home_pts"] > g["away_pts"]).astype(int)
    return g


def grid_search(games: pd.DataFrame, train_seasons: range, grid: dict | None = None) -> pd.DataFrame:
    """Évalue chaque combinaison de paramètres sur les saisons d'entraînement seulement.

    Elo est rejoué sur tout l'historique jusqu'à la fin de l'entraînement (pour que les notes
    soient « chaudes »), mais le score n'est calculé que sur `train_seasons`.
    """
    grid = grid or {"k": [10, 15, 20, 25, 30], "home_advantage": [60, 80, 100, 120],
                    "carry_over": [0.6, 0.75, 0.9], "use_margin": [True, False]}
    history = games[games["season"] <= max(train_seasons)]
    in_train = history["season"].isin(train_seasons).to_numpy()
    y = history["home_win"].to_numpy()[in_train]
    rows = []
    for values in itertools.product(*grid.values()):
        params = EloParams(**dict(zip(grid.keys(), values)))
        p = run_elo(history, params).loc[history.index, "p_elo"].to_numpy()[in_train]
        rows.append({**dict(zip(grid.keys(), values)), "log_loss": log_loss(p, y), "brier": brier(p, y)})
    return pd.DataFrame(rows).sort_values("log_loss").reset_index(drop=True)


def backtest(games: pd.DataFrame, params: EloParams, test_seasons: range) -> pd.DataFrame:
    """Prévisions de chaque modèle pour les matchs des saisons de test."""
    p_elo = run_elo(games, params)
    out = games.assign(p_elo=p_elo["p_elo"], p_home_rate=home_rate_predictions(games),
                       p_coin=0.5)
    return out[out["season"].isin(test_seasons)]


def per_season(pred: pd.DataFrame, prob_cols: list[str]) -> pd.DataFrame:
    """Log-loss par saison et par modèle (pour voir la stabilité dans le temps)."""
    return pred.groupby("season").apply(
        lambda d: pd.Series({c: log_loss(d[c], d["home_win"]) for c in prob_cols}),
        include_groups=False).round(4)


WALK_FORWARD_GRID = {"k": [15, 20, 25], "home_advantage": [40, 60, 80, 100, 120],
                     "carry_over": [0.75], "use_margin": [True]}


def walk_forward(games: pd.DataFrame, test_seasons: range, train_window: int = 10,
                 grid: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Avant chaque saison de test, re-règle Elo sur les `train_window` saisons précédentes.

    Plus réaliste qu'un réglage unique : l'avantage du terrain a évolué dans le temps.
    Renvoie les prévisions des saisons de test et les paramètres choisis à chaque saison.
    """
    grid = grid or WALK_FORWARD_GRID
    preds, chosen = [], []
    for season in test_seasons:
        train = range(season - train_window, season)
        best = grid_search(games, train, grid).iloc[0]
        params = EloParams(k=float(best["k"]), home_advantage=float(best["home_advantage"]),
                           carry_over=float(best["carry_over"]), use_margin=bool(best["use_margin"]))
        history = games[games["season"] <= season]
        p = run_elo(history, params)["p_elo"]
        preds.append(history.assign(p_elo_wf=p)[history["season"] == season])
        chosen.append({"season": season, "k": params.k, "home_advantage": params.home_advantage})
    return pd.concat(preds), pd.DataFrame(chosen).set_index("season")
