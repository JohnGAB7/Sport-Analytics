# NBA Betting Analytics

Projet personnel d'**analyse statistique et de simulation** de matchs NBA.
Aucune mise d'argent réelle, aucune commercialisation.

> ⚠️ Rien dans ce dépôt n'est un conseil de pari. Une probabilité élevée ne garantit aucun
> résultat, et un bon historique de prévisions ne garantit aucun gain futur.

## État actuel (v0.2.0)

| Fait | Pas encore |
|---|---|
| Structure du dépôt, schéma de données | Données après juin 2015 |
| Données réelles FiveThirtyEight (59 008 matchs NBA, 1946-2015, CC BY 4.0) | Modèle de prédiction |
| Contrôles qualité : manquants, types, dates, doublons, cohérence | Comparaison aux cotes |
| Données synthétiques, 2 notebooks Colab, 24 tests automatisés | Tableau de bord |

## Structure

```
Sport-Analytics/nba/
├── README.md                 ← ce fichier
├── CHANGELOG.md              ← historique des versions
├── TODO.md                   ← prochaines tâches
├── requirements.txt          ← dépendances Python
├── pyproject.toml            ← métadonnées + configuration pytest
├── .gitignore
├── data/                     ← jamais versionné (sauf README)
│   ├── README.md             ← dictionnaire des données
│   ├── raw/  processed/  synthetic/
├── docs/
│   ├── DATA_SOURCES.md       ← vérification des licences
│   ├── LIMITATIONS.md        ← limites connues
│   └── GUIDE_GITHUB_COLAB.md ← mode d'emploi pas à pas
├── notebooks/
│   ├── 01_chargement_controle_qualite.ipynb   ← contrôles testés sur données fictives
│   └── 02_donnees_reelles_fivethirtyeight.ipynb ← mêmes contrôles sur données réelles
├── src/nba_analytics/        ← code réutilisable (importé par les notebooks)
│   ├── schema.py             ← colonnes et types attendus
│   ├── synthetic.py          ← données fictives
│   ├── quality.py            ← contrôles et statistiques descriptives
│   └── sources/fivethirtyeight.py ← téléchargement, empreinte, conversion
└── tests/                    ← tests pytest
```

Principe : la logique vit dans `src/` (testable), les notebooks ne font qu'appeler ce code
et afficher les résultats.

## Démarrer dans Google Colab

Le dépôt `JohnGAB7/Sport-Analytics` est privé : créez d'abord le secret Colab `GITHUB_TOKEN`
(guide, partie 3.3), puis ouvrez le notebook via **Fichier → Ouvrir un notebook → GitHub**
(cochez « Inclure les dépôts privés ») et lancez **Exécution → Tout exécuter**.

Pour les tests, dans une cellule : `!python -m pytest -q`

Détails, y compris l'envoi de modifications vers GitHub : [docs/GUIDE_GITHUB_COLAB.md](docs/GUIDE_GITHUB_COLAB.md).

## Données

- **Réelles** : FiveThirtyEight « nba-elo », téléchargées à l'exécution, empreinte vérifiée.
  Données : FiveThirtyEight, CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), d'après
  Basketball-Reference.com ; une ligne par match, colonnes Elo retirées.
- **Synthétiques** : équipes fictives T01 à T30, pour tester les contrôles.

Analyse juridique : [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

## Licence

Code : à choisir (MIT suggérée). Les données ne sont pas couvertes par la licence du code.
