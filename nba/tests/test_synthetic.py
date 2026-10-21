"""Tests du générateur de données synthétiques."""

import pandas as pd

from nba_analytics.synthetic import generate_games, inject_defects


def test_reproductible_avec_la_meme_graine():
    a = generate_games(seasons=[2024], seed=1)
    b = generate_games(seasons=[2024], seed=1)
    pd.testing.assert_frame_equal(a, b)


def test_graines_differentes_donnent_des_scores_differents():
    a = generate_games(seasons=[2024], seed=1)
    b = generate_games(seasons=[2024], seed=2)
    assert not a["home_pts"].equals(b["home_pts"])


def test_volume_et_equipes():
    df = generate_games(seasons=[2024], seed=3)
    assert df["home_team"].nunique() == 30
    # 30 équipes x 82 matchs / 2 = 1230 ; une équipe peut finir à 81.
    assert 1229 <= len(df) <= 1230


def test_aucun_match_nul_ni_auto_affrontement():
    df = generate_games(seasons=[2023, 2024], seed=4)
    assert (df["home_pts"] != df["away_pts"]).all()
    assert (df["home_team"] != df["away_team"]).all()


def test_une_equipe_joue_au_plus_un_match_par_jour():
    df = generate_games(seasons=[2024], seed=5)
    long = pd.concat([df[["game_date", "home_team"]].set_axis(["d", "t"], axis=1),
                      df[["game_date", "away_team"]].set_axis(["d", "t"], axis=1)])
    assert not long.duplicated().any()


def test_ordre_chronologique_et_identifiants_uniques():
    df = generate_games(seasons=[2022, 2023], seed=6)
    assert df["game_date"].is_monotonic_increasing
    assert df["game_id"].is_unique


def test_avantage_du_terrain_visible():
    df = generate_games(seasons=[2022, 2023, 2024], seed=7)
    home_win_rate = (df["home_pts"] > df["away_pts"]).mean()
    # Avec +2.5 points d'avantage et sigma=12 par équipe, on attend ~55-58 %.
    assert 0.52 < home_win_rate < 0.62


def test_inject_defects_ajoute_deux_lignes():
    df = generate_games(seasons=[2024], seed=8)
    assert len(inject_defects(df)) == len(df) + 2
