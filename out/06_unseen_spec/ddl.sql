-- Spec 06 (sealed, unseen) — Promo / Coupon at Checkout
-- 6 events, all new occurrences of their own grain (one row per user per event,
-- per profile.md's 100%-unique user_id counts) -> CREATE TABLE for every event.
-- No ALTER statements: despite pay_now_clicked/purchase_completed already
-- carrying coupon_applied/coupon_name/discount_amount columns, this spec's
-- events are their own client-side moments (field render, code submit,
-- validation result, discount render, checkout proceed), not new attributes
-- landing on an existing row at an existing event's moment. See
-- justification.md "CREATE vs ALTER call" for the full reasoning and the
-- spec 05 (forex) precedent this follows.

CREATE TABLE IF NOT EXISTS clickathon.coupon_field_shown
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
    cart_value Float64,
    currency FixedString(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), device_type, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.coupon_entered
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
    cart_value Float64,
    currency FixedString(3),
    coupon_code LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), coupon_code, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.coupon_applied
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
    cart_value Float64,
    currency FixedString(3),
    coupon_code LowCardinality(String),
    discount_type LowCardinality(String),
    discount_amount Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), coupon_code, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.coupon_rejected
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
    cart_value Float64,
    currency FixedString(3),
    coupon_code LowCardinality(String),
    reject_reason LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), reject_reason, user_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.discount_shown
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
    cart_value Float64,
    currency FixedString(3),
    coupon_code LowCardinality(String),
    discount_amount Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), coupon_code, user_id, id)
SETTINGS index_granularity = 8192;

-- coupon_code is meaningfully NULL here (no-coupon baseline checkout, per
-- spec.md and profile.md's 62.9% null rate) and is this table's single most
-- important filter column (PM's conversion-lift question splits on exactly
-- this), so it leads ORDER BY; allow_nullable_key is required for that.
CREATE TABLE IF NOT EXISTS clickathon.checkout_with_coupon
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
    cart_value Float64,
    currency FixedString(3),
    coupon_code LowCardinality(Nullable(String)),
    discount_amount Float64,
    final_value Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), coupon_code, user_id, id)
SETTINGS index_granularity = 8192, allow_nullable_key = 1;
