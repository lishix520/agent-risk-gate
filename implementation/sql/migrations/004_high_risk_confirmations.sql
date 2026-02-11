BEGIN;

CREATE TABLE IF NOT EXISTS high_risk_confirmations (
    confirmation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id BIGINT NOT NULL REFERENCES decision_log(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES user_state(user_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    reason TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_confirmations_decision_user
ON high_risk_confirmations(decision_id, user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_confirmations_token_hash
ON high_risk_confirmations(token_hash);

COMMIT;
