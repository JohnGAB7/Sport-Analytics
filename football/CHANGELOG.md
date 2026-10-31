# Changelog

## [0.1.0] – 2026-10-31
### Ajouté
- Dossier `football/`, sur le modèle de `nba/`.
- Source football-data.co.uk (résultats + cotes moyennes et de clôture) et The Odds API (cotes 1X2 du jour).
- Modèles : fréquences, Poisson, Dixon-Coles avec pondération temporelle et pénalité ridge.
- Mesures 1X2 : Brier, RPS, log-loss, calibration, probabilités implicites.
- Backtest semaine par semaine (`scripts/backtest.py`) et simulation de paris.
- Registre de paris fictifs (`paper_trading.py`, `scripts/daily_update.py`) et workflows
  `football_daily.yml` (quotidien) et `football_backtest.yml` (pull requests).
- 42 tests pytest, dont absence de fuite d'information et script quotidien de bout en bout.
