CREATE SCHEMA IF NOT EXISTS AI_DWH.WEATHER_RAW;

CREATE TABLE IF NOT EXISTS AI_DWH.WEATHER_RAW.OPEN_METEO_RESPONSES (
    content_hash VARCHAR NOT NULL,
    location_name VARCHAR NOT NULL,
    requested_latitude FLOAT NOT NULL,
    requested_longitude FLOAT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    fetched_at TIMESTAMP_TZ NOT NULL,
    source_url VARCHAR NOT NULL,
    payload VARIANT NOT NULL
);
