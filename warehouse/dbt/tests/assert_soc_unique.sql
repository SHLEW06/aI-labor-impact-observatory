-- Custom test: mart_occupation_exposure must have unique soc_code.
-- Returns rows that violate uniqueness (= failures).

select
    soc_code,
    count(*) as n
from {{ ref('mart_occupation_exposure') }}
group by soc_code
having count(*) > 1
