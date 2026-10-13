select
  customer_id,
  lower(trim(email)) as email,
  updated_at
from {{ source('raw', 'customers') }}
qualify row_number() over (partition by customer_id order by updated_at desc) = 1