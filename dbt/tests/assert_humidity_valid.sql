select *
from {{ ref('stg_open_meteo__hourly') }}
where relative_humidity_pct not between 0 and 100
