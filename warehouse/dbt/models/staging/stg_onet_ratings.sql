-- O*NET 30.3 task ratings, filtered to Importance scale (IM).
-- Used for importance-weighting when aggregating tasks to SOC level.
-- Also preserves Frequency (FT) for optional analysis.

select
    trim(r.onet_soc_code) as onet_soc_code,
    x.soc_code,
    r.task_id,
    r.scale_id,
    r.scale_name,
    r.data_value,
    r.n as n_respondents,
    r.standard_error,
    r.lower_ci_bound,
    r.upper_ci_bound,
    case when r.recommend_suppress = 'Y' then true else false end as recommend_suppress
from {{ source('raw', 'raw_onet_task_ratings') }} r
inner join {{ ref('stg_onet_soc_crosswalk') }} x
    on trim(r.onet_soc_code) = x.onet_soc_code
where r.scale_id in ('IM', 'FT')
  and r.category is null  -- The summary row (not per-category breakdowns)
