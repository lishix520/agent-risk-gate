CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS user_state (
    user_id TEXT PRIMARY KEY,

    money_value DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    money_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.3,
    time_value DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    time_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.3,
    energy_value DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    energy_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.3,
    asset_value DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    asset_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.3,
    reliability_value DOUBLE PRECISION NOT NULL DEFAULT 0.8,
    reliability_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    identity_value DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    identity_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.3,

    main_constraint TEXT CHECK (main_constraint IN ('money','time','energy','asset','reliability','identity')),
    uncertainty_meta DOUBLE PRECISION NOT NULL DEFAULT 0.0,

    update_count INTEGER NOT NULL DEFAULT 0,
    user_profile JSONB,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT state_range_check CHECK (
        money_value BETWEEN 0 AND 1 AND
        money_confidence BETWEEN 0 AND 1 AND
        time_value BETWEEN 0 AND 1 AND
        time_confidence BETWEEN 0 AND 1 AND
        energy_value BETWEEN 0 AND 1 AND
        energy_confidence BETWEEN 0 AND 1 AND
        asset_value BETWEEN 0 AND 1 AND
        asset_confidence BETWEEN 0 AND 1 AND
        reliability_value BETWEEN 0 AND 1 AND
        reliability_confidence BETWEEN 0 AND 1 AND
        identity_value BETWEEN 0 AND 1 AND
        identity_confidence BETWEEN 0 AND 1 AND
        uncertainty_meta BETWEEN 0 AND 1
    )
);

CREATE INDEX IF NOT EXISTS idx_user_state_updated ON user_state(last_updated DESC);

CREATE TABLE IF NOT EXISTS state_evidence (
    evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_state(user_id) ON DELETE CASCADE,
    resource_axis TEXT NOT NULL CHECK (resource_axis IN ('money','time','energy','asset','reliability','identity')),
    before_value DOUBLE PRECISION NOT NULL,
    after_value DOUBLE PRECISION NOT NULL,
    signal_type TEXT NOT NULL CHECK (signal_type IN ('behavior','language','explicit','external')),
    signal_text TEXT NOT NULL,
    weight DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT evidence_range_check CHECK (
        before_value BETWEEN 0 AND 1 AND
        after_value BETWEEN 0 AND 1 AND
        weight BETWEEN 0 AND 1 AND
        confidence BETWEEN 0 AND 1
    )
);

CREATE INDEX IF NOT EXISTS idx_state_evidence_user_created ON state_evidence(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS memory_entries (
    entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_state(user_id) ON DELETE CASCADE,

    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_class TEXT NOT NULL,
    raw_context TEXT NOT NULL,

    delta_money DOUBLE PRECISION NOT NULL DEFAULT 0,
    delta_time DOUBLE PRECISION NOT NULL DEFAULT 0,
    delta_energy DOUBLE PRECISION NOT NULL DEFAULT 0,
    delta_asset DOUBLE PRECISION NOT NULL DEFAULT 0,
    delta_reliability DOUBLE PRECISION NOT NULL DEFAULT 0,
    delta_identity DOUBLE PRECISION NOT NULL DEFAULT 0,

    axis_confidence JSONB,
    missing_axes JSONB,

    pre_state_snapshot JSONB NOT NULL,

    continuity_cost DOUBLE PRECISION NOT NULL,
    irreversible BOOLEAN NOT NULL DEFAULT FALSE,
    system_caused BOOLEAN NOT NULL DEFAULT FALSE,

    memory_weight DOUBLE PRECISION NOT NULL,
    memory_layer INTEGER NOT NULL CHECK (memory_layer BETWEEN 1 AND 4),

    risk_vector VECTOR(8),
    related_entry_ids UUID[],

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_memory_user_time ON memory_entries(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memory_user_layer ON memory_entries(user_id, memory_layer);
CREATE INDEX IF NOT EXISTS idx_memory_user_cost ON memory_entries(user_id, continuity_cost DESC);
CREATE INDEX IF NOT EXISTS idx_memory_vector ON memory_entries USING ivfflat (risk_vector vector_cosine_ops) WITH (lists = 100);

CREATE TABLE IF NOT EXISTS memory_objects (
    object_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_state(user_id) ON DELETE CASCADE,
    object_type TEXT NOT NULL CHECK (object_type IN ('shell','success_path')),
    name TEXT,
    text_index TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('high','medium','low')),
    validity TEXT NOT NULL CHECK (validity IN ('long','medium','short')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_objects_user_type_updated ON memory_objects(user_id, object_type, updated_at DESC);

CREATE TABLE IF NOT EXISTS conversation_history (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_state(user_id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
    content TEXT NOT NULL,
    event_impact_id UUID REFERENCES memory_entries(entry_id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_user_session_time ON conversation_history(user_id, session_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS decision_log (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_state(user_id) ON DELETE CASCADE,

    context TEXT NOT NULL,
    candidate_actions JSONB NOT NULL,
    selected_action JSONB NOT NULL,

    predicted_gain DOUBLE PRECISION,
    predicted_risk DOUBLE PRECISION,
    uncertainty_penalty DOUBLE PRECISION,
    memory_penalty DOUBLE PRECISION,
    decision_score DOUBLE PRECISION NOT NULL,

    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decision_user_time ON decision_log(user_id, timestamp DESC);

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

CREATE TABLE IF NOT EXISTS action_outcome (
    outcome_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id BIGINT NOT NULL REFERENCES decision_log(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES user_state(user_id) ON DELETE CASCADE,

    predicted_impact_vector JSONB,
    actual_impact_vector JSONB,
    vector_error_l1 DOUBLE PRECISION,

    predicted_cost DOUBLE PRECISION,
    actual_cost DOUBLE PRECISION,
    cost_error DOUBLE PRECISION,

    continuity_failure BOOLEAN NOT NULL DEFAULT FALSE,
    failure_type TEXT,
    user_visible_cost TEXT,
    preventable BOOLEAN,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outcome_user_created ON action_outcome(user_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_action_outcome_decision_unique ON action_outcome(decision_id);

CREATE TABLE IF NOT EXISTS chat_idempotency (
    user_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT,
    response_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, idempotency_key)
);
