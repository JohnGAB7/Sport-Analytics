"""Données simulées partagées par les tests (aucun appel réseau)."""

import numpy as np
import pandas as pd
import pytest

TEAMS = [f"T{k:02d}" for k in range(12)]
TRUE_ATT = np.linspace(-0.4, 0.4, 12)
TRUE_DEF = np.linspace(-0.3, 0.3, 12)   # T11 : la meilleure attaque et la meilleure défense
MU, HOME, RHO = 0.15, 0.25, -0.1


def simulate(seasons=(2022, 2023, 2024), seed=1, league="EPL") -> pd.DataFrame:
    """Championnat fictif en aller-retour, buts tirés selon un modèle de Poisson connu."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in seasons:
        start = pd.Timestamp(f"{s - 1}-08-10")
        pairs = [(i, j) for i in range(12) for j in range(12) if i != j]
        rng.shuffle(pairs)
        for k, (i, j) in enumerate(pairs):
            lam = np.exp(MU + HOME + TRUE_ATT[i] - TRUE_DEF[j])
            nu = np.exp(MU + TRUE_ATT[j] - TRUE_DEF[i])
            rows.append({"league": league, "season": s, "date": start + pd.Timedelta(days=2 * (k // 6)),
                         "home_team": TEAMS[i], "away_team": TEAMS[j],
                         "home_goals": int(rng.poisson(lam)), "away_goals": int(rng.poisson(nu)),
                         "odds_home": 2.2, "odds_draw": 3.3, "odds_away": 3.4,
                         "close_home": 2.1, "close_draw": 3.4, "close_away": 3.6})
    return pd.DataFrame(rows)


@pytest.fixture(scope="session")
def history():
    return simulate()
