# Données

| Dossier | Contenu | Versionné ? |
|---|---|---|
| `raw/` | Fichiers tels que téléchargés depuis une source validée | Non |
| `processed/` | Tables nettoyées au format du schéma | Non |
| `synthetic/` | Données fictives régénérées par le notebook | Non |

Les données ne sont pas mises dans Git : cela évite de redistribuer des données
dont la licence l'interdirait, et garantit qu'elles sont toujours reproductibles
par le code.

## Schéma de la table des matchs (`src/nba_analytics/schema.py`)

| Colonne | Type | Description |
|---|---|---|
| `game_id` | texte | Identifiant unique du match |
| `season` | entier | Saison nommée d'après l'année de fin (2024 = saison 2023-24) |
| `game_date` | date | Date du match, format ISO `AAAA-MM-JJ` recommandé |
| `home_team` | texte | Code de l'équipe à domicile |
| `away_team` | texte | Code de l'équipe à l'extérieur |
| `home_pts` | entier | Points de l'équipe à domicile, prolongations comprises |
| `away_pts` | entier | Points de l'équipe à l'extérieur |
| `is_playoffs` | booléen | Match de play-offs |
| `source` | texte | Origine de la ligne (`synthetic`, `fivethirtyeight_nbaallelo`) |

Colonnes supplémentaires de la source FiveThirtyEight : `league` (NBA/ABA), `neutral_site`,
`home_franchise`, `away_franchise`, `notes` (ex. reprise d'un match contesté).
