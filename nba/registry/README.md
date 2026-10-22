# Registre des paris fictifs

Rempli automatiquement chaque jour par `.github/workflows/nba_daily.yml`. **Aucune mise réelle.**

| Fichier | Contenu |
|---|---|
| `paper_bets.csv` | Une ligne par match : prévision du modèle et cotes notées **avant** le match, puis le résultat |
| `bdl_games.csv` | Résultats NBA depuis 2015-16 (source BALLDONTLIE) |
| `report.json` | Bilan à jour |

## Lire `report.json`
- `brier_model` contre `brier_market` : le plus petit des deux prédit le mieux. Si le modèle ne
  bat pas le marché (les cotes, marge retirée), il n'a aucune raison de gagner de l'argent.
- `profit_units` : gain ou perte cumulé, pour une mise fictive de 1 par pari.
- `roi` : gain moyen par unité misée. `roi_std_error` : son incertitude. Tant que le ROI n'est
  pas supérieur à environ 2 fois cette incertitude, le résultat peut être dû au hasard.
  Il faut en général plusieurs centaines de paris pour conclure.

## Règles
Prévision enregistrée au plus tard 30 minutes avant le match, une seule fois par match, cote
médiane des bookmakers, lignes jamais réécrites (l'historique Git le prouve).
