# Fiche du modèle : Elo NBA (v0.3.0)

## But
Estimer, avant un match NBA, la probabilité que l'équipe à domicile gagne.
Outil d'analyse. **Ce n'est pas un conseil de pari.**

## Données
FiveThirtyEight `nbaallelo.csv` (CC BY 4.0, d'après Basketball-Reference.com), 59 008 matchs
NBA de 1946-47 à 2014-15. Voir `docs/DATA_SOURCES.md` et `docs/LIMITATIONS.md`.

## Modèle
Elo par franchise : note initiale 1300, retour vers 1505 entre les saisons, avantage du terrain
et vitesse K réglés sur le passé, pondération par l'écart au score (forme FiveThirtyEight).
Code : `src/nba_analytics/models/elo.py`. Il reproduit les prévisions publiées par
FiveThirtyEight (écart médian 3 × 10⁻⁷) quand on lui donne leurs paramètres.

## Évaluation (hors échantillon, saisons 2000 à 2015, 20 546 matchs)
Réglage refait avant chaque saison sur les 10 saisons précédentes uniquement.

| Modèle | Brier | Log-loss | Favori gagnant |
|---|---|---|---|
| Pile ou face | 0,2500 | 0,6931 | sans objet |
| Fréquence historique domicile | 0,2394 | 0,6718 | 60,3 % |
| Elo, réglé une fois sur 1977-1999 | 0,2093 | 0,6054 | 66,6 % |
| **Elo re-réglé chaque saison** | **0,2073** | **0,6010** | **67,2 %** |
| Prévision publiée par FiveThirtyEight | 0,2077 | 0,6017 | 66,9 % |

Calibration du modèle re-réglé : écart entre probabilité annoncée et fréquence observée inférieur
à 2 points dans chaque tranche de 20 % à 90 % (tableau dans le notebook 03).

Exécuté le 22/10/2026 (pandas 3.0.5) ; tests `tests/test_models.py` verts sous pandas 3.0.5 et 2.2.3.

## Hypothèses
- La force d'une équipe se résume à un nombre, qui évolue seulement avec les résultats.
- Même avantage du terrain pour toutes les équipes.
- Aucune information sur les blessures, le repos, les transferts ou les effectifs.

## Limites
- **Aucune mesure de rentabilité** : les données ne contiennent pas de cotes.
- **Pas de prévision des matchs actuels** : données arrêtées en juin 2015.
- La comparaison avec FiveThirtyEight les avantage : leurs paramètres ont été choisis en
  connaissant toute l'histoire.
- Les équipes arrivant d'autres ligues (1948-1951, ABA en 1977) démarrent à 1300.
- Les matchs contestés sont comptés à la date de reprise.

## Usage à proscrire
Miser de l'argent sur la seule base de ce modèle. Une probabilité de 70 % signifie que l'équipe
perd environ 3 fois sur 10.
