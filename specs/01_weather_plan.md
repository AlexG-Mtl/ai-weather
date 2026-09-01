# Montreal Hourly Weather: Implementation Plan

## Goal and scope

Build a small, reviewable data-engineering slice that fetches historical hourly weather for Montreal from Open-Meteo, stores each untouched JSON response in Snowflake, and exposes one dbt staging model.

The intended demonstration flow is **Plan → Build → Review**. Scheduling, multiple locations, dashboards, production infrastructure, and broader transformation layers are out of scope.

## Design

```text
Open-Meteo Historical Weather API
                ↓
        Python ingestion command
                ↓
 AI_DWH.WEATHER_RAW.OPEN_METEO_RESPONSES
                ↓
       stg_open_meteo__hourly
```

### Extraction and raw load

Add a Python 3.12 command managed with `uv`. The command will:

- Require `start_date` and `end_date` as ISO dates.
- Reject an invalid or reversed range before making a request.
- Use fixed Montreal coordinates: latitude `45.5019`, longitude `-73.5674`.
- Request UTC timestamps to avoid daylight-saving ambiguity.
- Fetch these hourly fields from the Open-Meteo Historical Weather API:
  - `temperature_2m`
  - `relative_humidity_2m`
  - `precipitation`
  - `weather_code`
  - `wind_speed_10m`
- Validate the HTTP result and minimum expected JSON structure.
- Load the complete, untouched response into a Snowflake `VARIANT` column.

The target will use the existing `AI_DWH` environment and `ai_dwh_svc` authentication. Connection details and credentials will be supplied through environment variables and will not be committed.

Create the dedicated raw schema `AI_DWH.WEATHER_RAW` for this project.

Proposed raw table:

| Column | Purpose |
|---|---|
| `content_hash` | SHA-256 of the canonical response, used as the load key |
| `location_name` | Constant value `Montreal` |
| `requested_latitude` | Requested coordinate |
| `requested_longitude` | Requested coordinate |
| `start_date` | Requested range start |
| `end_date` | Requested range end |
| `fetched_at` | UTC ingestion timestamp |
| `source_url` | Open-Meteo endpoint, excluding secrets (none are expected) |
| `payload` | Untouched response as `VARIANT` |

Load with a `MERGE` keyed by `content_hash`. An identical rerun is harmless, while a changed upstream response is retained as a new raw record.

### dbt staging model

Add a minimal dbt project with a source definition for the raw table and one view named `stg_open_meteo__hourly`.

The model will flatten `payload:hourly:time`. Each flattened array index will select the corresponding values from the other hourly arrays.

Output grain: one row per source response and weather hour.

Proposed columns:

- `weather_hour_utc`
- `location_name`
- `latitude`
- `longitude`
- `temperature_c`
- `relative_humidity_pct`
- `precipitation_mm`
- `weather_code`
- `wind_speed_kmh`
- `fetched_at`
- `source_content_hash`

Keep execution explicit: one ingestion command followed by one dbt command. No orchestrator will be introduced.

### Expected project structure

```text
src/ai_weather/
  cli.py
  open_meteo.py
  snowflake.py
sql/
  create_raw_objects.sql
dbt/
  dbt_project.yml
  models/staging/
    _open_meteo__sources.yml
    _open_meteo__models.yml
    stg_open_meteo__hourly.sql
tests/
  fixtures/open_meteo_response.json
  test_open_meteo.py
README.md
```

## Acceptance criteria

- A documented command requires explicit `start_date` and `end_date` and fetches Montreal historical weather in UTC.
- The request contains the fixed coordinates and five agreed hourly variables.
- Invalid dates, HTTP failures, malformed responses, and Snowflake failures return a non-zero exit with a useful error.
- A successful run stores the untouched JSON response plus request and ingestion metadata in the dedicated raw schema in `AI_DWH`.
- Repeating a load with an identical response creates no duplicate raw record.
- No credentials or account-specific secrets are committed.
- `dbt run --select stg_open_meteo__hourly` builds the staging view from the declared source.
- Staged values are correctly typed and aligned by the hourly array index.
- dbt tests verify:
  - `weather_hour_utc` and `source_content_hash` are not null.
  - `(source_content_hash, weather_hour_utc)` is unique.
  - humidity is between 0 and 100.
  - precipitation is non-negative.
- Python unit tests exercise request construction, response validation, and failure handling using mocks and a small synthetic fixture.
- The README documents `uv` setup, required environment variables, raw-object creation, ingestion, dbt execution, data grain, and inspection queries.
- Review includes comparing the first and last raw hourly entries with their staged rows.

## Approved decisions

- Use historical rather than forecast weather data.
- Require explicit start and end dates; provide no implicit date window.
- Preserve each complete Open-Meteo JSON response in `VARIANT`.
- Use the existing Snowflake `AI_DWH` environment with `ai_dwh_svc` authentication.
- Create the separate `AI_DWH.WEATHER_RAW` schema for the weather project.
- Manage Python dependencies and commands with `uv`.

## Out of scope

- Scheduling or orchestration
- Automated rolling loads or large backfills
- Additional cities or weather variables
- Forecast data
- Intermediate or mart models
- Dashboards and alerting
- Deployment infrastructure and CI/CD
