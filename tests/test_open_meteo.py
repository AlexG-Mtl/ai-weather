import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from ai_weather import open_meteo


@pytest.fixture
def payload():
    path = Path(__file__).parent / "fixtures" / "open_meteo_response.json"
    return json.loads(path.read_text())


def test_build_url_contains_fixed_request():
    query = parse_qs(urlparse(open_meteo.build_url("2024-01-01", "2024-01-02")).query)
    assert query["latitude"] == ["45.5019"]
    assert query["longitude"] == ["-73.5674"]
    assert query["timezone"] == ["UTC"]
    assert query["hourly"] == [",".join(open_meteo.HOURLY_FIELDS)]


@pytest.mark.parametrize("start,end", [("bad", "2024-01-02"), ("2024-01-03", "2024-01-02")])
def test_invalid_date_range_is_rejected(start, end):
    with pytest.raises(ValueError):
        open_meteo.build_url(start, end)


def test_validate_response_accepts_fixture(payload):
    assert open_meteo.validate_response(payload) is payload


def test_validate_response_rejects_misaligned_hourly_values(payload):
    payload["hourly"]["temperature_2m"].pop()
    with pytest.raises(ValueError, match="not aligned"):
        open_meteo.validate_response(payload)


def test_fetch_wraps_http_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr(open_meteo, "urlopen", fail)
    with pytest.raises(RuntimeError, match="Open-Meteo request failed"):
        open_meteo.fetch_weather("2024-01-01", "2024-01-02")
