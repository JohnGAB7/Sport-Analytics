"""Résultats récents via l'API BALLDONTLIE (formule gratuite : 5 requêtes par minute).

Conditions : https://www.balldontlie.io/terms.html (usage personnel ou commercial autorisé,
y compris les paris légaux ; stockage autorisé ; pas d'attribution exigée ; accès uniquement
par l'API officielle). Voir docs/DATA_SOURCES.md.
"""

from __future__ import annotations

import time

import pandas as pd
import requests

from ..teams import FRANCHISE

BASE_URL = "https://api.balldontlie.io/v1"
MIN_SECONDS_BETWEEN_CALLS = 12.5  # 5 requêtes/minute, avec une marge
SOURCE_NAME = "balldontlie"


def fetch_games(api_key: str, start_date: str, end_date: str, session=None,
                sleep=time.sleep) -> list[dict]:
    """Tous les matchs entre deux dates incluses (AAAA-MM-JJ), en suivant la pagination."""
    session = session or requests.Session()
    params = {"start_date": start_date, "end_date": end_date, "per_page": 100}
    games, first = [], True
    while True:
        if not first:
            sleep(MIN_SECONDS_BETWEEN_CALLS)
        first = False
        r = session.get(f"{BASE_URL}/games", params=params,
                        headers={"Authorization": api_key}, timeout=30)
        r.raise_for_status()
        body = r.json()
        games.extend(body["data"])
        cursor = (body.get("meta") or {}).get("next_cursor")
        if not cursor:
            return games
        params["cursor"] = cursor


def to_games(raw: list[dict]) -> pd.DataFrame:
    """Convertit la réponse de l'API au schéma commun. Ne garde que les matchs terminés."""
    rows = []
    for g in raw:
        if g.get("status_state", "").lower() != "final" and g.get("status") != "Final":
            continue
        home, away = g["home_team"]["abbreviation"], g["visitor_team"]["abbreviation"]
        if home not in FRANCHISE or away not in FRANCHISE:  # matchs d'exhibition, etc.
            continue
        rows.append({
            "game_id": f"BDL{g['id']}",
            # BALLDONTLIE nomme la saison par son année de début (2024 = 2024-25) ;
            # le projet la nomme par son année de fin.
            "season": int(g["season"]) + 1,
            "game_date": g["date"][:10],
            "home_team": home, "away_team": away,
            "home_pts": int(g["home_team_score"]), "away_pts": int(g["visitor_team_score"]),
            "is_playoffs": bool(g.get("postseason", False)),
            "source": SOURCE_NAME, "league": "NBA", "neutral_site": False,
            "home_franchise": FRANCHISE[home], "away_franchise": FRANCHISE[away], "notes": None,
        })
    cols = ["game_id", "season", "game_date", "home_team", "away_team", "home_pts", "away_pts",
            "is_playoffs", "source", "league", "neutral_site", "home_franchise", "away_franchise", "notes"]
    return pd.DataFrame(rows, columns=cols)
