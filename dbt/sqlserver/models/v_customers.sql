select
  customer_id,
  lower(ltrim(rtrim(email))) as email,
  updated_at
from (
  select *, row_number() over (partition by customer_id order by updated_at desc) as rn
  from raw.customers
) as ranked
where rn = 1