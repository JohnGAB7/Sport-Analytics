# Sources de données football

| Source | Contenu | Coût | Utilisation |
|---|---|---|---|
| [football-data.co.uk](https://www.football-data.co.uk/data.php) | Résultats et cotes 1X2 (moyennes, Pinnacle, clôture) depuis les années 1990 | Gratuit | Historique, backtest, règlement des paris fictifs |
| [The Odds API](https://the-odds-api.com) | Cotes du jour de nombreux bookmakers | Gratuit jusqu'à 500 crédits/mois | Cotes au moment de la prévision |

## Conditions
- **football-data.co.uk** met ses fichiers à disposition gratuitement pour un usage personnel.
  Avant toute utilisation commerciale (vente d'analyses, service de données), il faut relire ses
  conditions et, au besoin, demander l'autorisation à l'auteur. Les fichiers téléchargés ne sont pas
  versionnés (`data/raw/` est ignoré par Git) ; le registre ne contient que nos propres prévisions,
  les cotes relevées via The Odds API et les scores finaux.
- **The Odds API** : 1 crédit par championnat et par appel (`markets=h2h`, une région). Football :
  5 crédits par jour, environ 150 par mois ; NBA : environ 30 par mois. Total sous les 500 gratuits.
  Le solde est affiché dans `registry/report.json` (`odds_api_quota`).

## Colonnes utilisées de football-data.co.uk
`Date`, `HomeTeam`, `AwayTeam`, `FTHG`, `FTAG` ; cotes avant-match `AvgH/D/A` (sinon `BbAvH/D/A`,
sinon `B365H/D/A`) ; cotes de clôture `PSCH/D/A` (sinon `AvgCH/D/A`).
Description officielle : https://www.football-data.co.uk/notes.txt.
