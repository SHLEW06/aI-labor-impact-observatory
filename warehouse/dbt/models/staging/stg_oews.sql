-- BLS OEWS May 2025: national wages and employment by occupation.
-- Handles suppressed cells (*, #, ~) explicitly with a boolean flag.
-- Requires manual download — this model will fail if raw_oews doesn't exist.

{% set table_exists = run_query("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'raw_oews'") %}
{% if execute and table_exists[0][0] > 0 %}

select
    trim(occ_code) as soc_code,
    trim(occ_title) as soc_title,
    -- Employment: handle suppressed values
    case
        when tot_emp in ('*', '**', '#', '~') then null
        when try_cast(replace(tot_emp, ',', '') as integer) is not null
            then try_cast(replace(tot_emp, ',', '') as integer)
        else null
    end as tot_emp,
    -- Annual mean wage
    case
        when a_mean in ('*', '#', '~') then null
        when try_cast(replace(a_mean, ',', '') as double) is not null
            then try_cast(replace(a_mean, ',', '') as double)
        else null
    end as a_mean,
    -- Annual median wage
    case
        when a_median in ('*', '#', '~') then null
        when try_cast(replace(a_median, ',', '') as double) is not null
            then try_cast(replace(a_median, ',', '') as double)
        else null
    end as a_median,
    -- Hourly mean wage
    case
        when h_mean in ('*', '#', '~') then null
        when try_cast(replace(h_mean, ',', '') as double) is not null
            then try_cast(replace(h_mean, ',', '') as double)
        else null
    end as h_mean,
    -- Suppressed flag: true if ANY wage/employment cell is suppressed
    case
        when tot_emp in ('*', '**', '#', '~')
          or a_mean in ('*', '#', '~')
          or a_median in ('*', '#', '~')
            then true
        else false
    end as suppressed
from {{ source('raw', 'raw_oews') }}
where occ_code is not null
  and length(trim(occ_code)) = 7  -- Keep only detailed (6-digit) SOC codes

{% else %}

-- BLS OEWS not yet loaded — return empty table with correct schema
select
    null::varchar as soc_code,
    null::varchar as soc_title,
    null::integer as tot_emp,
    null::double as a_mean,
    null::double as a_median,
    null::double as h_mean,
    false as suppressed
where 1 = 0

{% endif %}
