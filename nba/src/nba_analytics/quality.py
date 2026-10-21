"""Contrôles de qualité de la table des matchs.

Chaque fonction renvoie un résultat inspectable (DataFrame ou dictionnaire)
plutôt que de lever une exception : le but est de *décrire* les problèmes,
la décision de corriger ou d'exclure une ligne reste explicite et documentée.
"""

from __future__ import annotations

import pandas as pd

from .schema import (
    EXPECTED_DTYPES,
    MAX_PLAUSIBLE_PTS,
    MIN_PLAUSIBLE_PTS,
    REQUIRED_COLUMNS,
    SEASON_START_MONTH,
)


def load_games_csv(path) -> pd.DataFrame:
    """Charge un CSV de matchs en texte brut (aucune conversion implicite).

    Lire tout en `str` évite que pandas devine les types silencieusement ;
    la conversion se fait ensuite, de façon contrôlée, avec `coerce_types`.
    """
    return pd.read_csv(path, dtype=str, keep_default_na=True)


def missing_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Nombre et pourcentage de valeurs manquantes par colonne."""
    n_missing = df.isna().sum()
    return pd.DataFrame({
        "n_missing": n_missing,
        "pct_missing": (100 * n_missing / max(len(df), 1)).round(2),
    }).sort_values("n_missing", ascending=False)


def coerce_types(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Convertit les colonnes vers les types attendus.

    Les valeurs non convertibles deviennent manquantes (NaT / <NA>) au lieu de
    faire échouer le chargement. Renvoie aussi, par colonne, le nombre de
    valeurs *présentes* qui n'ont pas pu être converties : c'est ce chiffre
    qui révèle les données corrompues.
    """
    out = df.copy()
    failures: dict[str, int] = {}
    for col, dtype in EXPECTED_DTYPES.items():
        if col not in out.columns:
            continue
        before_na = out[col].isna()
        if dtype.startswith("datetime"):
            converted = pd.to_datetime(out[col], errors="coerce", format="mixed")
        elif dtype in ("int64", "Int64"):
            converted = pd.to_numeric(out[col], errors="coerce")
            non_integer = converted.notna() & (converted % 1 != 0)
            converted = converted.mask(non_integer).astype("Int64")
        elif dtype == "boolean":
            mapping = {"true": True, "false": False, "1": True, "0": False}
            converted = out[col].map(
                lambda v: v if isinstance(v, bool) else mapping.get(str(v).strip().lower())
            ).astype("boolean")
        else:
            converted = out[col].astype("string")
        failures[col] = int((converted.isna() & ~before_na).sum())
        out[col] = converted
    return out, failures


def dtype_report(df: pd.DataFrame) -> pd.DataFrame:
    """Compare les types effectifs aux types attendus."""
    rows = []
    for col, expected in EXPECTED_DTYPES.items():
        actual = str(df[col].dtype) if col in df.columns else "ABSENTE"
        # Tolérances : season peut être Int64 (nullable) ; la résolution des dates
        # (ns, us...) dépend de la version de pandas (pandas 3 utilise us par défaut).
        ok = (actual == expected
              or (expected == "int64" and actual == "Int64")
              or (expected.startswith("datetime64") and actual.startswith("datetime64")))
        rows.append({"column": col, "expected": expected, "actual": actual, "ok": ok})
    return pd.DataFrame(rows)


def expected_season(dates: pd.Series) -> pd.Series:
    """Saison NBA d'une date : nommée d'après l'année de fin."""
    return dates.dt.year + (dates.dt.month >= SEASON_START_MONTH).astype("Int64")


def date_issues(df: pd.DataFrame, today: pd.Timestamp | None = None) -> pd.DataFrame:
    """Lignes dont la date est absente, dans le futur, hors saison ou incohérente avec `season`."""
    today = today or pd.Timestamp.today().normalize()
    d = df["game_date"]
    flags = pd.DataFrame(index=df.index)
    flags["date_missing"] = d.isna()
    flags["date_in_future"] = d > today
    flags["off_season_month"] = d.dt.month.isin([7, 8, 9]).fillna(False).astype(bool)
    season_from_date = expected_season(d)
    flags["season_mismatch"] = (
        (season_from_date != df["season"]).fillna(False).astype(bool) & d.notna()
    )
    return df.loc[flags.any(axis=1)].join(flags.loc[flags.any(axis=1)])


