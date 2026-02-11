-- Backfill main_constraint and uncertainty_meta for existing user_state rows.
-- Rule:
--   scarcity = 1 - value
--   main_constraint = axis with max scarcity
--   uncertainty_meta = 1 - avg(confidences)

BEGIN;

WITH s AS (
  SELECT
    user_id,
    money_value,
    time_value,
    energy_value,
    asset_value,
    reliability_value,
    identity_value,
    money_confidence,
    time_confidence,
    energy_confidence,
    asset_confidence,
    reliability_confidence,
    identity_confidence,
    GREATEST(
      1 - money_value,
      1 - time_value,
      1 - energy_value,
      1 - asset_value,
      1 - reliability_value,
      1 - identity_value
    ) AS max_scarcity,
    (
      money_confidence + time_confidence + energy_confidence +
      asset_confidence + reliability_confidence + identity_confidence
    ) / 6.0 AS avg_conf
  FROM user_state
), m AS (
  SELECT
    user_id,
    CASE
      WHEN (1 - money_value) = max_scarcity THEN 'money'
      WHEN (1 - time_value) = max_scarcity THEN 'time'
      WHEN (1 - energy_value) = max_scarcity THEN 'energy'
      WHEN (1 - asset_value) = max_scarcity THEN 'asset'
      WHEN (1 - reliability_value) = max_scarcity THEN 'reliability'
      ELSE 'identity'
    END AS inferred_main_constraint,
    GREATEST(0.0, LEAST(1.0, 1.0 - avg_conf)) AS inferred_uncertainty
  FROM s
)
UPDATE user_state u
SET main_constraint = m.inferred_main_constraint,
    uncertainty_meta = m.inferred_uncertainty,
    last_updated = NOW()
FROM m
WHERE u.user_id = m.user_id;

COMMIT;
