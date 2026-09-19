
CREATE TABLE IF NOT EXISTS farmers (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    mobile TEXT NOT NULL,
    farmer_id TEXT,
    crop TEXT NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    slot TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    bank_name TEXT,
    account_holder TEXT,
    account_number TEXT,
    ifsc_code TEXT,
    tracking_id TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS shipment_tracking (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL UNIQUE REFERENCES farmers(token) ON DELETE CASCADE,
    tracking_id TEXT NOT NULL UNIQUE,
    stage TEXT NOT NULL DEFAULT 'At Procurement Centre',
    location_name TEXT NOT NULL DEFAULT 'Procurement Centre',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    accuracy DOUBLE PRECISION,
    last_updated TEXT,
    gps_active BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS tracking_updates (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL REFERENCES farmers(token) ON DELETE CASCADE,
    stage TEXT,
    location_name TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    accuracy DOUBLE PRECISION,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS farmer_effort (
    token TEXT PRIMARY KEY REFERENCES farmers(token) ON DELETE CASCADE,
    visit_count INTEGER NOT NULL DEFAULT 1,
    first_registered_at TEXT,
    first_quality_at TEXT,
    last_updated TEXT
);

CREATE TABLE IF NOT EXISTS lot_trace (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL REFERENCES farmers(token) ON DELETE CASCADE,
    step_key TEXT NOT NULL,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    detail TEXT,
    updated_at TEXT,
    UNIQUE(token, step_key)
);

CREATE TABLE IF NOT EXISTS rejection_records (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL REFERENCES farmers(token) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    guidance TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_state (
    state_key TEXT PRIMARY KEY,
    current_queue_token INTEGER NOT NULL DEFAULT 97,
    next_token_number INTEGER NOT NULL DEFAULT 101,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_farmers_created_at ON farmers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_farmers_mobile ON farmers(mobile);
CREATE INDEX IF NOT EXISTS idx_tracking_updates_token ON tracking_updates(token, id DESC);
CREATE INDEX IF NOT EXISTS idx_lot_trace_token ON lot_trace(token, id);
CREATE INDEX IF NOT EXISTS idx_rejections_token ON rejection_records(token, id DESC);

INSERT INTO app_state(state_key, current_queue_token, next_token_number, updated_at)
VALUES ('global', 97, 101, CURRENT_TIMESTAMP::text)
ON CONFLICT (state_key) DO NOTHING;