def duplicate_report(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Trois niveaux de doublons, du plus strict au plus métier."""
    return {
        # Ligne strictement identique (souvent un double chargement).
        "exact_rows": df[df.duplicated(keep=False)],
        # Même identifiant de match pour deux lignes.
        "game_id": df[df.duplicated("game_id", keep=False)],
        # Même affiche le même jour, quel que soit l'identifiant.
        "same_matchup_same_day": df[
            df.duplicated(["game_date", "home_team", "away_team"], keep=False)
        ],
    }


def team_double_booked(df: pd.DataFrame) -> pd.DataFrame:
    """Équipes ayant plus d'un match à la même date (impossible en pratique)."""
    long = pd.concat([
        df[["game_id", "game_date", "home_team"]].rename(columns={"home_team": "team"}),
        df[["game_id", "game_date", "away_team"]].rename(columns={"away_team": "team"}),
    ])
    long = long.drop_duplicates(["game_id", "team"])
    counts = long.groupby(["game_date", "team"]).size()
    return counts[counts > 1].rename("n_games").reset_index()


def logic_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Incohérences métier : auto-affrontement, scores négatifs/implausibles, matchs nuls."""
    h, a = df["home_pts"], df["away_pts"]
    flags = pd.DataFrame(index=df.index)
    flags["same_team"] = (df["home_team"] == df["away_team"]).fillna(False).astype(bool)
    flags["negative_pts"] = ((h < 0) | (a < 0)).fillna(False).astype(bool)
    implausible = (h < MIN_PLAUSIBLE_PTS) | (h > MAX_PLAUSIBLE_PTS) | \
                  (a < MIN_PLAUSIBLE_PTS) | (a > MAX_PLAUSIBLE_PTS)
    flags["implausible_pts"] = implausible.fillna(False).astype(bool) & ~flags["negative_pts"]
    flags["tie"] = (h == a).fillna(False).astype(bool)
    bad = flags.any(axis=1)
    return df.loc[bad].join(flags.loc[bad])


def run_all_checks(df_raw: pd.DataFrame) -> dict:
    """Enchaîne tous les contrôles et renvoie un résumé chiffré + les détails."""
    cols = missing_columns(df_raw)
    if cols:
        return {"missing_columns": cols}
    df, conversion_failures = coerce_types(df_raw)
    dups = duplicate_report(df)
    dates = date_issues(df)
    logic = logic_issues(df)
    double = team_double_booked(df.dropna(subset=["game_date"]))
    summary = {
        "n_rows": len(df),
        "n_missing_cells": int(df[REQUIRED_COLUMNS].isna().sum().sum()),
        "conversion_failures": sum(conversion_failures.values()),
        "exact_duplicate_rows": len(dups["exact_rows"]),
        "duplicate_game_id_rows": len(dups["game_id"]),
        "date_issue_rows": len(dates),
        "logic_issue_rows": len(logic),
        "team_double_booked": len(double),
    }
    return {
        "missing_columns": [],
        "summary": summary,
        "data": df,
        "conversion_failures": conversion_failures,
        "missing": missing_report(df),
        "dtypes": dtype_report(df),
        "duplicates": dups,
        "dates": dates,
        "logic": logic,
        "double_booked": double,
    }


def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Statistiques par saison sur les matchs dont le score est complet."""
    d = df.dropna(subset=["home_pts", "away_pts"]).copy()
    d["margin"] = (d["home_pts"] - d["away_pts"]).astype(float)
    d["total"] = (d["home_pts"] + d["away_pts"]).astype(float)
    d["home_win"] = d["margin"] > 0
    stats = d.groupby("season").agg(
        n_games=("game_id", "count"),
        n_teams=("home_team", "nunique"),
        first_date=("game_date", "min"),
        last_date=("game_date", "max"),
        mean_home_pts=("home_pts", "mean"),
        mean_away_pts=("away_pts", "mean"),
        home_win_rate=("home_win", "mean"),
        mean_margin=("margin", "mean"),
        sd_margin=("margin", "std"),
        mean_total=("total", "mean"),
        sd_total=("total", "std"),
    )
    numeric = stats.select_dtypes("number").columns
    stats[numeric] = stats[numeric].round(3)
    return stats
