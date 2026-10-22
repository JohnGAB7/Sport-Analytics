"""Modèle de référence : « l'équipe à domicile gagne avec la fréquence historique ».

Pour la saison S, la probabilité est la part des victoires à domicile observée sur les
saisons strictement antérieures à S (aucune information de la saison S n'est utilisée).
Tout modèle plus complexe doit battre cette référence pour être utile.
"""

from __future__ import annotations

import pandas as pd


def home_rate_predictions(games: pd.DataFrame, window: int = 10) -> pd.Series:
    """Probabilité de victoire à domicile, calculée sur les `window` saisons précédentes."""
    win = (games["home_pts"] > games["away_pts"]).astype(float)
    by_season = win.groupby(games["season"]).agg(["sum", "count"]).sort_index()
    past = by_season.shift(1).rolling(window, min_periods=1).sum()
    rate = (past["sum"] / past["count"]).rename("p_home_rate")
    return games["season"].map(rate)
