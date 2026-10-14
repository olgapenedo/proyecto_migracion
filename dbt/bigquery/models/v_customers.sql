SELECT
  customer_id,
  LOWER(TRIM(email)) AS email,
  updated_at
FROM `{{ source('raw', 'customers') }}`
QUALIFY
  ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY updated_at DESC) = 1