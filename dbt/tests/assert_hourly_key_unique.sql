select source_content_hash, weather_hour_utc
from {{ ref('stg_open_meteo__hourly') }}
group by 1, 2
having count(*) > 1
