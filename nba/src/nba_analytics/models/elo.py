"""Modèle Elo pour la NBA (même famille que celui popularisé par FiveThirtyEight).

Principe : chaque franchise a une note. Avant un match, la probabilité de victoire à
domicile est
    p = 1 / (1 + 10^(-(note_dom + avantage_terrain - note_ext) / 400)).
Après le match, les deux notes bougent de K × multiplicateur × (résultat - p) : une
victoire inattendue fait gagner beaucoup de points, une victoire attendue peu.

Garanties anti-fuite : la prévision d'un match est enregistrée AVANT la mise à jour
avec son résultat, et les matchs sont traités dans l'ordre chronologique.

Entre deux saisons, chaque note revient en partie vers la moyenne (1505), car les
effectifs changent.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MEAN_RATING = 1505.0
INITIAL_RATING = 1300.0  # nouvelle franchise


@dataclass(frozen=True)
class EloParams:
    k: float = 20.0                 # vitesse d'apprentissage
    home_advantage: float = 100.0   # en points Elo (~ +3,5 points au score)
    carry_over: float = 0.75        # part de la note conservée d'une saison à l'autre
    use_margin: bool = True         # pondérer par l'écart au score


def win_probability(diff: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + 10 ** (-np.asarray(diff) / 400.0))


def margin_multiplier(margin: float, elo_diff_winner: float) -> float:
    """Multiplicateur d'écart au score (forme publiée par FiveThirtyEight).

    Grandit avec l'écart, mais moins vite quand le favori gagne (évite l'auto-renforcement).
    """
    return ((abs(margin) + 3) ** 0.8) / (7.5 + 0.006 * elo_diff_winner)


def run_elo(games: pd.DataFrame, params: EloParams = EloParams(),
            team_col_home: str = "home_franchise", team_col_away: str = "away_franchise") -> pd.DataFrame:
    """Parcourt les matchs dans l'ordre et renvoie, pour chacun, la probabilité *avant* le match.

    `games` doit contenir : game_date, season, home_pts, away_pts, neutral_site et les colonnes
    d'équipe. Les franchises (et non les codes) sont utilisées pour suivre une équipe qui déménage.
    """
    return elo_state(games, params, team_col_home, team_col_away)[0]


def elo_state(games: pd.DataFrame, params: EloParams = EloParams(),
              team_col_home: str = "home_franchise", team_col_away: str = "away_franchise"):
    """Comme `run_elo`, mais renvoie aussi l'état final : (prévisions, notes, dernière saison jouée)."""
    g = games.sort_values(["game_date", "game_id"], kind="stable")
    ratings: dict[str, float] = {}
    last_season: dict[str, int] = {}
    out_p = np.empty(len(g))
    out_h = np.empty(len(g))
    out_a = np.empty(len(g))
    neutral = g["neutral_site"].to_numpy() if "neutral_site" in g else np.zeros(len(g), bool)
    for i, (season, home, away, hp, ap) in enumerate(zip(
            g["season"].to_numpy(), g[team_col_home].to_numpy(), g[team_col_away].to_numpy(),
            g["home_pts"].to_numpy(), g["away_pts"].to_numpy())):
        for team in (home, away):
            if team not in ratings:
                ratings[team] = INITIAL_RATING
            elif last_season[team] != season:  # nouvelle saison : retour partiel vers la moyenne
                ratings[team] = params.carry_over * ratings[team] + (1 - params.carry_over) * MEAN_RATING
            last_season[team] = season
        hca = 0.0 if neutral[i] else params.home_advantage
        diff = ratings[home] + hca - ratings[away]
        p = float(win_probability(diff))
        out_p[i], out_h[i], out_a[i] = p, ratings[home], ratings[away]
        # --- mise à jour APRÈS avoir enregistré la prévision ---
        result = 1.0 if hp > ap else 0.0
        mult = 1.0
        if params.use_margin:
            winner_diff = diff if result == 1.0 else -diff
            mult = margin_multiplier(float(hp - ap), winner_diff)
        delta = params.k * mult * (result - p)
        ratings[home] += delta
        ratings[away] -= delta
    preds = pd.DataFrame({"game_id": g["game_id"].to_numpy(), "p_elo": out_p,
                          "elo_home_pre": out_h, "elo_away_pre": out_a}, index=g.index)
    return preds, ratings, last_season


def predict(ratings: dict, last_season: dict, home: str, away: str, season: int,
            params: EloParams = EloParams(), neutral: bool = False) -> float:
    """Probabilité de victoire à domicile pour un match à venir, sans modifier l'état."""
    def current(team):
        if team not in ratings:
            return INITIAL_RATING
        r = ratings[team]
        if last_season[team] != season:
            r = params.carry_over * r + (1 - params.carry_over) * MEAN_RATING
        return r
    hca = 0.0 if neutral else params.home_advantage
    return float(win_probability(current(home) + hca - current(away)))
