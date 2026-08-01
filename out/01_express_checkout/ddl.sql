-- Spec 01: Express Checkout
-- All 5 events are new occurrences at their own grain (own moment, own row) —
-- none of them share the grain of an existing table's event, so this spec is
-- CREATE TABLE only. No ALTER statements. See justification.md for the
-- per-event CREATE-vs-ALTER reasoning.
--
-- ⚠ MANDATORY pre-deployment step (known_issues.md D2): application_id in this
-- spec's raw events arrives as 32-char unhyphenated hex (confirmed in
-- profile.md's express_payment_confirmed sample), not the 36-char hyphenated
-- UUID the DB uses. The ingest pipeline MUST normalize to hyphenated form
-- before insert, e.g.:
--   concat(substring(raw_id,1,8),'-',substring(raw_id,9,4),'-',substring(raw_id,13,4),
--          '-',substring(raw_id,17,4),'-',substring(raw_id,21,12)) AS application_id
-- and the overlap_pct check against clickathon.application_started MUST be run
-- and documented before these tables are declared ready for join-based analysis.

-- ============================================================
-- express_checkout_shown — express eligible, button rendered
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.express_checkout_shown
(
    id                  UUID,
    timestamp           DateTime,
    user_id             String,                        -- join key: exact envelope type (String, not nullable)
    application_id      Nullable(String),               -- join key: exact envelope type; normalize per D2 before insert
    app_version         LowCardinality(String),
    city                LowCardinality(String),
    client_lib          LowCardinality(String),
    destination         FixedString(2),                 -- ISO-2 code, uniform length, no OTHER-style exception documented for this column
    device_type         LowCardinality(String),
    geoip_country_code  LowCardinality(String),          -- String, not FixedString: envelope documents an "OTHER" (5-char) exception value
    os                  LowCardinality(Nullable(String)),-- genuinely null ~6.8% here, consistent with envelope's stated 5.95% NULL
    currency            FixedString(3),                  -- ISO-4217 code, uniform 3-char length, no OTHER-style exception documented
    eligible             Bool,
    shown_amount        Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ============================================================
-- express_checkout_selected — user taps Express
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.express_checkout_selected
(
    id                  UUID,
    timestamp           DateTime,
    user_id             String,
    application_id      Nullable(String),
    app_version         LowCardinality(String),
    city                LowCardinality(String),
    client_lib          LowCardinality(String),
    destination         FixedString(2),
    device_type         LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    os                  LowCardinality(Nullable(String)),
    saved_method_type   LowCardinality(String)           -- card/upi/wallet today; set may grow (cf. pay_now_clicked.payment_method has 5 values) — not Enum
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ============================================================
-- saved_method_used — the saved instrument is loaded
-- No event-specific payload observed beyond the envelope subset.
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.saved_method_used
(
    id                  UUID,
    timestamp           DateTime,
    user_id             String,
    application_id      Nullable(String),
    app_version         LowCardinality(String),
    city                LowCardinality(String),
    client_lib          LowCardinality(String),
    destination         FixedString(2),
    device_type         LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    os                  LowCardinality(Nullable(String))
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ============================================================
-- otp_entered — OTP submitted
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.otp_entered
(
    id                  UUID,
    timestamp           DateTime,
    user_id             String,
    application_id      Nullable(String),
    app_version         LowCardinality(String),
    city                LowCardinality(String),
    client_lib          LowCardinality(String),
    destination         FixedString(2),
    device_type         LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    os                  LowCardinality(Nullable(String)),
    otp_attempts        UInt8,                            -- observed range [1,3]
    otp_success         Bool
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ============================================================
-- express_payment_confirmed — payment succeeds
-- Nested `payment` object flattened to payment_* columns.
-- ============================================================
CREATE TABLE IF NOT EXISTS clickathon.express_payment_confirmed
(
    id                  UUID,
    timestamp           DateTime,
    user_id             String,
    application_id      Nullable(String),
    app_version         LowCardinality(String),
    city                LowCardinality(String),
    client_lib          LowCardinality(String),
    destination         FixedString(2),
    device_type         LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    os                  LowCardinality(Nullable(String)),
    payment_amount      Float64,                          -- observed range [1509.0, 8997.0]
    payment_currency    FixedString(3),
    payment_latency_ms  UInt16                             -- observed range [607, 3999]
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (device_type, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;
