-- O*NET 30.3: mapping of tasks to Detailed Work Activities (DWAs).
-- Used for admin/clinical tagging via the GWA → IWA → DWA hierarchy.

select
    trim(t.onet_soc_code) as onet_soc_code,
    x.soc_code,
    t.task_id,
    trim(t.dwa_element_id) as dwa_element_id,
    trim(t.dwa_element_name) as dwa_element_name
from {{ source('raw', 'raw_onet_tasks_to_dwas') }} t
inner join {{ ref('stg_onet_soc_crosswalk') }} x
    on trim(t.onet_soc_code) = x.onet_soc_code
