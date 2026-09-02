# AI Weather

Minimal ingestion of Montreal historical hourly weather into Snowflake, followed by a dbt staging view.

## Setup

Install Python 3.12 dependencies:

```sh
uv sync
```

Ingestion and dbt use the existing Snowflake CLI named connection `ai_dwh_svc`, including its key-pair authentication. Override the selected CLI connection with `SNOWFLAKE_CONNECTION_NAME`. No separate password or dbt credential variables are required.

Create the raw objects using the existing connection:

```sh
snow sql -c ai_dwh_svc -f sql/create_raw_objects.sql
```

## Run

Both dates are required and inclusive:

```sh
uv run ai-weather 2024-01-01 2024-01-02
uv run ai-weather-dbt run --project-dir dbt --profiles-dir dbt --select stg_open_meteo__hourly
uv run ai-weather-dbt test --project-dir dbt --profiles-dir dbt --select stg_open_meteo__hourly
```

The staging grain is one row per raw response and UTC weather hour. An identical response is loaded only once because the raw `MERGE` is keyed by its canonical JSON SHA-256.

## Inspect

Compare the first and last raw array entries with the staged rows:

```sql
select payload:hourly:time[0], payload:hourly:time[array_size(payload:hourly:time)-1]
from AI_DWH.WEATHER_RAW.OPEN_METEO_RESPONSES
order by fetched_at desc limit 1;

select * from AI_DWH.WEATHER_STAGING.STG_OPEN_METEO__HOURLY
qualify source_content_hash = first_value(source_content_hash) over (order by fetched_at desc)
order by weather_hour_utc;
```
