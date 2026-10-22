# Guide : GitHub + Google Colab, sans rien installer

Tout se fait dans un navigateur (Chrome conseillé). Aucun logiciel à installer.

---

## Partie 1 : créer le dépôt et y déposer les fichiers

### 1.1 Le dépôt
Votre dépôt privé `JohnGAB7/Sport-Analytics` contient déjà le projet dans le dossier `nba/` : les parties 1.2 et 1.3 ne servent que pour un nouveau dépôt.
(Pour un autre projet : **+** → **New repository**, ne rien cocher dans « Initialize », **Create repository**.)

### 1.2 Envoyer les fichiers
1. Téléchargez l'archive `nba-betting-analytics.zip` fournie et décompressez-la sur votre ordinateur.
2. Sur la page du dépôt vide, cliquez sur le lien **uploading an existing file**.
3. Ouvrez le dossier décompressé, **sélectionnez tout son contenu** (pas le dossier lui-même) et
   glissez-le dans la fenêtre GitHub. Les sous-dossiers sont conservés.
4. En bas, champ **Commit changes** : écrivez `Version initiale 0.1.0`, puis **Commit changes**.

### 1.3 Vérifier les fichiers cachés
Les fichiers qui commencent par un point (`.gitignore`, `.gitkeep`) sont souvent masqués par
Windows et macOS et ne partent pas lors du glisser-déposer.
1. Sur la page du dépôt, vérifiez que `.gitignore` apparaît dans la liste.
2. S'il manque : **Add file** → **Create new file**, nommez-le `.gitignore`, collez le contenu
   du fichier fourni, puis **Commit changes**.
3. Les `.gitkeep` ne servent qu'à garder les dossiers `data/` vides ; le notebook recrée ces
   dossiers de toute façon.

---

## Partie 2 : exécuter le notebook dans Colab

1. Sur GitHub, ouvrez `nba/notebooks/02_donnees_reelles_fivethirtyeight.ipynb`.
2. Dans la barre d'adresse, remplacez `https://github.com/` par
   `https://colab.research.google.com/github/` et validez.
   Exemple : `https://colab.research.google.com/github/JohnGAB7/Sport-Analytics/blob/main/nba/notebooks/02_donnees_reelles_fivethirtyeight.ipynb`
   (dépôt privé : utilisez plutôt la méthode de la partie 3.4).
3. Créez d'abord le secret `GITHUB_TOKEN` (partie 3.3, étapes a et b) : la première cellule s'en sert pour cloner le dépôt privé.
4. Menu **Exécution** → **Tout exécuter**. La première cellule clone le dépôt dans Colab et
   installe les dépendances.
5. Pour lancer les tests, ajoutez une cellule et exécutez : `!python -m pytest -q`
   (la première cellule place déjà Colab dans le dossier `nba/`)
   (résultat attendu : `24 passed`).

À savoir : la machine Colab est **temporaire**. Tout ce qui n'est pas renvoyé sur GitHub est
perdu à la fermeture (au bout d'environ 90 minutes d'inactivité).

---

## Partie 3 : mettre à jour GitHub depuis Colab

Trois méthodes, de la plus simple à la plus complète.

