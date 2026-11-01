"""Mesures de qualité de prévisions 1X2 (trois issues : domicile H, nul D, extérieur A).

Toutes prennent un tableau de probabilités de forme (n, 3), colonnes dans l'ordre H, D, A,
et un vecteur de résultats codés 0 = H, 1 = D, 2 = A.
- Brier (multiclasse) : somme sur les 3 issues de (p - y)², moyenne sur les matchs.
  0 = parfait ; prédire 1/3 partout donne 0,667.
- RPS (ranked probability score) : comme le Brier, mais sur les probabilités cumulées.
  Il tient compte de l'ordre H > D > A : prédire « nul » quand l'équipe à domicile gagne est
  moins grave que prédire « victoire extérieure ». Mesure standard en football.
- Log-loss : moyenne de -log(probabilité donnée à l'issue réelle).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

EPS = 1e-12
OUTCOMES = ("H", "D", "A")


def outcome_code(home_goals, away_goals) -> np.ndarray:
    h, a = np.asarray(home_goals), np.asarray(away_goals)
    return np.where(h > a, 0, np.where(h == a, 1, 2))


def _onehot(y) -> np.ndarray:
    y = np.asarray(y, int)
    out = np.zeros((len(y), 3))
    out[np.arange(len(y)), y] = 1.0
    return out


def brier(p, y) -> float:
    p = np.asarray(p, float)
    return float(np.mean(np.sum((p - _onehot(y)) ** 2, axis=1)))


def rps(p, y) -> float:
    p = np.asarray(p, float)
    cp, cy = np.cumsum(p, axis=1)[:, :2], np.cumsum(_onehot(y), axis=1)[:, :2]
    return float(np.mean(np.sum((cp - cy) ** 2, axis=1) / 2))


def log_loss(p, y) -> float:
    p = np.asarray(p, float)
    y = np.asarray(y, int)
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], EPS, 1))))


def summary(pred: pd.DataFrame, models: list[str], y_col: str = "result") -> pd.DataFrame:
    """Tableau comparatif ; pour le modèle `m`, les colonnes attendues sont m_H, m_D, m_A."""
    rows = {}
    for m in models:
        p = pred[[f"{m}_{o}" for o in OUTCOMES]].to_numpy(float)
        y = pred[y_col].to_numpy()
        rows[m] = {"n": len(y), "brier": brier(p, y), "rps": rps(p, y), "log_loss": log_loss(p, y),
                   "accuracy": float(np.mean(p.argmax(axis=1) == y))}
    return pd.DataFrame(rows).T.round(4)


def calibration_table(pred: pd.DataFrame, model: str, y_col: str = "result", n_bins: int = 10) -> pd.DataFrame:
    """Probabilité annoncée contre fréquence observée, toutes issues confondues."""
    parts = []
    for k, o in enumerate(OUTCOMES):
        parts.append(pd.DataFrame({"p": pred[f"{model}_{o}"].astype(float), "y": (pred[y_col] == k).astype(float)}))
    d = pd.concat(parts, ignore_index=True)
    d["bin"] = pd.cut(d["p"], np.linspace(0, 1, n_bins + 1), include_lowest=True)
    return d.groupby("bin", observed=True).agg(n=("y", "size"), predicted=("p", "mean"),
                                               observed=("y", "mean")).round(3)


def implied_probabilities(odds) -> tuple[np.ndarray, float]:
    """Cotes décimales (H, D, A) -> probabilités implicites, marge retirée proportionnellement.

    Ex. cotes 2,00 / 3,40 / 3,80 : somme des inverses 1,057, marge 5,7 %.
    Hypothèse simple : la marge est répartie au prorata. En réalité, les bookmakers chargent
    souvent plus les outsiders (biais favori-outsider) ; d'autres méthodes existent (Shin).
    """
    raw = 1 / np.asarray(odds, float)
    total = raw.sum(axis=-1, keepdims=True)
    return raw / total, (total - 1).squeeze(-1)


def expected_value(p, odds):
    """Gain moyen espéré pour 1 unité misée : p × cote - 1. Valable seulement si p est juste."""
    return np.asarray(p, float) * np.asarray(odds, float) - 1
