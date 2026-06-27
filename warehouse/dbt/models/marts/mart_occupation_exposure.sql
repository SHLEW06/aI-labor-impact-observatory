-- mart_occupation_exposure: the deliverable table.
-- One row per 6-digit 2018 SOC code. Carries theoretical exposure,
-- observed exposure, the diffusion gap, wages, employment, education proxy,
-- and admin/clinical shares for healthcare occupations.
--
-- Schema matches spec §7 exactly.
--
-- IMPORTANT FRAMING: exposure is potential capability, not realized job loss.
-- The diffusion_gap measures where theoretical potential exceeds observed
-- adoption — it does NOT imply those occupations will experience job loss.

with soc_titles as (
    -- Get one title per SOC (from crosswalk, deduplicated)
    select distinct
        soc_code,
        first_value(soc_title) over (partition by soc_code order by soc_title) as soc_title
    from {{ ref('stg_onet_soc_crosswalk') }}
),

job_zones as (
    -- Collapse Job Zone to SOC level (mode or first)
    select
        soc_code,
        -- When multiple O*NET-SOC variants exist, take the most common Job Zone
        mode(job_zone) as job_zone
    from {{ ref('stg_onet_job_zones') }}
    group by soc_code
),

base as (
    select distinct soc_code from (
        select soc_code from {{ ref('int_exposure_by_soc') }}
        union
        select soc_code from {{ ref('int_tasks_by_soc') }}
    )
)

select
    b.soc_code,
    st.soc_title,
    -- Major group: first 2 digits + '-0000'
    left(b.soc_code, 2) || '-0000' as major_group,
    -- Health flag: SOC major groups 29 (Practitioners) and 31 (Support)
    case
        when left(b.soc_code, 2) in ('29', '31') then true
        else false
    end as is_health,
    -- Task counts
    t.n_tasks,
    t.n_rated_tasks,
    t.mean_importance,
    -- Exposure measures
    e.theoretical_exposure,
    e.observed_exposure,
    -- Diffusion gap: theoretical minus observed.
    -- Both are on [0, 1] scales, so direct subtraction is meaningful.
    -- Positive = theoretical potential exceeds observed usage.
    case
        when e.theoretical_exposure is not null and e.observed_exposure is not null
        then e.theoretical_exposure - e.observed_exposure
        else null
    end as diffusion_gap,
    -- Admin/clinical shares (meaningful primarily for health occupations)
    t.admin_share,
    t.clinical_share,
    -- Wages and employment (from OEWS, may be null if not yet loaded)
    w.tot_emp,
    w.a_mean,
    w.a_median,
    w.h_mean,
    -- Education proxy
    jz.job_zone,
    -- Suppressed flag (OEWS)
    coalesce(w.suppressed, false) as suppressed,
    -- Additional exposure variants for robustness
    e.theoretical_e1,
    e.theoretical_e1_e2,
    e.theoretical_human_beta,
    e.n_onet_variants,
    -- Task category counts
    t.n_admin_tasks,
    t.n_clinical_tasks,
    t.n_both_tasks,
    t.n_other_tasks
from base b
left join soc_titles st on b.soc_code = st.soc_code
left join {{ ref('int_tasks_by_soc') }} t on b.soc_code = t.soc_code
left join {{ ref('int_exposure_by_soc') }} e on b.soc_code = e.soc_code
left join {{ ref('stg_oews') }} w on b.soc_code = w.soc_code
left join job_zones jz on b.soc_code = jz.soc_code
