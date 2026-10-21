"""Schéma de référence de la table des matchs (une ligne = un match).

Ce schéma est volontairement minimal : il contient uniquement ce qui est
nécessaire pour contrôler la qualité des données et calculer des statistiques
descriptives. Il sera enrichi plus tard (cotes, statistiques d'équipe, etc.).
"""

# Colonnes obligatoires et type attendu après conversion.
EXPECTED_DTYPES = {
    "game_id": "string",        # identifiant unique du match
    "season": "int64",          # saison, nommée d'après l'année de fin (2024 = 2023-24)
    "game_date": "datetime64",  # résolution (ns/us) selon la version de pandas
    "home_team": "string",      # code équipe à domicile
    "away_team": "string",      # code équipe à l'extérieur
    "home_pts": "Int64",        # points de l'équipe à domicile (entier nullable)
    "away_pts": "Int64",
    "is_playoffs": "boolean",
}

REQUIRED_COLUMNS = list(EXPECTED_DTYPES)

# Bornes de plausibilité (hypothèses documentées dans docs/LIMITATIONS.md).
MIN_PLAUSIBLE_PTS = 50
MAX_PLAUSIBLE_PTS = 200

# Une saison NBA commence en octobre (année N-1) et finit au plus tard en juin (année N).
# Les mois de juillet à septembre sont hors saison (sauf cas exceptionnels, ex. 2020).
SEASON_START_MONTH = 8  # à partir d'août, une date appartient à la saison suivante
