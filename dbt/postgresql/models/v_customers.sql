SELECT
  customer_id,
  LOWER(TRIM(email)) AS email,
  updated_at
FROM (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY updated_at DESC) AS rn
  FROM {{ source('raw', 'customers') }}
) AS ranked
WHERE
  rn = 1