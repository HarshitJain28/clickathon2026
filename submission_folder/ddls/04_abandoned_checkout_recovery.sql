-- Feature spec: Abandoned Checkout Recovery
-- All 6 events are new occurrences at their own grain (a drop, a nudge send,
-- a nudge open, a nudge click, a return, a reconversion) — none of them fire
-- at the same moment/grain as an existing baseline table's event, so all 6
-- get their own CREATE TABLE. No ALTER TABLE statements in this spec.
-- See justification.md for the full CREATE-vs-ALTER reasoning per event.

-- ============================================================
-- abandonment_detected — recovery flow origin (2,300 rows profiled)
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.abandonment_detected
(
    id UUID,
    timestamp DateTime,
    user_id String,
    application_id Nullable(String),
    device_type LowCardinality(String),
    os LowCardinality(Nullable(String)),
    app_version LowCardinality(String),
    client_lib LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city LowCardinality(String),
    destination FixedString(2),
    drop_step LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), drop_step, user_id, id)
SETTINGS index_granularity = 8192;

-- ============================================================
-- reminder_sent — recovery flow nudge, all 3 channels (2,300 rows profiled)
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.reminder_sent
(
    id UUID,
    timestamp DateTime,
    user_id String,
    application_id Nullable(String),
    device_type LowCardinality(String),
    os LowCardinality(Nullable(String)),
    app_version LowCardinality(String),
    client_lib LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city LowCardinality(String),
    destination FixedString(2),
    drop_step LowCardinality(String),
    channel LowCardinality(String),
    hours_since_drop UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), channel, user_id, id)
SETTINGS index_granularity = 8192;

-- ============================================================
-- reminder_opened — recovery flow nudge open (690 rows profiled)
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.reminder_opened
(
    id UUID,
    timestamp DateTime,
    user_id String,
    application_id Nullable(String),
    device_type LowCardinality(String),
    os LowCardinality(Nullable(String)),
    app_version LowCardinality(String),
    client_lib LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city LowCardinality(String),
    destination FixedString(2),
    drop_step LowCardinality(String),
    channel LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), channel, user_id, id)
SETTINGS index_granularity = 8192;

-- ============================================================
-- reminder_cta_clicked — recovery flow nudge click (268 rows profiled)
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.reminder_cta_clicked
(
    id UUID,
    timestamp DateTime,
    user_id String,
    application_id Nullable(String),
    device_type LowCardinality(String),
    os LowCardinality(Nullable(String)),
    app_version LowCardinality(String),
    client_lib LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city LowCardinality(String),
    destination FixedString(2),
    drop_step LowCardinality(String),
    channel LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), channel, user_id, id)
SETTINGS index_granularity = 8192;

-- ============================================================
-- resumed_at_step — recovery flow return event (268 rows profiled)
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.resumed_at_step
(
    id UUID,
    timestamp DateTime,
    user_id String,
    application_id Nullable(String),
    device_type LowCardinality(String),
    os LowCardinality(Nullable(String)),
    app_version LowCardinality(String),
    client_lib LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city LowCardinality(String),
    destination FixedString(2),
    drop_step LowCardinality(String),
    channel LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), drop_step, user_id, id)
SETTINGS index_granularity = 8192;

-- ============================================================
-- reconverted — recovery conversion (93 rows profiled)
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.reconverted
(
    id UUID,
    timestamp DateTime,
    user_id String,
    application_id Nullable(String),
    device_type LowCardinality(String),
    os LowCardinality(Nullable(String)),
    app_version LowCardinality(String),
    client_lib LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city LowCardinality(String),
    destination FixedString(2),
    drop_step LowCardinality(String),
    channel LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), drop_step, user_id, id)
SETTINGS index_granularity = 8192;

-- No CREATE MATERIALIZED VIEW in this spec — see justification.md
-- "Materialized view decision" for why none is proposed.
