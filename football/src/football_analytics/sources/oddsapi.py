"""Cotes 1X2 du jour via The Odds API (formule gratuite : 500 crédits par mois, même clé que la NBA).

Un appel `markets=h2h`, une région, un championnat = 1 crédit. 5 championnats une fois par
jour = environ 150 crédits par mois. Les cotes historiques sont payantes et ne sont pas utilisées.
Conditions : https://the-odds-api.com/terms-and-conditions.html.
"""

from __future__ import annotations

import pandas as pd
import requests

URL = "https://api.the-odds-api.com/v4/sports/{sport}/odds/"
ODDS_COLUMNS = ["event_id", "commence_time", "home_name", "away_name", "bookmaker",
                "odds_home", "odds_draw", "odds_away", "fetched_at"]


def _get(session, url: str, params: dict):
    """GET qui ne laisse jamais fuiter la clé.

    The Odds API exige la clé dans l'URL (`apiKey=...`). Or les messages d'erreur de
    `requests` recopient l'URL complète : ils finiraient dans les journaux publics
    d'Actions ou dans `registry/report.json`, qui est versionné. On les remplace donc
    par un message neutre (code HTTP ou type d'erreur), sans chaîner l'exception d'origine.
    """
    try:
        r = session.get(url, params=params, timeout=30)
    except requests.RequestException as e:
        raise requests.RequestException(f"The Odds API : échec réseau ({type(e).__name__})") from None
    if not r.ok:
        raise requests.HTTPError(f"The Odds API : erreur HTTP {r.status_code}") from None
    return r


def fetch_odds(api_key: str, sport_key: str, regions: str = "eu", session=None) -> tuple[list[dict], dict]:
    """Cotes 1X2 (h2h, format décimal) d'un championnat. Renvoie (événements, crédits restants)."""
    session = session or requests.Session()
    r = _get(session, URL.format(sport=sport_key), {"apiKey": api_key, "regions": regions,
                                                    "markets": "h2h", "oddsFormat": "decimal"})
    quota = {k: r.headers.get(k) for k in ("x-requests-remaining", "x-requests-used", "x-requests-last")}
    return r.json(), quota


def to_odds(events: list[dict], fetched_at: str) -> pd.DataFrame:
    """Une ligne par (match, bookmaker) avec les cotes domicile, nul et extérieur.

    Les noms d'équipes restent ceux de The Odds API (rapprochement dans teams.py).
    """
    rows = []
    for e in events:
        for b in e.get("bookmakers", []):
            for m in b.get("markets", []):
                if m.get("key") != "h2h":
                    continue
                prices = {o["name"]: float(o["price"]) for o in m.get("outcomes", [])}
                if {e["home_team"], e["away_team"], "Draw"} <= set(prices):
                    rows.append({"event_id": e["id"], "commence_time": e["commence_time"],
                                 "home_name": e["home_team"], "away_name": e["away_team"],
                                 "bookmaker": b["key"], "odds_home": prices[e["home_team"]],
                                 "odds_draw": prices["Draw"], "odds_away": prices[e["away_team"]],
                                 "fetched_at": fetched_at})
    return pd.DataFrame(rows, columns=ODDS_COLUMNS)
