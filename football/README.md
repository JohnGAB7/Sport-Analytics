# Football Analytics : prévisions 1X2 et paris fictifs

Équivalent football du dossier [`../nba/`](../nba/). **Aucune mise d'argent réelle.**

- Championnats : Premier League, LaLiga, Serie A, Bundesliga, Ligue 1.
- Modèles : fréquences historiques (référence), Poisson, Dixon-Coles.
- Backtest hors échantillon contre les cotes réelles (moyennes avant-match et clôture Pinnacle).
- Registre quotidien de paris fictifs, enregistrés avant les matchs puis réglés automatiquement.

## Installation (Python 3.10 ou plus)
```bash
cd football
pip install -r requirements.txt
python -m pytest -q                 # 42 tests, sans réseau
```

## Utilisation
```bash
python scripts/backtest.py          # backtest 2020-2026, ~5 min, écrit reports/backtest.md
ODDS_API_KEY=... python scripts/daily_update.py   # une mise à jour du registre
```
Sur GitHub, deux workflows s'en chargent :
- `Football - paris fictifs quotidiens` (`.github/workflows/football_daily.yml`) : chaque jour à 08:00 UTC,
  avec le secret `ODDS_API_KEY` déjà créé pour la NBA.
  Les jours où il y a du nouveau, il publie le bilan en commentaire de l'issue « Bilan quotidien des
  paris fictifs ». Vous le recevez par e-mail si vous êtes assigné à l'issue (notifications GitHub activées) ;
- `Football - tests et backtest` (`.github/workflows/football_backtest.yml`) : à chaque pull request
  qui touche `football/`, ou à la main. Les résultats s'affichent dans l'onglet « Summary ».

## Organisation
```
football/
├── src/football_analytics/
│   ├── leagues.py            championnats et codes des sources
│   ├── teams.py              rapprochement des noms d'équipes entre sources
│   ├── paper_trading.py      registre de paris fictifs (enregistrement, règlement, bilan)
│   ├── sources/
│   │   ├── footballdata.py   résultats + cotes historiques (football-data.co.uk)
│   │   └── oddsapi.py        cotes du jour (The Odds API)
│   └── models/
│       ├── baseline.py       fréquences H / D / A
│       ├── poisson.py        Poisson et Dixon-Coles (maximum de vraisemblance pondéré)
│       ├── evaluation.py     Brier, RPS, log-loss, calibration, probabilités implicites
│       └── backtest.py       backtest chronologique semaine par semaine
├── scripts/                  backtest.py, daily_update.py
├── registry/                 registre de paris fictifs (rempli par GitHub Actions)
└── tests/
```
Voir aussi `MODEL_CARD.md` (modèle, résultats, limites), `docs/DATA_SOURCES.md`, `CHANGELOG.md`, `TODO.md`.
