"""Correspondance des noms d'équipe entre sources (NBA actuelle, 30 franchises).

Clé commune : l'abréviation BALLDONTLIE. `FRANCHISE` donne le nom de franchise utilisé
par FiveThirtyEight, pour que les notes Elo continuent sans rupture après 2015.
"""

from __future__ import annotations

# abréviation -> (surnom tel qu'il apparaît en fin de nom complet, franchise FiveThirtyEight)
TEAMS = {
    "ATL": ("Hawks", "Hawks"), "BOS": ("Celtics", "Celtics"), "BKN": ("Nets", "Nets"),
    "CHA": ("Hornets", "Hornets"), "CHI": ("Bulls", "Bulls"), "CLE": ("Cavaliers", "Cavaliers"),
    "DAL": ("Mavericks", "Mavericks"), "DEN": ("Nuggets", "Nuggets"), "DET": ("Pistons", "Pistons"),
    "GSW": ("Warriors", "Warriors"), "HOU": ("Rockets", "Rockets"), "IND": ("Pacers", "Pacers"),
    "LAC": ("Clippers", "Clippers"), "LAL": ("Lakers", "Lakers"), "MEM": ("Grizzlies", "Grizzlies"),
    "MIA": ("Heat", "Heat"), "MIL": ("Bucks", "Bucks"), "MIN": ("Timberwolves", "Timberwolves"),
    "NOP": ("Pelicans", "Pelicans"), "NYK": ("Knicks", "Knicks"), "OKC": ("Thunder", "Thunder"),
    "ORL": ("Magic", "Magic"), "PHI": ("76ers", "Sixers"), "PHX": ("Suns", "Suns"),
    "POR": ("Trail Blazers", "Trailblazers"), "SAC": ("Kings", "Kings"), "SAS": ("Spurs", "Spurs"),
    "TOR": ("Raptors", "Raptors"), "UTA": ("Jazz", "Jazz"), "WAS": ("Wizards", "Wizards"),
}
FRANCHISE = {abbr: fran for abbr, (_, fran) in TEAMS.items()}


def abbr_from_full_name(full_name: str) -> str:
    """« Los Angeles Clippers », « LA Clippers » -> « LAC ». Lève une erreur si inconnu."""
    name = full_name.strip()
    matches = [abbr for abbr, (nick, _) in TEAMS.items() if name.endswith(nick)]
    if len(matches) != 1:
        raise KeyError(f"Équipe non reconnue : {full_name!r}")
    return matches[0]
