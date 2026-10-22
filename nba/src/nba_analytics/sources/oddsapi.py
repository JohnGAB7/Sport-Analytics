"""Cotes du jour via The Odds API (formule gratuite : 500 crédits par mois).

Un appel `markets=h2h` sur une seule région coûte 1 crédit, soit environ 30 crédits par mois
pour un appel quotidien. Les cotes historiques sont payantes et ne sont pas utilisées.
Conditions : https://the-odds-api.com/terms-and-conditions.html.
"""

from __future__ import annotations

import pandas as pd
import requests

from ..teams import abbr_from_full_name

URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"


def fetch_odds(api_key: str, regions: str = "eu", session=None) -> tuple[list[dict], dict]:
    """Cotes « vainqueur du match » (h2h, format décimal). Renvoie (événements, crédits restants)."""
    session = session or requests.Session()
    r = session.get(URL, params={"apiKey": api_key, "regions": regions, "markets": "h2h",
                                 "oddsFormat": "decimal"}, timeout=30)
    r.raise_for_status()
    quota = {k: r.headers.get(k) for k in ("x-requests-remaining", "x-requests-used", "x-requests-last")}
    return r.json(), quota


def to_odds(events: list[dict], fetched_at: str) -> pd.DataFrame:
    """Une ligne par (match, bookmaker) avec la cote domicile et la cote extérieur."""
    rows = []
    for e in events:
        home, away = abbr_from_full_name(e["home_team"]), abbr_from_full_name(e["away_team"])
        for b in e.get("bookmakers", []):
            for m in b.get("markets", []):
                if m.get("key") != "h2h":
                    continue
                prices = {o["name"]: float(o["price"]) for o in m.get("outcomes", [])}
                if e["home_team"] in prices and e["away_team"] in prices:
                    rows.append({"event_id": e["id"], "commence_time": e["commence_time"],
                                 "home_team": home, "away_team": away, "bookmaker": b["key"],
                                 "odds_home": prices[e["home_team"]], "odds_away": prices[e["away_team"]],
                                 "fetched_at": fetched_at})
    return pd.DataFrame(rows, columns=["event_id", "commence_time", "home_team", "away_team",
                                       "bookmaker", "odds_home", "odds_away", "fetched_at"])
