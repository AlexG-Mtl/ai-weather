import argparse
import sys

from ai_weather.open_meteo import fetch_weather, parse_date_range
from ai_weather.snowflake import load_response


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Montreal historical weather")
    parser.add_argument("start_date", help="inclusive ISO date (YYYY-MM-DD)")
    parser.add_argument("end_date", help="inclusive ISO date (YYYY-MM-DD)")
    args = parser.parse_args()
    try:
        start, end = parse_date_range(args.start_date, args.end_date)
        url, payload = fetch_weather(args.start_date, args.end_date)
        content_hash = load_response(payload, url, start, end)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(content_hash)


if __name__ == "__main__":
    main()
