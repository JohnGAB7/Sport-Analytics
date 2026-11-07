# Changelog

## [0.2.0] – 2026-11-07
### Ajouté
- Bilan quotidien lisible (`digest.py`) : nouveaux résultats, paris du jour, bilan cumulé foot et NBA,
  avec la comparaison entre notre modèle et le marché. Le workflow le publie en commentaire de l'issue
  « Bilan quotidien des paris fictifs ». GitHub l'envoie alors par e-mail à la personne assignée,
  sans mot de passe ni adresse dans le code. Pas de bilan, donc pas d'e-mail, les jours sans nouveauté.
- Alias Deportivo La Coruña et Racing Santander.

## [0.1.1] – 2026-11-05
### Sécurité
- `oddsapi.fetch_odds` ne laisse plus jamais la clé (présente dans l'URL) dans un message d'erreur,
  donc ni dans `registry/report.json` (public) ni dans les journaux ; 6 tests.
- `daily_update.py` intercepte aussi les erreurs réseau, championnat par championnat.
- Voir `SECURITY.md` à la racine.

## [0.1.0] – 2026-10-31
### Ajouté
- Dossier `football/`, sur le modèle de `nba/`.
- Source football-data.co.uk (résultats + cotes moyennes et de clôture) et The Odds API (cotes 1X2 du jour).
- Modèles : fréquences, Poisson, Dixon-Coles avec pondération temporelle et pénalité ridge.
- Mesures 1X2 : Brier, RPS, log-loss, calibration, probabilités implicites.
- Backtest semaine par semaine (`scripts/backtest.py`) et simulation de paris.
- Registre de paris fictifs (`paper_trading.py`, `scripts/daily_update.py`) et workflows
  `football_daily.yml` (quotidien) et `football_backtest.yml` (pull requests).
- Backtest 2020-2026 contre les cotes : le marché bat le modèle partout, paris simulés ROI -12,5 % (MODEL_CARD.md).
- 42 tests pytest, dont absence de fuite d'information et script quotidien de bout en bout.