### 3.1 Notebook : « Enregistrer une copie dans GitHub » (le plus simple)
1. Dans Colab : **Fichier** → **Enregistrer une copie dans GitHub**.
2. La première fois, Colab demande l'autorisation d'accéder à GitHub : acceptez.
3. Choisissez le dépôt, la branche `main`, et le chemin
   `nba/notebooks/<nom du notebook>.ipynb` (même chemin pour remplacer l'ancien).
4. Écrivez un message de commit qui dit ce qui a changé, puis **OK**.

Limite : ne sauvegarde **que le notebook**, pas les fichiers `.py` ni les tests.

### 3.2 Fichiers `.py`, `.md`, tests : modifier directement sur GitHub
1. Sur GitHub, ouvrez le fichier, cliquez sur l'icône **crayon** (Edit).
2. Modifiez, puis **Commit changes…** avec un message clair.
3. Dans Colab, récupérez la nouvelle version : ajoutez une cellule `!git pull` (ou
   **Exécution** → **Redémarrer la session et tout exécuter**).

C'est la méthode recommandée tant que les modifications sont petites.

### 3.3 Pousser depuis Colab avec Git (pour plusieurs fichiers à la fois)

**a. Créer un jeton d'accès limité (une seule fois)**
1. GitHub → photo de profil → **Settings** → **Developer settings** →
   **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. Nom : `colab-nba` ; Expiration : 30 ou 90 jours.
3. **Repository access** : *Only select repositories* → `Sport-Analytics`.
4. **Permissions** → **Repository permissions** → **Contents** : *Read and write*. Rien d'autre.
5. **Generate token** et copiez-le (il ne sera plus affiché).

**b. Le ranger dans Colab, jamais dans le notebook**
1. Dans Colab, cliquez sur l'icône **clé** (Secrets) dans la barre de gauche.
2. **Ajouter un secret** : nom `GITHUB_TOKEN`, valeur = le jeton. Activez « Accès au notebook ».

**c. Envoyer les modifications** (cellule à exécuter après vos changements)
```python
from google.colab import userdata
import subprocess

USER = "JohnGAB7"
EMAIL = "JohnGAB7@users.noreply.github.com"   # adresse anonyme fournie par GitHub
token = userdata.get("GITHUB_TOKEN")

!git config user.name "{USER}"
!git config user.email "{EMAIL}"
!git status --short            # vérifiez la liste AVANT d'envoyer
!git add -A
!git commit -m "Décrivez ici ce qui a changé"
subprocess.run(["git", "push", f"https://{USER}:{token}@github.com/{USER}/Sport-Analytics.git", "main"], check=True)
```
Règles de sécurité :
- ne jamais écrire le jeton en clair dans une cellule, ni l'afficher avec `print` ;
- relire `git status` : les dossiers `data/` sont exclus par `.gitignore`, mais vérifiez quand même ;
- si le jeton fuit, supprimez-le immédiatement dans GitHub (même page qu'en a.).

### 3.4 Dépôt privé
- Ouvrir le notebook : dans Colab, **Fichier** → **Ouvrir un notebook** → onglet **GitHub**,
  cochez **Inclure les dépôts privés** et autorisez l'accès.
- La première cellule des notebooks lit déjà le secret `GITHUB_TOKEN` pour cloner : créez-le
  avant (3.3 a et b).

---

## Partie 4 : lancer les paris fictifs automatiques (une seule fois)

Chaque jour à 16 h UTC, GitHub note les cotes et les prévisions des matchs du soir, puis le
résultat des matchs de la veille, dans `nba/registry/`. Il faut deux clés gratuites.

### 4.1 Clé BALLDONTLIE
1. Allez sur https://www.balldontlie.io et créez un compte gratuit.
2. Dans votre tableau de bord, copiez votre **API key**.

### 4.2 Clé The Odds API
1. Allez sur https://the-odds-api.com, cliquez **Get API Key**, choisissez la formule **Starter (gratuite)**.
2. La clé arrive par e-mail ; copiez-la.

### 4.3 Ranger les clés dans GitHub (jamais dans la conversation)
1. Ouvrez https://github.com/JohnGAB7/Sport-Analytics/settings/secrets/actions
2. **New repository secret** : Name `BDL_API_KEY`, Secret = la clé BALLDONTLIE, **Add secret**.
3. Recommencez avec Name `ODDS_API_KEY` et la clé The Odds API.

### 4.4 Premier lancement
1. Ouvrez l'onglet **Actions** du dépôt, choisissez **NBA - paris fictifs quotidiens**.
2. Cliquez **Run workflow**, puis **Run workflow**.
3. Le premier passage prend environ 30 minutes (il télécharge les résultats depuis 2015).
   Une coche verte = réussi ; une croix rouge = ouvrez-la et copiez le message d'erreur.
4. Ensuite, tout se fait seul. Le bilan est dans `nba/registry/report.json`.

## Bonnes habitudes
- Un commit = une modification cohérente, avec un message qui dit **pourquoi**.
- Lancez `!python -m pytest -q` avant chaque envoi.
- Mettez à jour `CHANGELOG.md` à chaque version.
