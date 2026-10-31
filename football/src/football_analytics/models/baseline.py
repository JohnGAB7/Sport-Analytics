"""Référence : fréquences historiques H / D / A du championnat, sans regarder les équipes.

Un modèle qui ne bat pas cette référence n'apprend rien d'utile sur les équipes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .evaluation import outcome_code


def frequencies(history: pd.DataFrame) -> np.ndarray:
    """Fréquences (H, D, A) des matchs fournis (uniquement des matchs passés !)."""
    y = outcome_code(history["home_goals"], history["away_goals"])
    return np.bincount(y, minlength=3) / len(y)
