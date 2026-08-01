-- =====================================================================
-- Spec 01 — Express Checkout
-- Five new events, each its own row/grain (own timestamp, own moment in
-- the express flow) — none shares the grain of an existing table's event,
-- so all five are CREATE TABLE, not ALTER. See justification.md for the
-- per-event CREATE-vs-ALTER call (including why pay_now_clicked /
-- purchase_completed were NOT altered despite the pay_now_clicked.md
-- context page name-checking this spec).
--
-- Column style deliberately upgrades the 8-table baseline (plain
-- String/Nullable(String)) to LowCardinality/FixedString/NOT NULL+DEFAULT
-- where the profiler evidence supports it — see justification.md for the
-- per-column reasoning and the specific skill rules cited.
--
-- MANDATORY pre-deployment step (known_issues.md D2): after ingest,
-- confirm application_id overlap with application_started before treating
-- any of these tables as joinable — query given in justification.md.
-- =====================================================================

-- ---------------------------------------------------------------------
-- express_checkout_shown — funnel entry: Express button rendered to an
-- eligible user. n=1650 in sample.
-- ---------------------------------------------------------------------
CREATE TABLE express_checkout_shown
(
    id                   UUID,
    timestamp            DateTime,
    user_id              String,
    application_id       String,                         -- normalized to 36-char hyphenated UUID at ingest, see D2
    device_type          LowCardinality(String),
    os                   LowCardinality(Nullable(String)),
    app_version          LowCardinality(String),
    client_lib           LowCardinality(String),
    geoip_country_code   LowCardinality(String),
    city                 LowCardinality(String),
    destination          FixedString(2),
    currency             FixedString(3),
    eligible             UInt8 DEFAULT 1,
    shown_amount         Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ---------------------------------------------------------------------
-- express_checkout_selected — user taps Express. n=1007 in sample.
-- ---------------------------------------------------------------------
CREATE TABLE express_checkout_selected
(
    id                   UUID,
    timestamp            DateTime,
    user_id              String,
    application_id       String,                         -- normalized to 36-char hyphenated UUID at ingest, see D2
    device_type          LowCardinality(String),
    os                   LowCardinality(Nullable(String)),
    app_version          LowCardinality(String),
    client_lib           LowCardinality(String),
    geoip_country_code   LowCardinality(String),
    city                 LowCardinality(String),
    destination          FixedString(2),
    saved_method_type    LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ---------------------------------------------------------------------
-- saved_method_used — the saved instrument is loaded. n=1007 in sample.
-- No event-specific fields beyond the envelope subset (profile shows
-- none) — do not invent any.
-- ---------------------------------------------------------------------
CREATE TABLE saved_method_used
(
    id                   UUID,
    timestamp            DateTime,
    user_id              String,
    application_id       String,                         -- normalized to 36-char hyphenated UUID at ingest, see D2
    device_type          LowCardinality(String),
    os                   LowCardinality(Nullable(String)),
    app_version          LowCardinality(String),
    client_lib           LowCardinality(String),
    geoip_country_code   LowCardinality(String),
    city                 LowCardinality(String),
    destination          FixedString(2)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ---------------------------------------------------------------------
-- otp_entered — OTP submitted. n=1007 in sample. This is the first
-- instrumentation able to test the pay_now_clicked -> purchase_completed
-- leak directly (see pay_now_clicked.md); it remains its own table
-- because its row count (1007) and moment (OTP submission) differ from
-- pay_now_clicked's (14,739, "Pay Now" tap) — see justification.md.
-- ---------------------------------------------------------------------
CREATE TABLE otp_entered
(
    id                   UUID,
    timestamp            DateTime,
    user_id              String,
    application_id       String,                         -- normalized to 36-char hyphenated UUID at ingest, see D2
    device_type          LowCardinality(String),
    os                   LowCardinality(Nullable(String)),
    app_version          LowCardinality(String),
    client_lib           LowCardinality(String),
    geoip_country_code   LowCardinality(String),
    city                 LowCardinality(String),
    destination          FixedString(2),
    otp_attempts         UInt8,
    otp_success          UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ---------------------------------------------------------------------
-- express_payment_confirmed — payment succeeds via Express. n=836 in
-- sample. Nested `payment` object flattened to payment_* columns,
-- consistent with the flat-column convention used throughout the
-- existing 8 tables (e.g. purchase_completed.value/currency).
-- ---------------------------------------------------------------------
CREATE TABLE express_payment_confirmed
(
    id                   UUID,
    timestamp            DateTime,
    user_id              String,
    application_id       String,                         -- normalized to 36-char hyphenated UUID at ingest, see D2
    device_type          LowCardinality(String),
    os                   LowCardinality(Nullable(String)),
    app_version          LowCardinality(String),
    client_lib           LowCardinality(String),
    geoip_country_code   LowCardinality(String),
    city                 LowCardinality(String),
    destination          FixedString(2),
    payment_amount       Float64,
    payment_currency     FixedString(3),
    payment_latency_ms   UInt16
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- No CREATE MATERIALIZED VIEW: none of the spec's questions warrant one.
-- See justification.md "Materialized view decision" for the full reasoning.
