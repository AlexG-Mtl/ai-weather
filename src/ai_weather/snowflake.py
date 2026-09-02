import hashlib
import json
import os
from datetime import date, datetime, timezone

import snowflake.connector


def canonical_payload(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def connect():
    return snowflake.connector.connect(
        connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME", "ai_dwh_svc"),
        database="AI_DWH",
        schema="WEATHER_RAW",
    )


def load_response(
    payload: dict,
    source_url: str,
    start_date: date,
    end_date: date,
    connection=None,
) -> str:
    payload_json = canonical_payload(payload)
    content_hash = hashlib.sha256(payload_json.encode()).hexdigest()
    fetched_at = datetime.now(timezone.utc)
    owned_connection = connection is None
    connection = connection or connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                MERGE INTO AI_DWH.WEATHER_RAW.OPEN_METEO_RESPONSES target
                USING (
                    SELECT %s content_hash, %s location_name,
                           %s requested_latitude, %s requested_longitude,
                           %s start_date, %s end_date, %s fetched_at,
                           %s source_url, PARSE_JSON(%s) payload
                ) source
                ON target.content_hash = source.content_hash
                WHEN NOT MATCHED THEN INSERT (
                    content_hash, location_name, requested_latitude,
                    requested_longitude, start_date, end_date, fetched_at,
                    source_url, payload
                ) VALUES (
                    source.content_hash, source.location_name,
                    source.requested_latitude, source.requested_longitude,
                    source.start_date, source.end_date, source.fetched_at,
                    source.source_url, source.payload
                )
                """,
                (
                    content_hash,
                    "Montreal",
                    45.5019,
                    -73.5674,
                    start_date,
                    end_date,
                    fetched_at,
                    source_url,
                    payload_json,
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        if owned_connection:
            connection.close()
    return content_hash
