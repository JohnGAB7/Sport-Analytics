"""Tests des contrôles de qualité : chaque défaut injecté doit être détecté,
et des données propres ne doivent déclencher aucune alerte."""

import pandas as pd
import pytest

from nba_analytics import quality
from nba_analytics.synthetic import generate_games, inject_defects


@pytest.fixture(scope="module")
def clean_csv(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "games.csv"
    generate_games(seasons=[2023, 2024], seed=11).to_csv(path, index=False)
    return path


@pytest.fixture(scope="module")
def dirty_csv(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "games_dirty.csv"
    inject_defects(generate_games(seasons=[2023, 2024], seed=11), seed=3).to_csv(path, index=False)
    return path


def test_donnees_propres_aucune_alerte(clean_csv):
    res = quality.run_all_checks(quality.load_games_csv(clean_csv))
    s = res["summary"]
    assert res["missing_columns"] == []
    assert s["n_missing_cells"] == 0
    assert s["conversion_failures"] == 0
    assert s["exact_duplicate_rows"] == 0
    assert s["duplicate_game_id_rows"] == 0
    assert s["date_issue_rows"] == 0
    assert s["logic_issue_rows"] == 0
    assert s["team_double_booked"] == 0
    assert res["dtypes"]["ok"].all()


def test_defauts_detectes(dirty_csv):
    res = quality.run_all_checks(quality.load_games_csv(dirty_csv))
    s = res["summary"]
    # 3 scores manquants + 1 date illisible devenue NaT.
    assert s["n_missing_cells"] == 4
    assert res["conversion_failures"]["game_date"] == 1
    # 2 lignes recopiées => 4 lignes concernées (originaux + copies).
    assert s["exact_duplicate_rows"] == 4
    assert s["duplicate_game_id_rows"] == 4
    flags = res["logic"]
    assert flags["same_team"].sum() == 1
    assert flags["negative_pts"].sum() == 1
    assert flags["tie"].sum() == 1
    dates = res["dates"]
    assert dates["date_missing"].sum() == 1
    assert dates["off_season_month"].sum() == 1


def test_colonne_absente_signalee():
    df = pd.DataFrame({"game_id": ["A"], "season": ["2024"]})
    res = quality.run_all_checks(df)
    assert "game_date" in res["missing_columns"]
    assert "summary" not in res


def test_coerce_types_signale_les_valeurs_non_convertibles():
    raw = pd.DataFrame({
        "game_id": ["A", "B"], "season": ["2024", "2024"],
        "game_date": ["2023-11-01", "31/02/2024"],
        "home_team": ["T01", "T02"], "away_team": ["T03", "T04"],
        "home_pts": ["110", "abc"], "away_pts": ["100.5", "99"],
        "is_playoffs": ["False", "peut-etre"],
    })
    df, failures = quality.coerce_types(raw)
    assert failures["game_date"] == 1   # 31 février n'existe pas
    assert failures["home_pts"] == 1    # texte
    assert failures["away_pts"] == 1    # score non entier
    assert failures["is_playoffs"] == 1
    assert str(df["home_pts"].dtype) == "Int64"


def test_saison_deduite_de_la_date():
    dates = pd.Series(pd.to_datetime(["2023-10-24", "2024-04-14", "2024-06-17"]))
    assert quality.expected_season(dates).tolist() == [2024, 2024, 2024]


def test_incoherence_saison_detectee():
    df = generate_games(seasons=[2024], seed=12)
    df.loc[0, "season"] = 2020
    issues = quality.date_issues(df, today=pd.Timestamp("2030-01-01"))
    assert issues["season_mismatch"].sum() == 1


def test_equipe_deux_fois_le_meme_jour():
    df = generate_games(seasons=[2024], seed=13)
    extra = df.iloc[[0]].copy()
    extra["game_id"] = "EXTRA"
    extra["away_team"] = "T99"
    res = quality.team_double_booked(pd.concat([df, extra], ignore_index=True))
    assert len(res) >= 1


def test_statistiques_descriptives():
    df = generate_games(seasons=[2023, 2024], seed=14)
    stats = quality.descriptive_stats(df)
    assert list(stats.index) == [2023, 2024]
    assert stats["n_teams"].eq(30).all()
    assert stats["mean_total"].between(200, 250).all()
