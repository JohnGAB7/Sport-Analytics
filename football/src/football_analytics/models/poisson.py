"""Modèle de buts de Poisson, avec la correction de Dixon et Coles (1997).

Pour un match entre l'équipe à domicile i et l'équipe à l'extérieur j :
    buts domicile  X ~ Poisson(λ),  log λ = mu + home + att_i - def_j
    buts extérieur Y ~ Poisson(ν),  log ν = mu        + att_j - def_i
`att` = force offensive, `def` = solidité défensive (plus grand = encaisse moins).

Correction Dixon-Coles : X et Y ne sont pas tout à fait indépendants pour les petits scores.
La probabilité des scores 0-0, 1-0, 0-1 et 1-1 est multipliée par τ(ρ) :
    τ(0,0) = 1 - λνρ,  τ(0,1) = 1 + λρ,  τ(1,0) = 1 + νρ,  τ(1,1) = 1 - ρ,  sinon 1.
Avec ρ = 0, on retrouve le modèle de Poisson indépendant.

Estimation par maximum de vraisemblance pondérée :
- poids exp(-xi × ancienneté en jours) : un match récent compte plus qu'un match ancien
  (xi = 0,0019 : un match d'il y a un an compte moitié moins) ;
- pénalité ridge alpha/2 × Σ(att² + def²) : rend les paramètres identifiables (sinon on
  pourrait ajouter une constante à tous les att et à mu) et évite des valeurs extrêmes pour
  les équipes qui ont peu joué.
Seuls les matchs STRICTEMENT antérieurs à `ref_date` sont utilisés : pas de fuite possible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

RHO_BOUNDS = (-0.2, 0.2)


@dataclass(frozen=True)
class ModelParams:
    xi: float = 0.0019          # décroissance des poids, par jour
    alpha: float = 3.0          # force de la pénalité ridge (réglée sur 2016-2019)
    dixon_coles: bool = True    # False = Poisson indépendant (ρ fixé à 0)
    max_goals: int = 10         # scores calculés de 0-0 à 10-10 (le reste est négligeable)
    n_weakest_for_new: int = 3  # une équipe jamais vue reçoit la moyenne des 3 plus faibles


@dataclass
class FittedModel:
    teams: list[str]
    att: np.ndarray
    defn: np.ndarray
    mu: float
    home: float
    rho: float
    params: ModelParams
    n_matches: int
    converged: bool

    def _ratings(self, team: str) -> tuple[float, float]:
        """Notes d'une équipe. Équipe inconnue (promue) : moyenne des plus faibles."""
        if team in self._index:
            k = self._index[team]
            return self.att[k], self.defn[k]
        weakest = np.argsort(self.att + self.defn)[: self.params.n_weakest_for_new]
        return float(self.att[weakest].mean()), float(self.defn[weakest].mean())

    def __post_init__(self):
        self._index = {t: k for k, t in enumerate(self.teams)}

    def expected_goals(self, home: str, away: str) -> tuple[float, float]:
        ah, dh = self._ratings(home)
        aa, da = self._ratings(away)
        return float(np.exp(self.mu + self.home + ah - da)), float(np.exp(self.mu + aa - dh))

    def score_matrix(self, home: str, away: str) -> np.ndarray:
        """Matrice M[x, y] = P(score x-y), normalisée pour sommer à 1."""
        lam, nu = self.expected_goals(home, away)
        g = np.arange(self.params.max_goals + 1)
        m = np.outer(poisson.pmf(g, lam), poisson.pmf(g, nu))
        r = self.rho
        m[0, 0] *= 1 - lam * nu * r
        m[0, 1] *= 1 + lam * r
        m[1, 0] *= 1 + nu * r
        m[1, 1] *= 1 - r
        m = np.clip(m, 0, None)
        return m / m.sum()

    def probs(self, home: str, away: str) -> np.ndarray:
        """Probabilités (H, D, A)."""
        m = self.score_matrix(home, away)
        return np.array([np.tril(m, -1).sum(), np.trace(m), np.triu(m, 1).sum()])

    def predict(self, home_teams, away_teams) -> np.ndarray:
        return np.array([self.probs(h, a) for h, a in zip(home_teams, away_teams)]).reshape(-1, 3)


