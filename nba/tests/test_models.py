"""Tests des modèles : valeurs connues et absence de fuite d'information."""

import numpy as np
import pandas as pd
import pytest

from nba_analytics import quality
from nba_analytics.models import backtest as bt
from nba_analytics.models import evaluation as ev
from nba_analytics.models.baseline import home_rate_predictions
from nba_analytics.models.elo import EloParams, run_elo, win_probability
from nba_analytics.synthetic import generate_games


@pytest.fixture(scope="module")
def games():
    g, _ = quality.coerce_types(generate_games(seasons=[2021, 2022, 2023, 2024], seed=21))
    g = g.assign(home_franchise=g["home_team"], away_franchise=g["away_team"], neutral_site=False)
    return bt.prepare(g)


def test_mesures_valeurs_connues():
    assert ev.brier([0.5, 0.5], [1, 0]) == pytest.approx(0.25)
    assert ev.log_loss([0.5, 0.5], [1, 0]) == pytest.approx(np.log(2))
    assert ev.brier([1.0, 0.0], [1, 0]) == 0.0
    assert ev.accuracy([0.7, 0.2, 0.6], [1, 0, 0]) == pytest.approx(2 / 3)


def test_log_loss_reste_fini_sur_certitude_fausse():
    assert np.isfinite(ev.log_loss([1.0], [0]))


def test_probabilite_elo():
    assert win_probability(0) == pytest.approx(0.5)
    assert win_probability(100) == pytest.approx(0.6401, abs=1e-4)
    assert win_probability(100) + win_probability(-100) == pytest.approx(1.0)


def test_premier_match_avantage_terrain(games):
    r = run_elo(games, EloParams(home_advantage=100))
    assert r["p_elo"].iloc[0] == pytest.approx(0.6401, abs=1e-4)


def test_terrain_neutre_sans_avantage(games):
    g = games.copy()
    g.loc[g.index[0], "neutral_site"] = True
    assert run_elo(g)["p_elo"].iloc[0] == pytest.approx(0.5)


def test_pas_de_fuite_le_resultat_d_un_match_ne_change_pas_sa_prevision(games):
    i = 500
    base = run_elo(games)["p_elo"]
    altered = games.copy()
    idx = altered.index[i]
    altered.loc[idx, ["home_pts", "away_pts"]] = [altered.loc[idx, "away_pts"], altered.loc[idx, "home_pts"]]
    after = run_elo(altered)["p_elo"]
    assert np.allclose(base.iloc[: i + 1], after.iloc[: i + 1])   # passé et match lui-même inchangés
    assert not np.allclose(base.iloc[i + 1:], after.iloc[i + 1:])  # le futur, lui, change


def test_reference_utilise_seulement_les_saisons_passees(games):
    p = home_rate_predictions(games)
    assert p[games["season"] == 2021].isna().all()
    expected = games.loc[games["season"] == 2021, "home_win"].mean()
    assert p[games["season"] == 2022].iloc[0] == pytest.approx(expected)


def test_reglage_independant_des_saisons_de_test(games):
    grid = {"k": [10, 20], "home_advantage": [50, 100], "carry_over": [0.75], "use_margin": [True]}
    a = bt.grid_search(games, range(2021, 2023), grid)
    altered = games.copy()
    late = altered["season"] == 2024
    altered.loc[late, "home_pts"] = 0  # on « sabote » la saison de test
    altered["home_win"] = (altered["home_pts"] > altered["away_pts"]).astype(int)
    b = bt.grid_search(altered, range(2021, 2023), grid)
    pd.testing.assert_frame_equal(a, b)


def test_walk_forward_et_calibration(games):
    grid = {"k": [20], "home_advantage": [60, 100], "carry_over": [0.75], "use_margin": [True]}
    pred, chosen = bt.walk_forward(games, range(2023, 2025), train_window=2, grid=grid)
    assert set(pred["season"]) == {2023, 2024}
    assert list(chosen.index) == [2023, 2024]
    table = ev.calibration_table(pred["p_elo_wf"], pred["home_win"])
    assert table["n"].sum() == len(pred)


def test_probabilites_implicites_et_esperance():
    ph, pa, margin = ev.implied_probabilities(1.90, 1.90)
    assert ph == pytest.approx(0.5) and pa == pytest.approx(0.5)
    assert margin == pytest.approx(2 / 1.9 - 1)
    assert ev.expected_value(0.5, 1.90) == pytest.approx(-0.05)
    assert ev.expected_value(0.55, 2.00) == pytest.approx(0.10)
