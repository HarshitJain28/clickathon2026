-- Spec 01 — Express Checkout
-- All 5 events are new occurrences at their own grain (own row, own moment in
-- the express-checkout flow), none sharing a moment/grain with an existing
-- table's event (see justification.md "CREATE vs ALTER call" per event).
-- => 5x CREATE TABLE, 0x ALTER TABLE.
--
-- Physical layout deliberately deviates from the 8 existing tables per
-- known_issues.md D8: new tables must NOT lead ORDER BY with the random `id`
-- UUID, and must use LowCardinality(String) for tiny categoricals.
--
-- application_id is typed Nullable(String) to match application_started's
-- join-key type (see relationship.md "Application" + known_issues.md D2).
-- D2 is CRITICAL: the raw spec NDJSON carries application_id as a 32-char
-- unhyphenated hex string (confirmed in profile.md's express_payment_confirmed
-- sample), which will NOT join application_started's 36-char hyphenated UUID
-- as-is. The ingest pipeline MUST normalize (insert dashes at 8-4-4-4-12) on
-- write into every table below, and the D2 overlap-check query MUST be run
-- against application_started before these tables are declared join-ready.

CREATE TABLE IF NOT EXISTS clickathon.express_checkout_shown
(
    id                UUID,
    timestamp         DateTime,
    user_id           String,
    application_id    Nullable(String),
    device_type       LowCardinality(String),
    os                LowCardinality(Nullable(String)),
    app_version       LowCardinality(String),
    client_lib        LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city              LowCardinality(String),
    destination       LowCardinality(String),
    shown_amount      Float64,
    currency          LowCardinality(String),
    eligible          Bool
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), device_type, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.express_checkout_selected
(
    id                UUID,
    timestamp         DateTime,
    user_id           String,
    application_id    Nullable(String),
    device_type       LowCardinality(String),
    os                LowCardinality(Nullable(String)),
    app_version       LowCardinality(String),
    client_lib        LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city              LowCardinality(String),
    destination       LowCardinality(String),
    saved_method_type LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), device_type, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.saved_method_used
(
    id                UUID,
    timestamp         DateTime,
    user_id           String,
    application_id    Nullable(String),
    device_type       LowCardinality(String),
    os                LowCardinality(Nullable(String)),
    app_version       LowCardinality(String),
    client_lib        LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city              LowCardinality(String),
    destination       LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), device_type, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.otp_entered
(
    id                UUID,
    timestamp         DateTime,
    user_id           String,
    application_id    Nullable(String),
    device_type       LowCardinality(String),
    os                LowCardinality(Nullable(String)),
    app_version       LowCardinality(String),
    client_lib        LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city              LowCardinality(String),
    destination       LowCardinality(String),
    otp_attempts      UInt8,
    otp_success       Bool
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), device_type, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.express_payment_confirmed
(
    id                UUID,
    timestamp         DateTime,
    user_id           String,
    application_id    Nullable(String),
    device_type       LowCardinality(String),
    os                LowCardinality(Nullable(String)),
    app_version       LowCardinality(String),
    client_lib        LowCardinality(String),
    geoip_country_code LowCardinality(String),
    city              LowCardinality(String),
    destination       LowCardinality(String),
    payment_amount    Float64,
    payment_currency  LowCardinality(String),
    payment_latency_ms UInt16
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), device_type, user_id, id)
SETTINGS index_granularity = 8192;

-- No ALTER TABLE statements: no event in this spec shares a moment/grain with
-- an existing table's event (see justification.md).

-- No MATERIALIZED VIEW: every source table here is O(1e3) rows in the profiled
-- sample (836-1650) — full scans are already cheap; see justification.md
-- "Materialized view decision".
