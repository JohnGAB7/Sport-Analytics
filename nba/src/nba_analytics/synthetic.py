"""Générateur de données synthétiques de matchs NBA.

Objectif : disposer d'un jeu de données réaliste dans sa *forme* (calendrier,
avantage du terrain, ordres de grandeur des scores) mais entièrement fictif,
donc libre de droits. Les équipes s'appellent T01 à T30 et ne correspondent
à aucune équipe réelle.

Modèle génératif (simple, assumé) :
    points_domicile  ~ Normale(moyenne + attaque_dom - défense_ext + avantage_terrain, sigma)
    points_extérieur ~ Normale(moyenne + attaque_ext - défense_dom, sigma)
    En cas d'égalité, on simule des prolongations (+5 minutes) jusqu'à départager.

Ce modèle sert uniquement à tester le pipeline ; il ne doit pas être utilisé
pour tirer des conclusions sur le basketball réel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

N_TEAMS = 30
GAMES_PER_TEAM = 82
MEAN_PTS = 112.0
SIGMA_PTS = 12.0
HOME_ADVANTAGE = 2.5
OVERTIME_MEAN_PTS = 11.0


def team_codes(n_teams: int = N_TEAMS) -> list[str]:
    return [f"T{i:02d}" for i in range(1, n_teams + 1)]


def _schedule_season(rng: np.random.Generator, teams: list[str], season: int,
                     games_per_team: int) -> list[tuple[pd.Timestamp, str, str]]:
    """Construit un calendrier : chaque jour, des équipes disponibles sont appariées.

    Une équipe joue au plus un match par jour. On s'arrête lorsque chaque équipe
    a atteint `games_per_team` matchs, ou qu'il ne reste qu'une seule équipe
    en dessous (elle peut alors finir avec un match de moins).
    """
    games_played = dict.fromkeys(teams, 0)
    day = pd.Timestamp(year=season - 1, month=10, day=22)
    schedule = []
    while True:
        remaining = [t for t in teams if games_played[t] < games_per_team]
        if len(remaining) < 2:
            break
        # Priorité aux équipes en retard, avec un peu d'aléa.
        rng.shuffle(remaining)
        remaining.sort(key=lambda t: games_played[t])
        n_today = min(len(remaining), int(rng.integers(8, 25)))
        n_today -= n_today % 2
        today = list(rng.permutation(remaining[:n_today]))
        for home, away in zip(today[0::2], today[1::2]):
            schedule.append((day, str(home), str(away)))
            games_played[home] += 1
            games_played[away] += 1
        day += pd.Timedelta(days=1)
    return schedule


def _simulate_score(rng: np.random.Generator, att_h: float, def_h: float,
                    att_a: float, def_a: float) -> tuple[int, int]:
    home = rng.normal(MEAN_PTS + att_h - def_a + HOME_ADVANTAGE, SIGMA_PTS)
    away = rng.normal(MEAN_PTS + att_a - def_h, SIGMA_PTS)
    home, away = int(round(home)), int(round(away))
    while home == away:  # prolongation(s)
        home += int(rng.poisson(OVERTIME_MEAN_PTS))
        away += int(rng.poisson(OVERTIME_MEAN_PTS))
    return home, away


def generate_games(seasons: list[int] | None = None, seed: int = 42,
                   n_teams: int = N_TEAMS,
                   games_per_team: int = GAMES_PER_TEAM) -> pd.DataFrame:
    """Génère des matchs de saison régulière synthétiques, triés chronologiquement.

    Les forces d'équipe (attaque, défense) sont tirées une fois par saison.
    Le résultat est entièrement déterminé par `seed` (reproductible).
    """
    if seasons is None:
        seasons = [2022, 2023, 2024]
    rng = np.random.default_rng(seed)
    teams = team_codes(n_teams)
    rows = []
    for season in seasons:
        attack = dict(zip(teams, rng.normal(0, 3, n_teams)))
        defense = dict(zip(teams, rng.normal(0, 3, n_teams)))
        for date, home, away in _schedule_season(rng, teams, season, games_per_team):
            h_pts, a_pts = _simulate_score(rng, attack[home], defense[home],
                                           attack[away], defense[away])
            rows.append({
                "season": season,
                "game_date": date,
                "home_team": home,
                "away_team": away,
                "home_pts": h_pts,
                "away_pts": a_pts,
                "is_playoffs": False,
            })
    df = pd.DataFrame(rows).sort_values(["game_date", "home_team"], kind="stable")
    df.insert(0, "game_id", [f"SYN{i:06d}" for i in range(1, len(df) + 1)])
    df["source"] = "synthetic"
    return df.reset_index(drop=True)


def inject_defects(df: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Ajoute volontairement des défauts connus pour vérifier que les contrôles les détectent.

    Défauts injectés (un exemplaire de chaque, sauf mention) :
      - 3 valeurs manquantes dans home_pts ;
      - 1 date illisible et 1 date hors saison ;
      - 2 lignes dupliquées à l'identique ;
      - 1 match où une équipe joue contre elle-même ;
      - 1 score négatif ;
      - 1 match nul (impossible en NBA).
    """
    rng = np.random.default_rng(seed)
    out = df.copy()
    out["home_pts"] = out["home_pts"].astype("Int64")
    out["game_date"] = out["game_date"].astype("object")
    idx = rng.choice(len(out), size=8, replace=False)
    out.loc[idx[0:3], "home_pts"] = pd.NA
    out.loc[idx[3], "game_date"] = "pas-une-date"
    out.loc[idx[4], "game_date"] = pd.Timestamp(year=int(out.loc[idx[4], "season"]), month=8, day=15)
    out.loc[idx[5], "away_team"] = out.loc[idx[5], "home_team"]
    out.loc[idx[6], "away_pts"] = -5
    out.loc[idx[7], "away_pts"] = out.loc[idx[7], "home_pts"]
    dupes = out.iloc[[0, 1]]
    return pd.concat([out, dupes], ignore_index=True)
