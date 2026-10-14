{{ config(materialized='incremental', unique_key='ORDER_ID', incremental_strategy='merge') }}
WITH migration_candidates AS (
SELECT
  ORDER_ID,
  CUSTOMER_ID,
  ORDER_DATE,
  (
    ROUND(AMOUNT * (
      1 - COALESCE(DISCOUNT_PCT, 0) / 100.0
    ), 2)
  ) AS NET_AMOUNT,
  STATUS,
  CAST(GET_PATH(METADATA, 'channel') AS VARCHAR) AS CHANNEL,
  UPDATED_AT
FROM {{ source('raw', 'orders') }}
WHERE
  dbt_incremental_filter
QUALIFY
  ROW_NUMBER() OVER (PARTITION BY ORDER_ID ORDER BY UPDATED_AT DESC) = 1
)
SELECT candidate.* FROM migration_candidates AS candidate
{% if is_incremental() %}
WHERE NOT EXISTS (SELECT 1 FROM {{ this }} AS existing WHERE existing.ORDER_ID = candidate.ORDER_ID AND (candidate.UPDATED_AT < existing.UPDATED_AT OR candidate.UPDATED_AT IS NULL OR existing.UPDATED_AT IS NULL))
{% endif %}