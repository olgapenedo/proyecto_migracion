SELECT
  o.ORDER_ID,
  o.CUSTOMER_ID,
  o.ORDER_DATE,
  (
    ROUND(o.AMOUNT * (
      1 - COALESCE(o.DISCOUNT_PCT, 0) / 100.0
    ), 2)
  ) AS NET_AMOUNT,
  CAST(GET_PATH(o.METADATA, 'channel') AS VARCHAR) AS CHANNEL,
  c.EMAIL,
  o.UPDATED_AT
FROM {{ source('raw', 'orders') }} AS o
JOIN {{ ref('v_customers') }} AS c
  ON o.CUSTOMER_ID = c.CUSTOMER_ID
WHERE
  o.STATUS = 'completed'