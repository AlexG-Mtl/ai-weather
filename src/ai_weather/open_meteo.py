import json
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
LATITUDE = 45.5019
LONGITUDE = -73.5674
HOURLY_FIELDS = (
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "weather_code",
    "wind_speed_10m",
)


def parse_date_range(start_date: str, end_date: str) -> tuple[date, date]:
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as exc:
        raise ValueError("start_date and end_date must be ISO dates (YYYY-MM-DD)") from exc
    if start > end:
        raise ValueError("start_date must be on or before end_date")
    return start, end


def build_url(start_date: str, end_date: str) -> str:
    parse_date_range(start_date, end_date)
    query = urlencode(
        {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(HOURLY_FIELDS),
            "timezone": "UTC",
        }
    )
    return f"{BASE_URL}?{query}"


def validate_response(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Open-Meteo response must be a JSON object")
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
        raise ValueError("Open-Meteo response is missing hourly.time")
    expected_length = len(hourly["time"])
    for field in HOURLY_FIELDS:
        values = hourly.get(field)
        if not isinstance(values, list):
            raise ValueError(f"Open-Meteo response is missing hourly.{field}")
        if len(values) != expected_length:
            raise ValueError(f"hourly.{field} is not aligned with hourly.time")
    return payload


def fetch_weather(start_date: str, end_date: str) -> tuple[str, dict]:
    url = build_url(start_date, end_date)
    try:
        with urlopen(url, timeout=30) as response:  # noqa: S310 - fixed HTTPS host
            payload = json.load(response)
    except Exception as exc:
        raise RuntimeError(f"Open-Meteo request failed: {exc}") from exc
    return url, validate_response(payload)
