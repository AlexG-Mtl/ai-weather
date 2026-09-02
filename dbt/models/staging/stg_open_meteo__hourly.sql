with responses as (
    select * from {{ source('open_meteo', 'responses') }}
),

flattened as (
    select
        try_to_timestamp_ntz(hour.value::string) as weather_hour_utc,
        responses.location_name,
        responses.requested_latitude::float as latitude,
        responses.requested_longitude::float as longitude,
        responses.payload:hourly:temperature_2m[hour.index]::float as temperature_c,
        responses.payload:hourly:relative_humidity_2m[hour.index]::integer as relative_humidity_pct,
        responses.payload:hourly:precipitation[hour.index]::float as precipitation_mm,
        responses.payload:hourly:weather_code[hour.index]::integer as weather_code,
        responses.payload:hourly:wind_speed_10m[hour.index]::float as wind_speed_kmh,
        responses.fetched_at,
        responses.content_hash as source_content_hash
    from responses,
    lateral flatten(input => responses.payload:hourly:time) hour
)

select * from flattened