def _neg_loglik(theta, hi, ai, x, y, w, n, alpha, use_rho):
    """Moins la log-vraisemblance pondérée pénalisée, et son gradient (calcul exact)."""
    mu, home, rho = theta[0], theta[1], (theta[2] if use_rho else 0.0)
    att, dfn = theta[3:3 + n], theta[3 + n:]
    lam = np.exp(mu + home + att[hi] - dfn[ai])
    nu = np.exp(mu + att[ai] - dfn[hi])

    tau = np.ones_like(lam)
    s00, s01, s10, s11 = (x == 0) & (y == 0), (x == 0) & (y == 1), (x == 1) & (y == 0), (x == 1) & (y == 1)
    tau[s00] = 1 - lam[s00] * nu[s00] * rho
    tau[s01] = 1 + lam[s01] * rho
    tau[s10] = 1 + nu[s10] * rho
    tau[s11] = 1 - rho
    tau = np.clip(tau, 1e-10, None)

    ll = x * np.log(lam) - lam + y * np.log(nu) - nu + np.log(tau)
    obj = -np.sum(w * ll) + alpha / 2 * (att @ att + dfn @ dfn)

    # Dérivées de log τ par rapport à log λ, log ν et ρ.
    dtau_l, dtau_n, dtau_r = np.zeros_like(lam), np.zeros_like(lam), np.zeros_like(lam)
    dtau_l[s00] = -lam[s00] * nu[s00] * rho / tau[s00]
    dtau_n[s00] = dtau_l[s00]
    dtau_r[s00] = -lam[s00] * nu[s00] / tau[s00]
    dtau_l[s01] = lam[s01] * rho / tau[s01]
    dtau_r[s01] = lam[s01] / tau[s01]
    dtau_n[s10] = nu[s10] * rho / tau[s10]
    dtau_r[s10] = nu[s10] / tau[s10]
    dtau_r[s11] = -1 / tau[s11]

    gl = w * (x - lam + dtau_l)   # dérivée de ll par rapport à log λ
    gn = w * (y - nu + dtau_n)    # ... par rapport à log ν
    grad = np.zeros_like(theta)
    grad[0] = -(gl.sum() + gn.sum())
    grad[1] = -gl.sum()
    grad[2] = -np.sum(w * dtau_r) if use_rho else 0.0
    g_att = np.bincount(hi, gl, n) + np.bincount(ai, gn, n)
    g_def = -np.bincount(ai, gl, n) - np.bincount(hi, gn, n)
    grad[3:3 + n] = -g_att + alpha * att
    grad[3 + n:] = -g_def + alpha * dfn
    return obj, grad


def fit(history: pd.DataFrame, ref_date, params: ModelParams = ModelParams()) -> FittedModel:
    """Estime le modèle sur les matchs joués avant `ref_date` (colonnes date, home_team,
    away_team, home_goals, away_goals)."""
    ref = pd.Timestamp(ref_date)
    h = history[pd.to_datetime(history["date"]) < ref]
    if h.empty:
        raise ValueError("aucun match avant la date de référence")
    teams = sorted(set(h["home_team"]) | set(h["away_team"]))
    idx = {t: k for k, t in enumerate(teams)}
    hi = h["home_team"].map(idx).to_numpy()
    ai = h["away_team"].map(idx).to_numpy()
    x = h["home_goals"].to_numpy(float)
    y = h["away_goals"].to_numpy(float)
    age = (ref - pd.to_datetime(h["date"])).dt.days.to_numpy(float)
    w = np.exp(-params.xi * age)

    n = len(teams)
    theta0 = np.zeros(3 + 2 * n)
    theta0[0] = np.log(max(np.average((x + y) / 2, weights=w), 0.1))
    theta0[1] = 0.2
    bounds = [(None, None), (None, None), RHO_BOUNDS if params.dixon_coles else (0.0, 0.0)] + [(None, None)] * 2 * n
    res = minimize(_neg_loglik, theta0, jac=True, method="L-BFGS-B", bounds=bounds,
                   args=(hi, ai, x, y, w, n, params.alpha, params.dixon_coles))
    th = res.x
    return FittedModel(teams=teams, att=th[3:3 + n], defn=th[3 + n:], mu=float(th[0]), home=float(th[1]),
                       rho=float(th[2]) if params.dixon_coles else 0.0, params=params,
                       n_matches=len(h), converged=bool(res.success))
