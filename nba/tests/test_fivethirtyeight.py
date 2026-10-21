"""Tests de l'adaptateur FiveThirtyEight sur un petit extrait écrit à la main
(au format du fichier d'origine), sans téléchargement."""

import io

import pandas as pd
import pytest

from nba_analytics import quality
from nba_analytics.sources import fivethirtyeight as f38

HEADER = ("gameorder,game_id,lg_id,_iscopy,year_id,date_game,seasongame,is_playoffs,team_id,"
          "fran_id,pts,elo_i,elo_n,win_equiv,opp_id,opp_fran,opp_pts,opp_elo_i,opp_elo_n,"
          "game_location,game_result,forecast,notes\n")
ROWS = [
    # Match 1 : deux lignes (domicile puis copie extérieur).
    "1,194611010TRH,NBA,0,1947,11/1/1946,1,0,TRH,Huskies,66,1300,1293,40,NYK,Knicks,68,1300,1306,H,L,0.64,",
    "1,194611010TRH,NBA,1,1947,11/1/1946,1,0,NYK,Knicks,68,1300,1306,41,TRH,Huskies,66,1300,1293,A,W,0.36,",
    # Match 2 : terrain neutre, playoffs.
    "2,194704020PHW,NBA,0,1947,4/2/1947,2,1,PHW,Warriors,80,1400,1410,50,CHS,Stags,70,1400,1390,N,W,0.5,at Chicago IL",
    "2,194704020PHW,NBA,1,1947,4/2/1947,2,1,CHS,Stags,70,1400,1390,30,PHW,Warriors,80,1400,1410,N,L,0.5,at Chicago IL",
    # Match 3 : ABA, exclu par défaut.
    "3,196710130ANA,ABA,0,1968,10/13/1967,1,0,ANA,Squires,110,1300,1310,45,DNR,Nuggets,100,1300,1290,H,W,0.6,",
    "3,196710130ANA,ABA,1,1968,10/13/1967,1,0,DNR,Nuggets,100,1300,1290,40,ANA,Squires,110,1300,1310,A,L,0.4,",
]


@pytest.fixture
def raw():
    return pd.read_csv(io.StringIO(HEADER + "\n".join(ROWS) + "\n"), dtype=str)


def test_une_ligne_par_match_et_nba_seulement(raw):
    g = f38.to_games(raw)
    assert g["game_id"].tolist() == ["194611010TRH", "194704020PHW"]


def test_option_aba(raw):
    assert len(f38.to_games(raw, leagues=("NBA", "ABA"))) == 3


def test_domicile_exterieur_et_dates(raw):
    g = f38.to_games(raw).set_index("game_id")
    assert (g.loc["194611010TRH", "home_team"], g.loc["194611010TRH", "away_team"]) == ("TRH", "NYK")
    assert (g.loc["194611010TRH", "home_pts"], g.loc["194611010TRH", "away_pts"]) == ("66", "68")
    assert g.loc["194611010TRH", "game_date"] == "1946-11-01"
    assert g.loc["194704020PHW", "neutral_site"]
    assert not g.loc["194611010TRH", "neutral_site"]


def test_pas_de_colonnes_elo(raw):
    g = f38.to_games(raw)
    assert not any(c.startswith("elo") or c == "forecast" for c in g.columns)


def test_compatible_avec_les_controles(raw):
    res = quality.run_all_checks(f38.to_games(raw))
    assert res["missing_columns"] == []
    assert res["summary"]["conversion_failures"] == 0
    assert res["dtypes"]["ok"].all()
    assert bool(res["data"].set_index("game_id").loc["194704020PHW", "is_playoffs"]) is True


def test_colonne_absente_refusee(raw):
    with pytest.raises(ValueError):
        f38.to_games(raw.drop(columns=["_iscopy"]))


def test_empreinte_verifiee(tmp_path):
    fake = tmp_path / "nbaallelo.csv"
    fake.write_text(HEADER)
    with pytest.raises(ValueError, match="Empreinte inattendue"):
        f38.download(fake)


def test_incoherence_id_date_detectee(raw):
    g = f38.to_games(raw)
    assert f38.id_date_mismatches(g).empty
    g.loc[0, "game_id"] = "194611020TRH"  # le 2 novembre au lieu du 1er
    assert f38.id_date_mismatches(g)["game_id"].tolist() == ["194611020TRH"]
