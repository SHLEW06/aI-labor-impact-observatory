-- Eloundou et al. (2024) theoretical LLM exposure scores.
-- β = E1 + 0.5*E2 (the standard headline measure).
-- At O*NET-SOC level; collapsed to SOC in intermediate layer.

select
    trim(e.onet_soc_code) as onet_soc_code,
    x.soc_code,
    e.title,
    e.dv_rating_alpha as exposure_e1,           -- E1: exposed as-is (GPT-4 rating)
    e.dv_rating_beta as exposure_beta,           -- β = E1 + 0.5*E2
    e.dv_rating_gamma as exposure_e1_plus_e2,    -- E1 + E2: full software complement
    e.human_rating_alpha as human_e1,
    e.human_rating_beta as human_beta,
    e.human_rating_gamma as human_e1_plus_e2
from {{ source('raw', 'raw_eloundou') }} e
inner join {{ ref('stg_onet_soc_crosswalk') }} x
    on trim(e.onet_soc_code) = x.onet_soc_code
