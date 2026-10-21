# Sources de données : vérification des conditions d'utilisation

> Vérification faite le 14/10/2026, complétée le 21/10/2026, sur les pages listées en bas de page.
> Ce document n'est pas un avis juridique. Les conditions changent : relisez-les avant
> chaque nouvelle utilisation, et consultez un juriste avant toute diffusion publique.

## Usage envisagé (ce qu'on vérifie)

Projet personnel d'analyse statistique et de simulation, **sans mise d'argent réelle ni
commercialisation**, mais dont l'objet est l'analyse des paris (comparaison future aux cotes).
Point important : plusieurs conditions d'utilisation visent *tout lien* avec une activité de
paris, même sans argent. Le nom « Betting Analytics » rend ce lien explicite.

## Principe

La licence du **code** qui télécharge les données (souvent MIT) ne dit rien des droits sur les
**données**. Seules les conditions de la source d'origine comptent, et une licence affichée par
un intermédiaire (Kaggle, GitHub) ne peut pas accorder plus de droits que la source d'origine
n'en a donnés.

## Résultat

| Source | Conditions des données | Verdict pour ce projet |
|---|---|---|
| **NBA.com / stats.nba.com** (et tout ce qui en dérive : `nba_api`, la plupart des jeux Kaggle) | Section 9 « NBA Statistics » : usage privé non commercial autorisé avec attribution, **mais** interdit « in connection with any gambling activity (including legal gambling activity) » et avec tout produit « that features a database ». | ❌ **Exclu.** Incompatible avec un projet d'analyse de paris, même fictifs. |
| **`nba_api`** (bibliothèque Python) | Licence MIT : ne couvre que le code. Les données restent soumises aux conditions de NBA.com (ligne ci-dessus). | ❌ Exclu (par héritage). |
| **Basketball-Reference** (Sports Reference) | Conditions §5 : la réutilisation des données de pages individuelles est « welcomed », y compris commerciale, avec crédit. **Mais** : tout accès automatisé (scripts, scrapers) est interdit sans autorisation écrite ; copie/archivage interdits ; usage pour entraîner ou « prompter » des modèles d'IA interdit ; base de données concurrente interdite. Une page « bot traffic » tolère 20 requêtes/minute, ce qui contredit en partie les conditions générales. | ⚠️ **Non validé** pour constituer un historique par script. Acceptable pour consulter ou recopier à la main quelques pages, avec crédit. |
| **FiveThirtyEight `nba-elo`** (dépôt GitHub `fivethirtyeight/data`) | Données publiées explicitement sous **CC BY 4.0** (attribution exigée). Fichier `nbaallelo.csv` : 1946-11-01 → 2015-06-16, deux lignes par match, scores et Elo. Les informations de match proviennent de Basketball-Reference. | ✅ **Retenu le 21/10/2026.** Licence explicite et compatible ; les réserves initiales (droit européen des bases, conditions de Sports Reference) sont examinées ci-dessous. S'arrête en 2015. |
| **Jeux Kaggle NBA** (ex. `wyattowalsh/basketball`, `nathanlauga/nba-games`) | La licence affichée est choisie par la personne qui a déposé le jeu ; la donnée vient de NBA.com ou de Basketball-Reference. | ❌ Ne pas s'y fier : hérite des restrictions ci-dessus. |
| **Données de cotes** (pour plus tard) | Non examinées à cette étape. | À traiter avant l'étape de comparaison aux cotes. |

## Décision (21/10/2026)

Vous avez choisi **FiveThirtyEight `nba-elo`** comme première source réelle. Les données
synthétiques restent utilisées pour tester les contrôles (notebook 01).

### Pourquoi l'usage est considéré comme licite

1. **Licence explicite** : FiveThirtyEight publie ses données sous CC BY 4.0 (« Unless otherwise
   noted »), et le dossier `nba-elo` ne prévoit aucune exception. CC BY 4.0 autorise la copie,
   l'adaptation et la redistribution, y compris commerciale, à condition de citer la source,
   d'indiquer la licence et de signaler les modifications.
2. **Faits** : les dates et scores de matchs sont des faits, non protégés par le droit d'auteur.
3. **Droit « sui generis » européen** : l'article 11 de la directive 96/9/CE ne protège que les
   bases dont le fabricant est ressortissant ou résident d'un État membre, ou une société établie
   dans l'UE. FiveThirtyEight et Sports Reference sont américains : ce droit ne s'applique pas
   à leurs bases, sauf accord international (aucun n'a été trouvé).
4. **Conditions de Sports Reference** : ce sont des conditions d'utilisation **de leur site**. Le
   projet ne visite pas ce site et ne le moissonne pas ; il n'est donc pas partie à ce contrat.
5. **Paris** : le projet ne comporte aucune mise. Les lois belge et française sur les jeux de hasard
   visent les jeux avec mise (point de connaissance générale, textes non relus à cette étape).

### Obligations à respecter

- Afficher l'attribution (`nba_analytics.sources.fivethirtyeight.ATTRIBUTION`) dans tout résultat
  partagé : « Données : FiveThirtyEight, CC BY 4.0, d'après Basketball-Reference.com », avec la
  liste des modifications.
- Le fichier brut n'est pas mis dans Git : il est retéléchargé et son empreinte SHA-256 est
  vérifiée, pour détecter tout changement de la source (et donc relire sa licence).
- Ne pas remplacer cette source par du moissonnage de Basketball-Reference ou de NBA.com.

### Réserves qui demeurent

- Ce document n'est pas un avis juridique. Avant toute commercialisation, faites-le relire.
- Les données s'arrêtent en juin 2015. Toute source plus récente demandera une nouvelle analyse.

## Autres éléments utilisés

| Élément | Licence ou conditions | Verdict |
|---|---|---|
| pandas | BSD-3-Clause | ✅ usage libre |
| NumPy | BSD-3-Clause (+ composants MIT, 0BSD, Zlib, CC0) | ✅ usage libre |
| Matplotlib | Licence Matplotlib (type PSF) | ✅ usage libre |
| pytest | MIT | ✅ usage libre |
| Google Colab (gratuit) | Activités interdites : hébergement de services, cryptominage, P2P, attaques, contournement de quotas… | ✅ l'analyse de données n'en fait pas partie |
| GitHub (dépôt privé gratuit) | Conditions générales GitHub | ✅ usage personnel standard |
| Données synthétiques | Générées par le projet | ✅ aucun droit de tiers |

## Pages consultées

- NBA.com, Terms of Use (section 9 « NBA Statistics ») : https://www.nba.com/terms
- Sports Reference, Terms of Use : https://www.sports-reference.com/termsofuse.html
  (copie consultée via https://tostracker.app/document/sports-reference, la page officielle ayant renvoyé une erreur)
- Sports Reference, Data Use : https://www.sports-reference.com/data_use.html
- Sports Reference, Bot Traffic : https://www.sports-reference.com/bot-traffic.html
- FiveThirtyEight, licence des données : https://github.com/fivethirtyeight/data (README et LICENSE)
- FiveThirtyEight, `nba-elo` : https://github.com/fivethirtyeight/data/tree/master/nba-elo
- `nba_api`, licence : https://github.com/swar/nba_api
- Directive 96/9/CE, article 11 : https://www.legislation.gov.uk/eudr/1996/9/article/11
- Google Colab, FAQ (activités restreintes) : https://research.google.com/colaboratory/faq.html
- Licences des bibliothèques : métadonnées des paquets installés (`importlib.metadata`)
