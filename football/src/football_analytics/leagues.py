"""Championnats suivis et codes de chaque source.

`fd_code` : nom de fichier sur football-data.co.uk ; `odds_key` : clé de The Odds API.
Une saison est désignée par l'année où elle se termine : 2026 = saison 2025-26
(même convention que le dossier nba/).
"""

from __future__ import annotations

import pandas as pd

LEAGUES = {
    "EPL": {"name": "Premier League", "fd_code": "E0", "odds_key": "soccer_epl"},
    "LIGA": {"name": "LaLiga", "fd_code": "SP1", "odds_key": "soccer_spain_la_liga"},
    "SERIEA": {"name": "Serie A", "fd_code": "I1", "odds_key": "soccer_italy_serie_a"},
    "BUNDES": {"name": "Bundesliga", "fd_code": "D1", "odds_key": "soccer_germany_bundesliga"},
    "LIGUE1": {"name": "Ligue 1", "fd_code": "F1", "odds_key": "soccer_france_ligue_one"},
}


def season_of(date) -> int:
    """Saison d'une date : à partir de juillet, on est dans la saison qui se termine l'an suivant."""
    d = pd.Timestamp(date)
    return d.year + 1 if d.month >= 7 else d.year


def season_code(season: int) -> str:
    """Code de saison de football-data.co.uk : 2026 -> '2526'."""
    return f"{(season - 1) % 100:02d}{season % 100:02d}"
