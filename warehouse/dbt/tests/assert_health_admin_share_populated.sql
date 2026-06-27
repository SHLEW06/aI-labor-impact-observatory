-- Custom test: all health occupations (is_health = true) must have
-- non-null admin_share and clinical_share values.

select soc_code, soc_title
from {{ ref('mart_occupation_exposure') }}
where is_health = true
  and (admin_share is null or clinical_share is null)
