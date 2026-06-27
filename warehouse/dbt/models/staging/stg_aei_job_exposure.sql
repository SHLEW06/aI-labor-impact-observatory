-- Anthropic Economic Index: observed AI exposure by occupation.
-- Already at 6-digit SOC level (756 occupations).

select
    trim(occ_code) as soc_code,
    trim(title) as soc_title,
    observed_exposure
from {{ source('raw', 'raw_aei_job_exposure') }}
