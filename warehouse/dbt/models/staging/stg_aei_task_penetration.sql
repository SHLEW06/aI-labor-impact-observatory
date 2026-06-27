-- Anthropic Economic Index: AI penetration scores by task text.
-- Joined to O*NET tasks via fuzzy/exact task text matching in intermediate layer.

select
    trim(task) as task_text,
    penetration
from {{ source('raw', 'raw_aei_task_penetration') }}
