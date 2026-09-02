select *
from {{ ref('stg_open_meteo__hourly') }}
where precipitation_mm < 0
