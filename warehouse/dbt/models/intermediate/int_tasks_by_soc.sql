-- Collapse O*NET tasks to 6-digit SOC, importance-weighted.
-- Multiple O*NET-SOC variants (e.g., .00/.01/.02) are averaged.
--
-- Judgment call: 845 tasks lack Importance ratings.
-- When an occupation HAS rated tasks, shares are importance-weighted.
-- When ALL tasks lack ratings (7 occupations), shares fall back to
-- simple count-based proportions. Documented in methodology.md.

with task_level as (
    select
        tc.soc_code,
        tc.task_id,
        tc.task,
        tc.task_category,
        tc.is_admin,
        tc.is_clinical,
        tc.importance,
        tc.importance_suppressed
    from {{ ref('int_task_classification') }} tc
)

select
    soc_code,
    count(distinct task_id) as n_tasks,
    count(distinct case when importance is not null then task_id end) as n_rated_tasks,
    avg(importance) as mean_importance,
    -- Admin/clinical shares: importance-weighted when ratings exist,
    -- falling back to simple count-based shares when all tasks lack ratings.
    case
        when sum(case when importance is not null then importance else 0 end) > 0
        then sum(case when is_admin = 1 and importance is not null then importance else 0 end)
           / sum(case when importance is not null then importance else 0 end)
        when count(distinct task_id) > 0
        then cast(count(distinct case when is_admin = 1 then task_id end) as double)
           / cast(count(distinct task_id) as double)
        else null
    end as admin_share,
    case
        when sum(case when importance is not null then importance else 0 end) > 0
        then sum(case when is_clinical = 1 and importance is not null then importance else 0 end)
           / sum(case when importance is not null then importance else 0 end)
        when count(distinct task_id) > 0
        then cast(count(distinct case when is_clinical = 1 then task_id end) as double)
           / cast(count(distinct task_id) as double)
        else null
    end as clinical_share,
    -- Count by category
    count(distinct case when task_category = 'admin' then task_id end) as n_admin_tasks,
    count(distinct case when task_category = 'clinical' then task_id end) as n_clinical_tasks,
    count(distinct case when task_category = 'both' then task_id end) as n_both_tasks,
    count(distinct case when task_category = 'other' then task_id end) as n_other_tasks
from task_level
group by soc_code
