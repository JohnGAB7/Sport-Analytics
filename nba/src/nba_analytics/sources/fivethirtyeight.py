"""Adaptateur pour le fichier `nbaallelo.csv` de FiveThirtyEight.

Licence : Creative Commons Attribution 4.0 (CC BY 4.0), voir docs/DATA_SOURCES.md.
Obligations : citer la source, donner le lien de la licence, signaler les modifications.

Le fichier d'origine contient **deux lignes par match** (une par équipe). La ligne
`_iscopy == 0` est toujours celle de l'équipe à domicile (ou la première équipe
pour les 19 matchs sur terrain neutre) : on ne garde qu'elle.

Les colonnes Elo (`elo_i`, `elo_n`, `forecast`...) sont des *sorties du modèle* de
FiveThirtyEight, pas des observations : elles ne sont pas reprises dans la table
des matchs, pour éviter de les utiliser par erreur comme variables explicatives.
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/nbaallelo.csv"
# Empreinte du fichier téléchargé le 21/10/2026 (126 314 lignes, 1946-11-01 -> 2015-06-16).
# Si elle change, le fichier source a été modifié : on s'arrête plutôt que de continuer en silence.
EXPECTED_SHA256 = "d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc"
SOURCE_NAME = "fivethirtyeight_nbaallelo"
ATTRIBUTION = (
    "Données : FiveThirtyEight, « nba-elo » (https://github.com/fivethirtyeight/data/tree/master/nba-elo), "
    "licence CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), d'après Basketball-Reference.com. "
    "Modifications : une ligne par match au lieu de deux, colonnes renommées, colonnes Elo retirées."
)
RAW_COLUMNS = ["game_id", "lg_id", "_iscopy", "year_id", "date_game", "is_playoffs",
               "team_id", "fran_id", "pts", "opp_id", "opp_fran", "opp_pts",
               "game_location", "notes"]


def sha256_of(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(dest="data/raw/nbaallelo.csv", verify: bool = True) -> Path:
    """Télécharge le fichier (une seule fois) et vérifie son empreinte SHA-256."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        urllib.request.urlretrieve(URL, dest)
    if verify:
        digest = sha256_of(dest)
        if digest != EXPECTED_SHA256:
            raise ValueError(
                f"Empreinte inattendue pour {dest} : {digest}. Le fichier source a changé ; "
                "vérifiez-le (et sa licence) avant de mettre à jour EXPECTED_SHA256."
            )
    return dest


def to_games(raw: pd.DataFrame, leagues: tuple[str, ...] = ("NBA",)) -> pd.DataFrame:
    """Convertit le format FiveThirtyEight (texte brut) vers le schéma commun.

    Les colonnes restent en texte : la conversion des types est faite ensuite par
    `quality.coerce_types`, comme pour n'importe quelle source.
    `leagues` : ("NBA",) par défaut ; ajouter "ABA" pour inclure la ligue ABA (1967-1976).
    """
    missing = [c for c in RAW_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Colonnes absentes du fichier FiveThirtyEight : {missing}")
    d = raw[raw["_iscopy"].astype(str) == "0"]
    d = d[d["lg_id"].isin(leagues)]
    games = pd.DataFrame({
        "game_id": d["game_id"],
        "season": d["year_id"],
        # Format américain M/J/AAAA, imposé explicitement pour éviter toute ambiguïté.
        "game_date": pd.to_datetime(d["date_game"], format="%m/%d/%Y", errors="coerce")
                       .dt.strftime("%Y-%m-%d"),
        "home_team": d["team_id"],
        "away_team": d["opp_id"],
        "home_pts": d["pts"],
        "away_pts": d["opp_pts"],
        "is_playoffs": d["is_playoffs"],
        "source": SOURCE_NAME,
        # Colonnes supplémentaires, hors schéma obligatoire :
        "league": d["lg_id"],
        "neutral_site": d["game_location"] == "N",
        "home_franchise": d["fran_id"],
        "away_franchise": d["opp_fran"],
        "notes": d["notes"],
    })
    return games.sort_values(["game_date", "game_id"], kind="stable").reset_index(drop=True)


def id_date_mismatches(games: pd.DataFrame) -> pd.DataFrame:
    """Matchs dont la date encodée dans `game_id` (AAAAMMJJ) diffère de `game_date`.

    Contrôle propre à cette source. Il ne dit pas laquelle des deux dates est juste :
    chaque cas doit être vérifié à la main (voir docs/LIMITATIONS.md).
    """
    id_date = pd.to_datetime(games["game_id"].str[:8], format="%Y%m%d", errors="coerce")
    return games[id_date.dt.strftime("%Y-%m-%d") != games["game_date"].astype(str).str[:10]]


def load(path="data/raw/nbaallelo.csv", leagues: tuple[str, ...] = ("NBA",),
         verify: bool = True) -> pd.DataFrame:
    """Télécharge si besoin, vérifie, lit en texte brut et convertit au schéma commun."""
    path = download(path, verify=verify)
    return to_games(pd.read_csv(path, dtype=str), leagues=leagues)
