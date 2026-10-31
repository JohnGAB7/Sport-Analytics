"""Rapprochement des noms d'équipes The Odds API -> football-data.co.uk."""

import pytest

from football_analytics.teams import match_team, normalize

EPL = ["Arsenal", "Man United", "Man City", "Nott'm Forest", "Wolves", "Brighton", "West Ham", "Tottenham"]
L1 = ["Paris SG", "Paris FC", "Lens", "St Etienne", "Monaco", "Brest"]
BUNDES = ["Dortmund", "M'gladbach", "FC Koln", "Ein Frankfurt", "Mainz", "St Pauli", "Hoffenheim"]


@pytest.mark.parametrize("name,cands,expected", [
    ("Manchester United", EPL, "Man United"), ("Manchester City", EPL, "Man City"),
    ("Nottingham Forest", EPL, "Nott'm Forest"), ("Wolverhampton Wanderers", EPL, "Wolves"),
    ("Brighton and Hove Albion", EPL, "Brighton"), ("Arsenal", EPL, "Arsenal"),
    ("Paris Saint Germain", L1, "Paris SG"), ("Paris FC", L1, "Paris FC"), ("RC Lens", L1, "Lens"),
    ("Saint Etienne", L1, "St Etienne"), ("AS Monaco", L1, "Monaco"),
    ("Borussia Monchengladbach", BUNDES, "M'gladbach"), ("1. FC Köln", BUNDES, "FC Koln"),
    ("FSV Mainz 05", BUNDES, "Mainz"), ("FC St. Pauli", BUNDES, "St Pauli"),
    ("TSG 1899 Hoffenheim", BUNDES, "Hoffenheim"),
])
def test_noms_connus(name, cands, expected):
    assert match_team(name, cands) == expected


def test_nom_inconnu_ou_ambigu_renvoie_none():
    assert match_team("Real Madrid", EPL) is None
    assert match_team("United", ["Man United", "Sheffield United"]) is None   # ambigu : on ne devine pas


def test_normalisation():
    assert normalize("Atlético  Madrid") == "atletico madrid"
