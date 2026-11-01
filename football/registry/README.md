# Registre des paris fictifs football

Rempli automatiquement chaque jour par `.github/workflows/football_daily.yml`. **Aucune mise réelle.**

| Fichier | Contenu |
|---|---|
| `paper_bets.csv` | Une ligne par match : probabilités du modèle et cotes notées **avant** le match, puis le résultat |
| `report.json` | Bilan à jour, global et par championnat |

## Lire `report.json`
- `rps_model` contre `rps_market` (idem `brier_` et `log_loss_`) : le plus petit prédit le mieux.
  Si le modèle ne bat pas le marché, il n'a aucune raison de gagner de l'argent.
- `profit_units` : gain ou perte cumulé, pour une mise fictive de 1 par pari.
- `roi` et `roi_std_error` : tant que le ROI ne dépasse pas environ 2 fois son erreur type, le
  résultat peut être dû au hasard. Il faut plusieurs centaines de paris pour conclure.
- `unmatched_teams` : noms d'équipes non reconnus (pas de pari sur ces matchs) ; à ajouter dans `teams.py`.

## Règles
Prévision enregistrée entre 36 h et 30 min avant le match, une seule fois par match, cote médiane
des bookmakers, pari seulement si l'espérance dépasse 5 % et la cote 5,0 au plus, lignes jamais
réécrites (l'historique Git le prouve).
