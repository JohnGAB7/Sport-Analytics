"""Résultats et cotes historiques de football-data.co.uk (gratuit, un fichier CSV par saison).

Chaque fichier contient le score final et les cotes 1X2 de plusieurs bookmakers :
- `AvgH/AvgD/AvgA` (ou `BbAvH...` avant 2019) : cote moyenne, relevée en général le vendredi
  (matchs du week-end) ou le mardi (matchs de semaine), donc 1 à 3 jours avant le match ;
- `PSCH/PSCD/PSCA` : cote de clôture Pinnacle (juste avant le coup d'envoi), la référence la
  plus difficile à battre.
Conditions d'utilisation : voir docs/DATA_SOURCES.md (usage personnel et non commercial).
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from ..leagues import LEAGUES, season_code

BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/{fd}.csv"

MATCH_COLUMNS = ["league", "season", "date", "home_team", "away_team", "home_goals", "away_goals",
                 "odds_home", "odds_draw", "odds_away", "close_home", "close_draw", "close_away"]

# Colonnes possibles, de la plus souhaitable à la moins souhaitable.
PRE_MATCH_ODDS = [("AvgH", "AvgD", "AvgA"), ("BbAvH", "BbAvD", "BbAvA"), ("B365H", "B365D", "B365A")]
CLOSING_ODDS = [("PSCH", "PSCD", "PSCA"), ("AvgCH", "AvgCD", "AvgCA")]


def url(league: str, season: int) -> str:
    return BASE_URL.format(code=season_code(season), fd=LEAGUES[league]["fd_code"])


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1"):  # les anciens fichiers ne sont pas en UTF-8
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("encodage inconnu")


def _first_available(df: pd.DataFrame, choices) -> pd.DataFrame:
    """Pour chaque ligne, le premier trio de cotes complet parmi `choices` (sinon NaN)."""
    out = pd.DataFrame(np.nan, index=df.index, columns=[0, 1, 2])
    for cols in choices:
        if not set(cols) <= set(df.columns):
            continue
        trio = df[list(cols)].apply(pd.to_numeric, errors="coerce")
        trio.columns = [0, 1, 2]
        missing = out.isna().any(axis=1) & trio.notna().all(axis=1)
        out.loc[missing] = trio.loc[missing].to_numpy()
    return out


def parse(text: str, league: str, season: int) -> pd.DataFrame:
    """CSV brut -> une ligne par match terminé, colonnes MATCH_COLUMNS."""
    df = pd.read_csv(io.StringIO(text), dtype=str).dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])  # matchs pas encore joués
    dates = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    short = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    pre, close = _first_available(df, PRE_MATCH_ODDS), _first_available(df, CLOSING_ODDS)
    out = pd.DataFrame({
        "league": league, "season": season, "date": dates.fillna(short),
        "home_team": df["HomeTeam"].str.strip(), "away_team": df["AwayTeam"].str.strip(),
        "home_goals": pd.to_numeric(df["FTHG"], errors="coerce"),
        "away_goals": pd.to_numeric(df["FTAG"], errors="coerce"),
        "odds_home": pre[0], "odds_draw": pre[1], "odds_away": pre[2],
        "close_home": close[0], "close_draw": close[1], "close_away": close[2]})
    bad = out["date"].isna() | out["home_goals"].isna() | out["away_goals"].isna()
    if bad.any():
        raise ValueError(f"{league} {season} : {int(bad.sum())} ligne(s) illisible(s)")
    out[["home_goals", "away_goals"]] = out[["home_goals", "away_goals"]].astype(int)
    return out.reset_index(drop=True)[MATCH_COLUMNS]


def download(league: str, season: int, cache_dir: Path, refresh: bool = False, session=None) -> pd.DataFrame:
    """Télécharge une saison (ou la relit dans le cache). `refresh=True` pour la saison en cours."""
    path = Path(cache_dir) / f"{LEAGUES[league]['fd_code']}_{season_code(season)}.csv"
    if refresh or not path.exists():
        session = session or requests.Session()
        r = session.get(url(league, season), timeout=60)
        r.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_decode(r.content), encoding="utf-8")
    return parse(path.read_text(encoding="utf-8"), league, season)


def load_history(leagues, seasons, cache_dir: Path, current_season: int | None = None,
                 session=None) -> pd.DataFrame:
    """Toutes les saisons demandées, triées par date. La saison en cours est re-téléchargée.

    Une saison absente du site (pas encore commencée) est ignorée avec un message.
    """
    frames = []
    for lg in leagues:
        for s in seasons:
            try:
                frames.append(download(lg, s, cache_dir, refresh=(s == current_season), session=session))
            except requests.HTTPError as e:
                print(f"{lg} {s} indisponible ({e.response.status_code if e.response is not None else '?'})")
    if not frames:
        return pd.DataFrame(columns=MATCH_COLUMNS)
    return pd.concat(frames, ignore_index=True).sort_values(["date", "league", "home_team"],
                                                             kind="stable").reset_index(drop=True)
