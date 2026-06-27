-- Classify each task as admin, clinical, or other via GWA/DWA mapping.
--
-- Admin GWAs (per spec §4):
--   - Documenting/Recording Information (4.A.3.b.6)
--   - Working with Computers (4.A.3.b.1)
--   - Performing Administrative Activities (4.A.4.c.1)
--
-- Clinical GWAs (per spec §4):
--   - Assisting and Caring for Others (4.A.4.a.5)
--   - Making Decisions and Solving Problems (4.A.2.b.1)
--
-- Logic: a task is tagged admin if ANY of its DWAs roll up to an admin GWA;
-- tagged clinical if ANY roll up to a clinical GWA. Tasks can be both
-- (e.g., documenting a clinical decision) — the shares account for this.

with task_gwas as (
    -- For each task, find ALL GWAs it connects to via DWAs
    select distinct
        td.onet_soc_code,
        td.soc_code,
        td.task_id,
        gh.gwa_element_id,
        gh.gwa_element_name
    from {{ ref('stg_onet_tasks_to_dwas') }} td
    inner join {{ ref('stg_onet_gwa_hierarchy') }} gh
        on td.dwa_element_id = gh.dwa_element_id
),

task_tags as (
    select
        onet_soc_code,
        soc_code,
        task_id,
        -- Admin flag: task connects to any admin GWA
        max(case when gwa_element_id in (
            '4.A.3.b.6',  -- Documenting/Recording Information
            '4.A.3.b.1',  -- Working with Computers
            '4.A.4.c.1'   -- Performing Administrative Activities
        ) then 1 else 0 end) as is_admin,
        -- Clinical flag: task connects to any clinical GWA
        max(case when gwa_element_id in (
            '4.A.4.a.5',  -- Assisting and Caring for Others
            '4.A.2.b.1'   -- Making Decisions and Solving Problems
        ) then 1 else 0 end) as is_clinical
    from task_gwas
    group by onet_soc_code, soc_code, task_id
)

select
    tt.onet_soc_code,
    tt.soc_code,
    tt.task_id,
    t.task,
    t.task_type,
    r.data_value as importance,
    r.recommend_suppress as importance_suppressed,
    tt.is_admin,
    tt.is_clinical,
    case
        when tt.is_admin = 1 and tt.is_clinical = 0 then 'admin'
        when tt.is_clinical = 1 and tt.is_admin = 0 then 'clinical'
        when tt.is_admin = 1 and tt.is_clinical = 1 then 'both'
        else 'other'
    end as task_category
from task_tags tt
inner join {{ ref('stg_onet_tasks') }} t
    on tt.onet_soc_code = t.onet_soc_code
    and tt.task_id = t.task_id
left join {{ ref('stg_onet_ratings') }} r
    on tt.onet_soc_code = r.onet_soc_code
    and tt.task_id = r.task_id
    and r.scale_id = 'IM'
