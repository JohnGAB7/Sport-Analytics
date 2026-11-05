"""La clé The Odds API ne doit jamais apparaître dans un message d'erreur.

Ces messages finissent dans les journaux publics d'Actions et dans registry/report.json.
"""

import pytest
import requests

from football_analytics.sources import oddsapi

KEY = "cle-secrete-0123456789abcdef"


class FakeResponse:
    def __init__(self, status):
        self.status_code, self.ok, self.headers = status, status < 400, {}

    def json(self):
        return []


class FakeSession:
    def __init__(self, status=None, exc=None):
        self.status, self.exc = status, exc

    def get(self, url, params=None, timeout=None):
        if self.exc:
            raise self.exc(f"Max retries exceeded with url: {url}?apiKey={params['apiKey']}")
        return FakeResponse(self.status)


def _call(session):
    return oddsapi.fetch_odds(KEY, "soccer_epl", session=session)


@pytest.mark.parametrize("session", [FakeSession(status=401), FakeSession(status=429),
                                     FakeSession(exc=requests.ConnectionError),
                                     FakeSession(exc=requests.Timeout)])
def test_error_message_never_contains_key(session):
    with pytest.raises(requests.RequestException) as info:
        _call(session)
    err = info.value
    assert KEY not in str(err)
    assert err.__cause__ is None and err.__suppress_context__


def test_http_error_keeps_status_code():
    with pytest.raises(requests.HTTPError, match="401"):
        _call(FakeSession(status=401))


def test_success_returns_events():
    events, _ = _call(FakeSession(status=200))
    assert events == []
