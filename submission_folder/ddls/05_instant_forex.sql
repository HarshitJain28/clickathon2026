-- Spec 05: Instant Forex Add-on
-- All 5 events are new occurrences at their own grain (own moment, own row) —
-- no ALTER candidates identified. See justification.md "CREATE vs ALTER call".
-- Each substitutes `destination` as its leading sort-key discriminator,
-- following D8's fix template and this spec's own PM questions
-- ("by destination", "which destinations attach best").

CREATE TABLE IF NOT EXISTS clickathon.forex_offer_shown
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
    from_currency FixedString(3),
    to_currency FixedString(3),
    fx_rate Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), destination, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.currency_selected
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
    from_currency FixedString(3),
    to_currency FixedString(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), destination, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.amount_entered
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
    from_currency FixedString(3),
    to_currency FixedString(3),
    amount UInt16
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), destination, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.forex_added_to_cart
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
    from_currency FixedString(3),
    to_currency FixedString(3),
    amount UInt16,
    addon_value_inr Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), destination, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.forex_purchased
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
    from_currency FixedString(3),
    to_currency FixedString(3),
    amount UInt16,
    addon_value_inr Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), destination, user_id, id)
SETTINGS index_granularity = 8192;

-- No ALTER TABLE statements: none of this spec's 5 events share the grain of
-- an existing baseline/spec table (see justification.md).
-- No MATERIALIZED VIEW: row volumes (546-2,900 rows/event) are too small to
-- justify pre-aggregation — see justification.md "Materialized view decision".
