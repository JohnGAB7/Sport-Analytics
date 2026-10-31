# TODO

1. Le marché bat le modèle (RPS 0,1956 contre 0,2019) : piste la plus utile, combiner modèle et cotes
   (ex. régression sur les probabilités implicites) et vérifier si le mélange bat la clôture.
2. Laisser tourner le registre de paris fictifs au moins une saison avant toute conclusion.
3. Surveiller `unmatched_teams` dans `registry/report.json` et compléter `ALIASES` dans `teams.py`.
4. Meilleur traitement des équipes promues (données de 2e division : E1, SP2, I2, D2, F2).
5. Méthode de Shin pour retirer la marge des bookmakers (biais favori-outsider).
6. Marchés plus/moins de 2,5 buts (le modèle donne déjà la matrice des scores).
