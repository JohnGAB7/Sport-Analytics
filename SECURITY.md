# Sécurité

Ce dépôt est **public**. Règles :

1. **Aucune clé dans le code.** `BDL_API_KEY` et `ODDS_API_KEY` vivent uniquement dans
   *Settings → Secrets and variables → Actions* et sont lues par `os.environ` dans les scripts.
   Le `.gitignore` racine exclut `.env`, `*.key`, `*.pem`, `secrets*`, etc.
2. **Messages d'erreur nettoyés.** The Odds API impose la clé dans l'URL ; `sources/oddsapi.py`
   remplace donc tout message d'erreur réseau/HTTP par un texte neutre (code HTTP seulement),
   car ces messages arrivent dans les journaux publics d'Actions et dans `registry/report.json`.
   Testé par `tests/test_oddsapi_security.py`.
3. **Workflows au moindre privilège.** `permissions: {}` par défaut, `contents: write` seulement
   pour le job qui enregistre le registre ; jeton non conservé dans `.git` pendant `pip`/`pytest`
   (`persist-credentials: false`) ; actions épinglées par SHA (mises à jour par Dependabot) ;
   `timeout-minutes` sur chaque job.
4. **Notebooks.** Clonage sans jeton ; effacer les sorties avant tout commit.

## Si une clé fuit

Réécrire l'historique ne suffit pas sur un dépôt public (copies, forks, caches) :
**révoquer et régénérer la clé chez le fournisseur** (balldontlie.io, the-odds-api.com, GitHub),
puis mettre à jour le secret dans GitHub.

## Signaler un problème

Utiliser *Security → Report a vulnerability* (signalement privé) plutôt qu'une issue publique.
