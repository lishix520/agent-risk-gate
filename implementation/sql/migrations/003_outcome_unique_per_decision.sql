-- Migration: enforce one outcome row per decision_id (latest wins)

BEGIN;

WITH ranked AS (
    SELECT
        outcome_id,
        decision_id,
        ROW_NUMBER() OVER (PARTITION BY decision_id ORDER BY created_at DESC, outcome_id DESC) AS rn
    FROM action_outcome
)
DELETE FROM action_outcome a
USING ranked r
WHERE a.outcome_id = r.outcome_id
  AND r.rn > 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_action_outcome_decision_unique
ON action_outcome(decision_id);

COMMIT;
