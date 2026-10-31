# Fiche du modèle : Dixon-Coles football (v0.1.0)

## But
Estimer, avant un match, les probabilités de victoire à domicile (H), de nul (D) et de victoire
à l'extérieur (A). Outil d'analyse. **Ce n'est pas un conseil de pari.**

## Données
football-data.co.uk : résultats et cotes des 5 grands championnats européens (voir `docs/DATA_SOURCES.md`).

## Modèle
Buts domicile ~ Poisson(λ), buts extérieur ~ Poisson(ν), avec
log λ = mu + avantage domicile + attaque(dom.) - défense(ext.) et log ν = mu + attaque(ext.) - défense(dom.),
plus la correction de Dixon et Coles (1997) des scores 0-0, 1-0, 0-1, 1-1 (paramètre ρ).
Un modèle par championnat, ré-estimé avant chaque prévision sur la saison en cours et les 3 précédentes :
- poids exp(-0,0019 × ancienneté en jours) (un match d'il y a un an compte moitié moins) ;
- pénalité ridge alpha = 3 sur les forces d'équipes.
xi et alpha ont été choisis sur les saisons 2016 à 2019 uniquement (grille de 12 combinaisons,
critère RPS). Une équipe sans aucun match dans la fenêtre (promue) reçoit la moyenne des 3 équipes
les plus faibles. Code : `src/football_analytics/models/poisson.py`.

## Évaluation hors échantillon (saisons 2019-20 à 2025-26, 12 459 matchs, 5 championnats)
Ré-estimation chaque lundi avec les seuls matchs déjà joués.

| Modèle | RPS | Brier | Log-loss | Issue la plus probable correcte |
|---|---|---|---|---|
| Fréquences historiques | 0,2310 | 0,6507 | 1,0749 | 43,1 % |
| Poisson | 0,2019 | 0,5908 | 0,9911 | 52,3 % |
| **Dixon-Coles** | **0,2019** | **0,5905** | **0,9905** | 52,3 % |

Calibration Dixon-Coles (les 3 issues confondues) : écart entre probabilité annoncée et fréquence
observée de 1,1 point au plus dans les tranches de 0 à 60 %, de 2,6 points au plus de 60 à 90 %.
La tranche 90-100 % (21 cas) est trop petite pour conclure.

## Comparaison aux cotes (même période, 12 458 matchs ayant des cotes)
Calculée par le workflow « Football - tests et backtest » sur GitHub le 31/10/2026 (pandas récent, Python 3.12).

| Prévision | RPS | Brier | Log-loss | Issue la plus probable correcte |
|---|---|---|---|---|
| Dixon-Coles | 0,2019 | 0,5905 | 0,9905 | 52,3 % |
| Cotes moyennes avant-match (marge retirée) | 0,1963 | 0,5784 | 0,9729 | 53,6 % |
| Cotes de clôture Pinnacle | **0,1956** | **0,5767** | **0,9703** | 53,9 % |

**Le marché fait mieux que le modèle dans chacun des 5 championnats et chacune des 7 saisons.**

Paris fictifs simulés avec la règle du registre (espérance annoncée ≥ 5 %, cote ≤ 5) :

| Cotes utilisées | Paris | Gain (unités) | ROI | Erreur type |
|---|---|---|---|---|
| Moyennes avant-match | 6 147 | -767 | **-12,5 %** | 1,8 % |
| Clôture Pinnacle | 7 372 | -521 | **-7,1 %** | 1,7 % |

La perte dépasse la marge des bookmakers (environ 5 %) : quand le modèle croit voir une « valeur »,
c'est le plus souvent lui qui se trompe (il ignore blessures, compositions, motivation). Résultat attendu
pour un modèle qui n'utilise que les scores. Le registre en direct sert à mesurer cela honnêtement,
pas à gagner de l'argent.

Résultats sans les cotes exécutés aussi en local le 31/10/2026 (pandas 3.0.5, scipy 1.18.1), à partir
d'une copie publique des résultats football-data.co.uk : mêmes chiffres.

## Hypothèses
- La force d'une équipe se résume à une attaque et une défense, qui évoluent lentement.
- Même avantage du terrain pour toutes les équipes d'un championnat.
- Pas d'information sur les blessures, suspensions, transferts, calendrier, compositions.

## Limites
- Les équipes promues sont mal connues pendant les premières semaines.
- La pénalité ridge dépend de la somme des poids : si le dernier match date de plusieurs mois,
  les forces sont davantage tirées vers la moyenne (intersaison).
- Les cotes « moyennes » de football-data.co.uk sont relevées 1 à 3 jours avant le match ; le
  registre en direct, lui, prend la médiane des cotes 30 min à 36 h avant.
- Un ROI positif en backtest ne garantit rien : sélection des matchs, marges, limites de mise.

## Usage à proscrire
Toute décision de pari réel fondée sur ce modèle seul.
