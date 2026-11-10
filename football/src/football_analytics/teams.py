"""Rapprochement des noms d'équipes : The Odds API -> football-data.co.uk.

Les deux sources n'écrivent pas les noms de la même façon (« Manchester United » contre
« Man United »). Ordre des essais :
1. table d'alias écrite à la main (cas connus) ;
2. égalité après normalisation (minuscules, sans accents, sans « FC », « AC »...) ;
3. un seul nom candidat qui contient l'autre, ou très proche (difflib, seuil 0,85).
Si rien n'est sûr, on renvoie None : le match est ignoré (et signalé dans report.json)
plutôt que de risquer d'enregistrer une prévision sur la mauvaise équipe.
"""

from __future__ import annotations

import difflib
import re
import unicodedata

DROP_TOKENS = {"fc", "cf", "afc", "ac", "as", "ss", "ssc", "sc", "rc", "bc", "vfl", "vfb", "tsg", "fsv",
               "sv", "ca", "ud", "rcd", "ogc", "us", "acf", "calcio", "1", "05", "1899", "1846", "1907", "de"}

# Clé : nom normalisé côté The Odds API. Valeur : nom exact football-data.co.uk.
ALIASES = {
    # Premier League
    "manchester united": "Man United", "manchester city": "Man City", "newcastle united": "Newcastle",
    "nottingham forest": "Nott'm Forest", "tottenham hotspur": "Tottenham", "west ham united": "West Ham",
    "wolverhampton wanderers": "Wolves", "brighton and hove albion": "Brighton", "leeds united": "Leeds",
    "leicester city": "Leicester", "ipswich town": "Ipswich", "luton town": "Luton",
    "sheffield united": "Sheffield United", "west bromwich albion": "West Brom", "norwich city": "Norwich",
    # LaLiga
    "athletic bilbao": "Ath Bilbao", "athletic club": "Ath Bilbao", "atletico madrid": "Ath Madrid",
    "real betis": "Betis", "celta vigo": "Celta", "espanyol": "Espanol", "real sociedad": "Sociedad",
    "rayo vallecano": "Vallecano", "real oviedo": "Oviedo", "real valladolid": "Valladolid",
    "deportivo alaves": "Alaves", "real mallorca": "Mallorca", "osasuna": "Osasuna",
    "deportivo la coruna": "La Coruna", "racing santander": "Santander",
    # Serie A
    "inter milan": "Inter", "internazionale": "Inter", "milan": "Milan", "roma": "Roma",
    "hellas verona": "Verona", "atalanta bc": "Atalanta",
    # Bundesliga
    "bayern munich": "Bayern Munich", "borussia dortmund": "Dortmund", "eintracht frankfurt": "Ein Frankfurt",
    "bayer leverkusen": "Leverkusen", "borussia monchengladbach": "M'gladbach",
    "mainz": "Mainz", "hamburger": "Hamburg", "koln": "FC Koln", "heidenheim": "Heidenheim",
    "st pauli": "St Pauli", "union berlin": "Union Berlin", "hertha berlin": "Hertha",
    # Ligue 1
    "paris saint germain": "Paris SG", "saint etienne": "St Etienne", "lens": "Lens",
    "monaco": "Monaco", "stade brestois 29": "Brest", "stade rennais": "Rennes",
    "olympique lyonnais": "Lyon", "olympique marseille": "Marseille", "clermont foot": "Clermont",
}


def normalize(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    words = [w for w in s.split() if w not in DROP_TOKENS]
    return " ".join(words)


def match_team(name: str, candidates) -> str | None:
    """Nom football-data.co.uk correspondant à `name`, choisi parmi `candidates` (ou None)."""
    candidates = list(dict.fromkeys(candidates))
    if name in candidates:
        return name
    key = normalize(name)
    alias = ALIASES.get(key)
    if alias in candidates:
        return alias
    norm = {c: normalize(c) for c in candidates}
    exact = [c for c, n in norm.items() if n == key]
    if len(exact) == 1:
        return exact[0]
    inside = [c for c, n in norm.items() if n and key and (n in key.split() or key in n.split()
                                                           or n.startswith(key + " ") or key.startswith(n + " "))]
    if len(inside) == 1:
        return inside[0]
    close = difflib.get_close_matches(key, list(norm.values()), n=2, cutoff=0.85)
    if len(close) == 1:
        found = [c for c, n in norm.items() if n == close[0]]
        if len(found) == 1:
            return found[0]
    return None
