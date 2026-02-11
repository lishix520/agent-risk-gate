-- Migration: v1.1 -> v1.2
-- Goals:
-- 1) improve retrieval and audit query performance
-- 2) strengthen idempotency and event backfill support
-- 3) keep backward compatibility

BEGIN;

-- 1) memory_entries retrieval indexes
CREATE INDEX IF NOT EXISTS idx_memory_user_layer_cost_created
ON memory_entries (user_id, memory_layer, continuity_cost DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memory_user_system_caused
ON memory_entries (user_id, system_caused, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memory_user_irreversible
ON memory_entries (user_id, irreversible, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memory_missing_axes_gin
ON memory_entries USING GIN (missing_axes);

-- 2) state_evidence analytic indexes
CREATE INDEX IF NOT EXISTS idx_state_evidence_user_axis_created
ON state_evidence (user_id, resource_axis, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_state_evidence_signal_type_created
ON state_evidence (signal_type, created_at DESC);

-- 3) decision/outcome join indexes
CREATE INDEX IF NOT EXISTS idx_action_outcome_decision
ON action_outcome (decision_id);

CREATE INDEX IF NOT EXISTS idx_action_outcome_failure
ON action_outcome (user_id, continuity_failure, created_at DESC);

-- 4) idempotency operational index
CREATE INDEX IF NOT EXISTS idx_chat_idempotency_created
ON chat_idempotency (created_at DESC);

-- 5) optional columns for calibration metadata (backward compatible)
ALTER TABLE decision_log
ADD COLUMN IF NOT EXISTS trace_id TEXT;

ALTER TABLE action_outcome
ADD COLUMN IF NOT EXISTS calibration_version TEXT DEFAULT 'v1';

COMMIT;
