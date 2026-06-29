-- BLS OEWS May 2025: national wages and employment by 6-digit SOC.
-- Handles suppressed wage cells (*, #, ~) explicitly with a boolean flag.
-- Never coerces suppressed values to zero.
-- Requires manual download — this model returns an empty (typed) shell
-- if raw_oews has not been loaded yet.

{% set table_exists = run_query("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'raw_oews'") %}
{% if execute and table_exists[0][0] > 0 %}

-- raw_oews has heterogeneous types after pandas read_excel: tot_emp comes
-- through as BIGINT (no suppression markers in this file), wage columns
-- come through as VARCHAR with '*' suppression markers.
select
    trim(occ_code) as soc_code,
    trim(occ_title) as soc_title,
    tot_emp,
    case
        when a_mean in ('*', '**', '#', '~') then null
        else try_cast(replace(a_mean, ',', '') as double)
    end as a_mean,
    case
        when a_median in ('*', '**', '#', '~') then null
        else try_cast(replace(a_median, ',', '') as double)
    end as a_median,
    case
        when h_mean in ('*', '**', '#', '~') then null
        else try_cast(replace(h_mean, ',', '') as double)
    end as h_mean,
    case
        when a_mean in ('*', '**', '#', '~')
          or a_median in ('*', '**', '#', '~')
          or h_mean in ('*', '**', '#', '~')
            then true
        else false
    end as suppressed
from {{ source('raw', 'raw_oews') }}
where occ_code is not null
  and o_group = 'detailed'  -- 6-digit detailed SOC rows (excludes major/minor/broad aggregates)

{% else %}

select
    null::varchar as soc_code,
    null::varchar as soc_title,
    null::bigint as tot_emp,
    null::double as a_mean,
    null::double as a_median,
    null::double as h_mean,
    false as suppressed
where 1 = 0

{% endif %}
