-- Official O*NET-SOC 2019 → 6-digit 2018 SOC crosswalk.
-- This is the canonical mapping used throughout the pipeline.
-- 1,016 O*NET-SOC codes → 867 unique SOC codes.

select
    trim(onet_soc_2019_code) as onet_soc_code,
    trim("2018_soc_code") as soc_code,
    trim(onet_soc_2019_title) as onet_title,
    trim("2018_soc_title") as soc_title
from {{ source('raw', 'raw_onet_soc_crosswalk') }}
where onet_soc_2019_code is not null
