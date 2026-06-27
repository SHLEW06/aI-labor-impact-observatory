-- Custom test: every Eloundou occupation (at SOC level) must appear in the mart.
-- This ensures the crosswalk doesn't silently drop occupations.
-- Returns SOC codes that exist in exposure data but not in the mart.

with eloundou_socs as (
    select distinct soc_code
    from {{ ref('int_exposure_by_soc') }}
    where theoretical_exposure is not null
)

select e.soc_code
from eloundou_socs e
left join {{ ref('mart_occupation_exposure') }} m
    on e.soc_code = m.soc_code
where m.soc_code is null
