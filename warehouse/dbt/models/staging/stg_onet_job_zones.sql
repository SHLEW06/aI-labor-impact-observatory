-- O*NET 30.3 Job Zones (education/training proxy).
-- As of O*NET 30.2, Job Zones are {2, 3, 4, 5} — Zone 1 was dropped.

select
    trim(j.onet_soc_code) as onet_soc_code,
    x.soc_code,
    j.job_zone
from {{ source('raw', 'raw_onet_job_zones') }} j
inner join {{ ref('stg_onet_soc_crosswalk') }} x
    on trim(j.onet_soc_code) = x.onet_soc_code
