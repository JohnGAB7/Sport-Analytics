"""Mesures de qualité de prévisions probabilistes (victoire de l'équipe à domicile).

- Score de Brier : moyenne de (p - y)². 0 = parfait ; 0,25 = toujours prédire 50 %.
- Log-loss : moyenne de -[y log p + (1-y) log(1-p)]. Punit fortement les certitudes fausses.
- Calibration : parmi les matchs prédits à ~70 %, l'équipe gagne-t-elle ~70 % du temps ?
"""

from __future__ import annotations

import numpy as np
import pandas as pd

EPS = 1e-12


def brier(p, y) -> float:
    p, y = np.asarray(p, float), np.asarray(y, float)
    return float(np.mean((p - y) ** 2))


def log_loss(p, y) -> float:
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def accuracy(p, y) -> float:
    p, y = np.asarray(p, float), np.asarray(y, float)
    return float(np.mean((p > 0.5) == (y == 1)))


def calibration_table(p, y, n_bins: int = 10) -> pd.DataFrame:
    """Probabilité moyenne prédite contre fréquence observée, par tranche de probabilité."""
    d = pd.DataFrame({"p": np.asarray(p, float), "y": np.asarray(y, float)})
    d["bin"] = pd.cut(d["p"], np.linspace(0, 1, n_bins + 1), include_lowest=True)
    t = d.groupby("bin", observed=True).agg(n=("y", "size"), predicted=("p", "mean"), observed=("y", "mean"))
    return t.round(3)


def summary(predictions: pd.DataFrame, prob_cols: list[str], y_col: str = "home_win") -> pd.DataFrame:
    """Tableau comparatif des modèles sur les mêmes matchs."""
    rows = {}
    for c in prob_cols:
        p, y = predictions[c], predictions[y_col]
        rows[c] = {"n": len(p), "brier": brier(p, y), "log_loss": log_loss(p, y), "accuracy": accuracy(p, y)}
    return pd.DataFrame(rows).T.round(4)


def implied_probabilities(odds_home: float, odds_away: float) -> tuple[float, float, float]:
    """Probabilités implicites de cotes décimales, marge du bookmaker retirée.

    Renvoie (p_domicile, p_extérieur, marge). Ex. cotes 1,90 / 1,90 : 50 % / 50 %, marge 5,3 %.
    La normalisation proportionnelle est une hypothèse simple ; d'autres méthodes existent.
    """
    raw_h, raw_a = 1 / odds_home, 1 / odds_away
    overround = raw_h + raw_a
    return raw_h / overround, raw_a / overround, overround - 1


def expected_value(p: float, odds: float) -> float:
    """Gain moyen espéré pour 1 € misé : p × cote - 1. Négatif = perte attendue.

    Une espérance positive n'est valable que si p est juste : une erreur de quelques points
    de pourcentage sur p suffit à la rendre négative.
    """
    return p * odds - 1
