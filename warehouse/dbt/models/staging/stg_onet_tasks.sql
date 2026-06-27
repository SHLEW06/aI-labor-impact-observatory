-- O*NET 30.3 task statements with SOC code derived via crosswalk.
-- One row per occupation-task pair. 18,796 rows.

select
    t.onet_soc_code,
    x.soc_code,
    t.task_id,
    t.task,
    t.task_type,
    t.incumbents_responding,
    t.date as survey_date,
    t.domain_source
from {{ source('raw', 'raw_onet_task_statements') }} t
inner join {{ ref('stg_onet_soc_crosswalk') }} x
    on trim(t.onet_soc_code) = x.onet_soc_code
