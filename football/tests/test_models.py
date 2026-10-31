"""Tests des modèles : valeurs connues, estimation sur données simulées, absence de fuite."""

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import check_grad

from conftest import HOME, TEAMS, TRUE_ATT, TRUE_DEF
from football_analytics.models import backtest as bt
from football_analytics.models import evaluation as ev
from football_analytics.models import poisson as P
from football_analytics.models.baseline import frequencies


def test_mesures_valeurs_connues():
    uniform = np.full((3, 3), 1 / 3)
    y = [0, 1, 2]
    assert ev.brier(uniform, y) == pytest.approx(2 / 3)
    assert ev.log_loss(uniform, y) == pytest.approx(np.log(3))
    assert ev.rps([[1, 0, 0]], [0]) == 0.0
    assert ev.rps([[0, 0, 1]], [0]) == pytest.approx(1.0)        # pire erreur possible
    assert ev.rps([[0, 1, 0]], [0]) < ev.rps([[0, 0, 1]], [0])    # le nul est « moins faux »
    assert np.isfinite(ev.log_loss([[1, 0, 0]], [2]))


def test_probabilites_implicites():
    p, margin = ev.implied_probabilities([2.0, 3.4, 3.8])
    assert p.sum() == pytest.approx(1.0)
    assert margin == pytest.approx(1 / 2 + 1 / 3.4 + 1 / 3.8 - 1)
    assert ev.expected_value(0.55, 2.0) == pytest.approx(0.10)


def test_gradient_exact(history):
    teams = sorted(set(history.home_team))
    idx = {t: k for k, t in enumerate(teams)}
    hi, ai = history.home_team.map(idx).to_numpy(), history.away_team.map(idx).to_numpy()
    x, y = history.home_goals.to_numpy(float), history.away_goals.to_numpy(float)
    w = np.random.default_rng(0).random(len(x))
    theta = np.random.default_rng(1).normal(0, 0.2, 3 + 2 * len(teams))
    args = (hi, ai, x, y, w, len(teams), 2.0, True)
    err = check_grad(lambda t: P._neg_loglik(t, *args)[0], lambda t: P._neg_loglik(t, *args)[1], theta)
    assert err < 1e-3


def test_estimation_retrouve_les_vrais_parametres(history):
    m = P.fit(history, "2030-01-01", P.ModelParams(xi=0.0, alpha=0.1))
    assert m.converged
    assert m.home == pytest.approx(HOME, abs=0.08)
    order = [m.teams.index(t) for t in TEAMS]
    assert np.corrcoef(m.att[order], TRUE_ATT)[0, 1] > 0.9
    assert np.corrcoef(m.defn[order], TRUE_DEF)[0, 1] > 0.9


def test_probabilites_coherentes(history):
    m = P.fit(history, "2024-07-01")
    p = m.probs("T11", "T00")
    assert p.sum() == pytest.approx(1.0) and p[0] > 0.6           # la meilleure équipe chez la pire
    assert m.score_matrix("T00", "T11").sum() == pytest.approx(1.0)
    assert P.fit(history, "2024-07-01", P.ModelParams(dixon_coles=False)).rho == 0.0


def test_equipe_inconnue_traitee_comme_promue(history):
    m = P.fit(history, "2024-07-01")
    assert m.probs("Promu FC", "T11")[0] < m.probs("T05", "T11")[0]


def test_pas_de_fuite_les_matchs_futurs_sont_ignores(history):
    ref = pd.Timestamp("2023-03-01")
    a = P.fit(history, ref)
    altered = history.copy()
    altered.loc[altered["date"] >= ref, "home_goals"] = 9               # on « sabote » le futur
    b = P.fit(altered, ref)
    assert np.allclose(a.att, b.att) and a.n_matches == (history["date"] < ref).sum()


def test_reference_frequences():
    h = pd.DataFrame({"home_goals": [1, 0, 2, 1], "away_goals": [0, 0, 3, 1]})
    assert frequencies(h).tolist() == [0.25, 0.5, 0.25]


def test_walk_forward_sans_fuite(history):
    models = {"poisson": P.ModelParams(dixon_coles=False)}
    a = bt.walk_forward(history, "EPL", [2024], train_seasons=2, models=models)
    target = a.iloc[40]
    altered = history.copy()
    same = (altered["date"] == target["date"]) & (altered["home_team"] == target["home_team"])
    altered.loc[same, ["home_goals", "away_goals"]] = [0, 7]
    b = bt.walk_forward(altered, "EPL", [2024], train_seasons=2, models=models)
    cols = ["poisson_H", "poisson_D", "poisson_A", "freq_H"]
    assert np.allclose(a.loc[40, cols].astype(float), b.loc[40, cols].astype(float))  # sa propre prévision
    assert b.loc[40, "result"] == 2
    assert len(a) == (history["season"] == 2024).sum()
    assert {"market_H", "closing_H", "market_margin"} <= set(a.columns)


def test_simulation_des_paris():
    pred = pd.DataFrame({"league": "EPL", "season": 2024, "result": [0, 2],
                         "m_H": [0.6, 0.6], "m_D": [0.2, 0.2], "m_A": [0.2, 0.2],
                         "oh": [2.0, 2.0], "od": [3.5, 3.5], "oa": [4.0, 4.0]})
    bets = bt.simulate_bets(pred, "m", ["oh", "od", "oa"])
    assert bets["side"].tolist() == ["H", "H"] and bets["profit"].tolist() == [1.0, -1.0]
    assert bt.roi_summary(bets)["roi"] == 0.0
