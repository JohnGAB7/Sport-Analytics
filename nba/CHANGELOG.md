# Changelog

## [0.4.1] – 2026-11-05
### Sécurité
- Dépôt rendu public : audit des fichiers et de tout l'historique, aucune clé trouvée.
- `oddsapi.fetch_odds` ne laisse plus jamais la clé (présente dans l'URL) dans un message d'erreur ; 6 tests.
- Notebooks : clonage sans jeton. Guide Colab : `git push` sans afficher le jeton en cas d'échec.
- Voir `SECURITY.md` à la racine (workflows, Dependabot, `.gitignore`).

## [0.4.0] – 2026-10-22
### Ajouté
- Test en direct sans argent : `paper_trading.py`, `scripts/daily_update.py`,
  workflow GitHub Actions quotidien `.github/workflows/nba_daily.yml` (à la racine du dépôt).
- Sources BALLDONTLIE (résultats) et The Odds API (cotes du jour), avec leurs conditions dans `docs/DATA_SOURCES.md`.
- `teams.py`, `elo.predict` / `elo.elo_state`, 10 tests (44 au total), guide partie 4.

## [0.3.0] – 2026-10-22
### Ajouté
- `src/nba_analytics/models/` : référence (fréquence domicile), Elo, mesures (Brier, log-loss,
  calibration, probabilités implicites, espérance), backtest chronologique et re-réglage saisonnier.
- `notebooks/03_modele_elo.ipynb` : backtest 2000-2015.
- `MODEL_CARD.md`.
- 10 tests de modèles, dont des tests d'absence de fuite (34 au total).

## [0.2.0] – 2026-10-21
### Ajouté
- Source réelle FiveThirtyEight `nba-elo` (CC BY 4.0) : `src/nba_analytics/sources/fivethirtyeight.py`
  (téléchargement, vérification SHA-256, une ligne par match, contrôle id/date).
- `notebooks/02_donnees_reelles_fivethirtyeight.ipynb` : contrôles et statistiques sur 59 008 matchs.
- 8 tests de l'adaptateur (24 au total).
- Audit de licéité complet dans `docs/DATA_SOURCES.md` (droit européen des bases, bibliothèques, Colab).
### Modifié
- Notebooks : clonage du dépôt privé `JohnGAB7/Sport-Analytics` avec le secret Colab `GITHUB_TOKEN`.
- `docs/LIMITATIONS.md` : alertes trouvées dans les données réelles et leur explication.

## [0.1.0] – 2026-10-14
### Ajouté
- Structure du dépôt, README, `.gitignore`, `requirements.txt`, `pyproject.toml`.
- `src/nba_analytics/schema.py` : schéma de la table des matchs.
- `src/nba_analytics/synthetic.py` : générateur de matchs fictifs reproductible + injection de défauts.
- `src/nba_analytics/quality.py` : contrôles (manquants, types, dates, doublons, cohérence) et statistiques descriptives.
- `notebooks/01_chargement_controle_qualite.ipynb`.
- 16 tests pytest.
- `docs/DATA_SOURCES.md`, `docs/LIMITATIONS.md`, `docs/GUIDE_GITHUB_COLAB.md`.
