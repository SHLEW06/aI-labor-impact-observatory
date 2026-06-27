-- Collapse exposure scores to 6-digit SOC level.
-- Theoretical (Eloundou) starts at O*NET-SOC; average across variants.
-- Observed (AEI) is already at 6-digit SOC.

with theoretical as (
    select
        soc_code,
        avg(exposure_beta) as theoretical_exposure,
        avg(exposure_e1) as theoretical_e1,
        avg(exposure_e1_plus_e2) as theoretical_e1_e2,
        avg(human_beta) as theoretical_human_beta,
        count(*) as n_onet_variants
    from {{ ref('stg_eloundou') }}
    group by soc_code
),

observed as (
    select
        soc_code,
        observed_exposure
    from {{ ref('stg_aei_job_exposure') }}
)

select
    coalesce(t.soc_code, o.soc_code) as soc_code,
    t.theoretical_exposure,
    t.theoretical_e1,
    t.theoretical_e1_e2,
    t.theoretical_human_beta,
    t.n_onet_variants,
    o.observed_exposure
from theoretical t
full outer join observed o on t.soc_code = o.soc_code
