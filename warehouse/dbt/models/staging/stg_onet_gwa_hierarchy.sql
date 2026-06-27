-- O*NET 30.3: GWA → IWA → DWA hierarchy.
-- Maps each Detailed Work Activity up to its parent General Work Activity.
-- Used for admin/clinical classification of tasks.

select
    trim(gwa_element_id) as gwa_element_id,
    trim(gwa_element_name) as gwa_element_name,
    trim(iwa_element_id) as iwa_element_id,
    trim(iwa_element_name) as iwa_element_name,
    trim(dwa_element_id) as dwa_element_id,
    trim(dwa_element_name) as dwa_element_name
from {{ source('raw', 'raw_onet_gwas_to_iwas_to_dwas') }}
