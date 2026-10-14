SELECT
  o.*,
  c.CHANNEL_NAME,
  c.IS_DIGITAL
FROM {{ ref('v_orders') }} AS o
LEFT JOIN {{ ref('channel_catalog') }} AS c
  ON o.CHANNEL = c.CHANNEL_CODE