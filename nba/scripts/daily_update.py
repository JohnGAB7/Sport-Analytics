"""Mise à jour quotidienne du registre de paris fictifs.

Lancé chaque jour par GitHub Actions (.github/workflows/nba_daily.yml), ou à la main :
    BDL_API_KEY=... ODDS_API_KEY=... python scripts/daily_update.py
Les clés ne sont jamais écrites dans un fichier : elles viennent des variables d'environnement.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_analytics import paper_trading as pt  # noqa: E402
from nba_analytics import quality  # noqa: E402
from nba_analytics.models.elo import EloParams, elo_state, predict  # noqa: E402
from nba_analytics.sources import balldontlie as bdl  # noqa: E402
from nba_analytics.sources import fivethirtyeight as f38  # noqa: E402
from nba_analytics.sources import oddsapi  # noqa: E402

REGISTRY_DIR = ROOT / "registry"
GAMES_CACHE = REGISTRY_DIR / "bdl_games.csv"
REGISTRY = REGISTRY_DIR / "paper_bets.csv"
REPORT = REGISTRY_DIR / "report.json"
FIRST_BDL_DATE = "2015-08-01"  # les données FiveThirtyEight s'arrêtent en juin 2015
# Paramètres retenus par le re-réglage saisonnier du notebook 03 (saisons 2003-2015).
PARAMS = EloParams(k=20, home_advantage=80, carry_over=0.75, use_margin=True)


def update_games_cache(api_key: str, today: pd.Timestamp) -> pd.DataFrame:
    cache = pd.read_csv(GAMES_CACHE, dtype=str) if GAMES_CACHE.exists() else bdl.to_games([])
    start = (pd.Timestamp(cache["game_date"].max()) + pd.Timedelta(days=1)).strftime("%Y-%m-%d") \
        if len(cache) else FIRST_BDL_DATE
    end = (today - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    if start <= end:
        new = bdl.to_games(bdl.fetch_games(api_key, start, end))
        cache = pd.concat([cache, new.astype(str)], ignore_index=True).drop_duplicates("game_id")
        cache.to_csv(GAMES_CACHE, index=False)
        print(f"Résultats ajoutés : {len(new)} ({start} -> {end})")
    return cache


def require_keys() -> None:
    missing = [k for k in ("BDL_API_KEY", "ODDS_API_KEY") if not os.environ.get(k)]
    if missing:
        sys.exit("Clé(s) absente(s) : " + ", ".join(missing) + ". Créez-les dans GitHub : Settings > "
                 "Secrets and variables > Actions > New repository secret (voir docs/GUIDE_GITHUB_COLAB.md, partie 4).")


def main() -> None:
    require_keys()
    now = pd.Timestamp.now(tz="UTC")
    REGISTRY_DIR.mkdir(exist_ok=True)
    bdl_games = update_games_cache(os.environ["BDL_API_KEY"], now.tz_localize(None).normalize())

    old = f38.to_games(pd.read_csv(f38.download(ROOT / "data/raw/nbaallelo.csv"), dtype=str))
    history, _ = quality.coerce_types(pd.concat([old, bdl_games], ignore_index=True))
    history["neutral_site"] = history["neutral_site"].astype(str).eq("True")
    _, ratings, last_season = elo_state(history, PARAMS)

    def predict_home(home, away, commence_time):
        local_day = (commence_time - pd.Timedelta(hours=6)).tz_localize(None)  # approx. heure US
        season = int(quality.expected_season(pd.Series([local_day])).iloc[0])
        fr = bdl.FRANCHISE
        return predict(ratings, last_season, fr[home], fr[away], season, PARAMS), season

    registry = pd.read_csv(REGISTRY) if REGISTRY.exists() else pt.empty_registry()
    events, quota = oddsapi.fetch_odds(os.environ["ODDS_API_KEY"])
    odds = oddsapi.to_odds(events, now.isoformat())
    added = pt.new_entries(odds, registry, predict_home, now)
    if len(added):
        registry = added if registry.empty else pd.concat([registry, added], ignore_index=True)
    registry = pt.settle(registry, bdl_games)
    registry.to_csv(REGISTRY, index=False)

    summary = {"updated_at": now.isoformat(), "new_matches": len(added),
               "new_bets": int(added["bet_side"].notna().sum()) if len(added) else 0,
               "odds_api_quota": quota, **pt.report(registry)}
    REPORT.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
