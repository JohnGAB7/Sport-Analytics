# Limites connues

## Données synthétiques

Elles servent à tester le code, **pas à apprendre quoi que ce soit sur la NBA**.

- Les scores domicile et extérieur sont tirés de lois normales **indépendantes** (moyenne 112,
  écart-type 12). Dans la réalité, les deux scores d'un match sont corrélés (rythme de jeu).
- Le niveau de chaque équipe (attaque, défense) est constant sur une saison : pas de blessures,
  d'échanges de joueurs, de fatigue (matchs consécutifs) ni de tendance.
- Avantage du terrain fixé à +2,5 points pour toutes les équipes.
- Les prolongations sont simulées grossièrement (+Poisson(11) points par équipe), ce qui gonfle
  légèrement les moyennes.
- Calendrier simplifié : pas de conférences ni de divisions, saison qui finit début avril au
  lieu de mi-avril, une équipe peut terminer à 81 matchs au lieu de 82. Pas de play-offs.
- Les équipes T01 à T30 sont fictives.

## Données réelles FiveThirtyEight (`nbaallelo.csv`)

Résultats des contrôles, vérifiés le 21/10/2026 sur 59 008 matchs NBA (1946-47 à 2014-15) :
aucune valeur manquante, aucun doublon, aucune date hors saison, types conformes.
Les alertes restantes ne sont **pas corrigées** :

- **52 scores hors de [50, 200]** : 51 entre 1947 et 1953 (avant l'horloge des 24 secondes),
  dont le 19-18 de 1950, et Chicago 49 – Miami 82 en 1999. Ce sont des scores réels. Les
  premières saisons devront être exclues ou traitées à part.
- **Matchs contestés** (1970, 1979, 1983, 2008) : la fin du match a été rejouée des mois plus
  tard, le jour d'un autre match entre les mêmes équipes. La date enregistrée est celle de la
  reprise. Un backtest ne doit pas connaître ce score avant cette date.
- **1954-03-08** : deux matchs Milwaukee–Baltimore le même jour, sans note. Non vérifié.
- **Incohérences internes** entre la date de `game_id` et `game_date` : Atlanta–Miami 2008
  (date probablement fausse : reprise le 8 mars) et finale 2015, match 6 (identifiant
  probablement faux : match le 16 juin). Non vérifié contre une seconde source.
- **Ligue ABA** exclue par défaut (option `leagues=("NBA", "ABA")`).
- **Terrain neutre** (19 matchs) : l'équipe « domicile » est la première listée par la source.
  Les statistiques domicile/extérieur du notebook les incluent ; le calcul « hors terrain
  neutre » est donné à part.
- **Codes d'équipe** : ils changent avec les déménagements (ex. SEA → OKC). La colonne
  `home_franchise` regroupe les codes d'une même franchise.
- Les colonnes Elo et `forecast` de FiveThirtyEight sont volontairement retirées : ce sont des
  prévisions d'un modèle, pas des observations.
- **Données arrêtées en juin 2015**.

## Contrôles de qualité

- **Dates ambiguës** : la lecture accepte plusieurs formats (`format="mixed"`). Une date comme
  `03/04/2024` est lue au format américain (4 mars), pas français. Utilisez le format ISO
  `AAAA-MM-JJ` dans vos fichiers ; FiveThirtyEight utilise `M/J/AAAA` (américain), ce qui est
  donc lu correctement.
- **Hors saison** : juillet à septembre sont signalés. La saison 2019-20 (bulle, matchs jusqu'en
  octobre 2020) déclenchera de fausses alertes.
- **Saison déduite de la date** : un match à partir d'août appartient à la saison suivante.
- **Bornes de plausibilité** : un score < 50 ou > 200 est signalé. Hypothèse raisonnable pour la
  NBA moderne, mais les années 1940-50 comptent des scores plus bas.
- **Date « future »** : comparée à l'horloge de la machine qui exécute le code.
- Les contrôles décrivent les problèmes ; ils **ne corrigent rien** automatiquement.
- Non vérifié : cohérence avec une source externe, codes d'équipe (déménagements, changements de
  nom), nombre de matchs par équipe et par saison.

## Juridique

- Aucune source réelle n'est encore validée (voir `DATA_SOURCES.md`).
- Le document des sources n'est pas un avis juridique.

## Ce qui n'existe pas encore

Aucun modèle de prédiction, aucune comparaison aux cotes, aucun tableau de bord. Aucune
statistique de ce dépôt ne doit être lue comme une indication de pari.
