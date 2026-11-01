"""Lecture des fichiers football-data.co.uk (contenu fictif, aucun appel réseau)."""

import pandas as pd
import pytest

from football_analytics.leagues import season_code, season_of
from football_analytics.sources import footballdata as fd

RECENT = """Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A,AvgH,AvgD,AvgA,PSCH,PSCD,PSCA
E0,15/08/2025,20:00,Liverpool,Bournemouth,4,2,H,1.3,6.0,9.0,1.31,5.8,8.9,1.29,6.2,9.8
E0,16/08/2025,12:30,Aston Villa,Newcastle,0,0,D,2.6,3.4,2.7,2.55,3.45,2.75,,,
E0,23/08/2025,15:00,Arsenal,Leeds,,,,1.2,7.0,13.0,1.21,6.9,12.5,,,
"""

OLD = "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,BbAvH,BbAvD,BbAvA\nF1,10/08/13,Monaco,Bordeaux,2,0,H,1.6,3.8,5.5\n"


def test_codes_de_saison():
    assert season_code(2026) == "2526" and season_code(2000) == "9900"
    assert season_of("2025-08-15") == 2026 and season_of("2026-05-20") == 2026


def test_lecture_fichier_recent():
    g = fd.parse(RECENT, "EPL", 2026)
    assert len(g) == 2                                      # le match pas encore joué est ignoré
    assert g.loc[0, "date"] == pd.Timestamp("2025-08-15")
    assert g.loc[0, "odds_home"] == 1.31                    # cote moyenne préférée à Bet365
    assert g.loc[0, "close_home"] == 1.29
    assert pd.isna(g.loc[1, "close_home"])                  # cote de clôture manquante -> NaN
    assert g["home_goals"].tolist() == [4, 0]


def test_lecture_ancien_format():
    g = fd.parse(OLD, "LIGUE1", 2014)
    assert g.loc[0, "date"] == pd.Timestamp("2013-08-10") and g.loc[0, "odds_away"] == 5.5


def test_ligne_illisible_signalee():
    with pytest.raises(ValueError):
        fd.parse(RECENT.replace("15/08/2025", "date?"), "EPL", 2026)


def test_decodage_latin1():
    assert fd._decode("Málaga".encode("latin-1")) == "Málaga"


class FakeResponse:
    def __init__(self, raw, status=200):
        self.content, self.status = raw, status

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self):
        self.urls = []

    def get(self, url, timeout=None):
        self.urls.append(url)
        return FakeResponse(RECENT.encode("utf-8-sig"))


def test_cache(tmp_path):
    s = FakeSession()
    fd.download("EPL", 2026, tmp_path, session=s)
    fd.download("EPL", 2026, tmp_path, session=s)          # relu dans le cache
    assert s.urls == ["https://www.football-data.co.uk/mmz4281/2526/E0.csv"]
    fd.download("EPL", 2026, tmp_path, refresh=True, session=s)
    assert len(s.urls) == 2
