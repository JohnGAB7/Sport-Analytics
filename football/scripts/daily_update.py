"""Mise à jour quotidienne du registre de paris fictifs football.

Lancé chaque jour par GitHub Actions (.github/workflows/football_daily.yml), ou à la main :
    ODDS_API_KEY=... python scripts/daily_update.py
La clé n'est jamais écrite dans un fichier : elle vient d'une variable d'environnement.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_analytics import paper_trading as pt  # noqa: E402
from football_analytics.leagues import LEAGUES, season_of  # noqa: E402
from football_analytics.models.poisson import ModelParams, fit  # noqa: E402
from football_analytics.sources import footballdata as fd  # noqa: E402
from football_analytics.sources import oddsapi  # noqa: E402
from football_analytics.teams import match_team  # noqa: E402

REGISTRY_DIR = ROOT / "registry"
REGISTRY = REGISTRY_DIR / "paper_bets.csv"
REPORT = REGISTRY_DIR / "report.json"
CACHE = ROOT / "data/raw"
TRAIN_SEASONS = 3                  # saisons complètes en plus de la saison en cours
PARAMS = ModelParams()             # Dixon-Coles, xi = 0,0019, alpha = 3 (réglés sur 2016-2019)


def require_key() -> str:
    key = os.environ.get("ODDS_API_KEY")
    if not key:
        sys.exit("Clé absente : ODDS_API_KEY. Créez-la dans GitHub : Settings > Secrets and variables > "
                 "Actions > New repository secret (la même que pour la NBA suffit).")
    return key


def make_predictor(history: pd.DataFrame, now: pd.Timestamp, unmatched: set):
    """Estime le modèle sur les matchs passés du championnat et renvoie la fonction de prévision."""
    model = fit(history, now.tz_convert(None), PARAMS)
    season = history["season"].max()
    current = list(dict.fromkeys(history.loc[history["season"] == season, "home_team"]))
    everyone = list(dict.fromkeys(history["home_team"]))

    def find(name: str) -> str | None:
        # D'abord parmi les équipes de la saison en cours, puis parmi toutes celles connues.
        return match_team(name, current) or match_team(name, everyone)

    def predict(home_name, away_name, commence_time):
        home, away = find(home_name), find(away_name)
        for name, team in ((home_name, home), (away_name, away)):
            if team is None:
                unmatched.add(name)
        p = model.probs(home or home_name, away or away_name)  # inconnue = traitée comme promue
        return p, home, away, season_of(commence_time)

    return predict


def main() -> None:
    key = require_key()
    now = pd.Timestamp.now(tz="UTC")
    current = season_of(now.tz_convert(None))
    REGISTRY_DIR.mkdir(exist_ok=True)
    history = fd.load_history(LEAGUES, range(current - TRAIN_SEASONS, current + 1), CACHE, current_season=current)

    registry = pd.read_csv(REGISTRY) if REGISTRY.exists() else pt.empty_registry()
    added_all, quota, unmatched, errors = [], {}, set(), {}
    for lg, info in LEAGUES.items():
        h = history[history["league"] == lg]
        if h.empty:
            errors[lg] = "aucun historique"
            continue
        try:
            events, quota = oddsapi.fetch_odds(key, info["odds_key"])
        except requests.HTTPError as e:
            errors[lg] = f"The Odds API : {e}"
            continue
        odds = oddsapi.to_odds(events, now.isoformat())
        added = pt.new_entries(odds, registry, make_predictor(h, now, unmatched), now, lg)
        if len(added):
            added_all.append(added)
            registry = added if registry.empty else pd.concat([registry, added], ignore_index=True)
    registry = pt.settle(registry, history)
    registry.to_csv(REGISTRY, index=False)

    added = pd.concat(added_all) if added_all else pt.empty_registry()
    summary = {"updated_at": now.isoformat(), "new_matches": len(added),
               "new_bets": int(added["bet_side"].notna().sum()), "odds_api_quota": quota,
               "unmatched_teams": sorted(unmatched), "errors": errors, **pt.report(registry)}
    REPORT.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
