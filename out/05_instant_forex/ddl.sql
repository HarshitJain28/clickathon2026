-- =====================================================================
-- Spec 05 — Instant Forex Add-on
-- =====================================================================
-- Grain call (see justification.md for full reasoning):
--   forex_offer_shown, currency_selected, amount_entered,
--   forex_added_to_cart  -> each is a new event with its own grain
--                            (own row, own moment) -> CREATE TABLE
--   forex_purchased      -> fires at the SAME moment as
--                            purchase_completed ("pays for it alongside
--                            the visa") -> ALTER TABLE purchase_completed
--                            ADD COLUMN (mirrors the existing
--                            insurance_added/insurance_amount add-on
--                            pattern), per purchase_completed.md's
--                            explicit instruction to instrument forex
--                            "consistently with [insurance/plan tiers]".
-- =====================================================================

-- ---------------------------------------------------------------------
-- CREATE TABLE forex_offer_shown
-- Source event: forex_offer_shown (n=2900 in profile.md)
-- ---------------------------------------------------------------------
CREATE TABLE forex_offer_shown
(
    id                          UUID,
    timestamp                   DateTime,
    user_id                     FixedString(28),
    application_id              Nullable(FixedString(36)), -- normalized on ingest, see D2 below
    app_session_id              Nullable(String),
    device                      Nullable(String),
    device_type                 LowCardinality(Nullable(String)),
    os                          LowCardinality(Nullable(String)),
    app_version                 LowCardinality(Nullable(String)),
    client_lib                  LowCardinality(Nullable(String)),
    geoip_country_code          LowCardinality(Nullable(String)),
    geoip_subdivision_1_code    Nullable(String),
    city                        LowCardinality(Nullable(String)),
    client_ip                   Nullable(String),
    latitude                    Nullable(Float64),
    longitude                   Nullable(Float64),
    locale                      Nullable(String),
    language                    Nullable(String),
    funnel_type                 Nullable(String),
    co_travelers                Nullable(UInt8),
    is_guest                    Nullable(UInt8),
    is_referral                 Nullable(UInt8),
    is_enterprise                Nullable(UInt8),
    gclid                       Nullable(String),
    fbclid                      Nullable(String),
    gad_source                  Nullable(String),
    citizenship                 Nullable(String),
    destination                 FixedString(2),
    is_back_filled               Nullable(UInt8),
    duplicate_id                Nullable(String),
    -- event-specific
    from_currency                FixedString(3),
    to_currency                  FixedString(3),
    fx_rate                      Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (destination, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ---------------------------------------------------------------------
-- CREATE TABLE currency_selected
-- Source event: currency_selected (n=1033 in profile.md)
-- ---------------------------------------------------------------------
CREATE TABLE currency_selected
(
    id                          UUID,
    timestamp                   DateTime,
    user_id                     FixedString(28),
    application_id              Nullable(FixedString(36)),
    app_session_id              Nullable(String),
    device                      Nullable(String),
    device_type                 LowCardinality(Nullable(String)),
    os                          LowCardinality(Nullable(String)),
    app_version                 LowCardinality(Nullable(String)),
    client_lib                  LowCardinality(Nullable(String)),
    geoip_country_code          LowCardinality(Nullable(String)),
    geoip_subdivision_1_code    Nullable(String),
    city                        LowCardinality(Nullable(String)),
    client_ip                   Nullable(String),
    latitude                    Nullable(Float64),
    longitude                   Nullable(Float64),
    locale                      Nullable(String),
    language                    Nullable(String),
    funnel_type                 Nullable(String),
    co_travelers                Nullable(UInt8),
    is_guest                    Nullable(UInt8),
    is_referral                 Nullable(UInt8),
    is_enterprise                Nullable(UInt8),
    gclid                       Nullable(String),
    fbclid                      Nullable(String),
    gad_source                  Nullable(String),
    citizenship                 Nullable(String),
    destination                 FixedString(2),
    is_back_filled               Nullable(UInt8),
    duplicate_id                Nullable(String),
    -- event-specific
    from_currency                FixedString(3),
    to_currency                  FixedString(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (destination, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ---------------------------------------------------------------------
-- CREATE TABLE amount_entered
-- Source event: amount_entered (n=1033 in profile.md)
-- ---------------------------------------------------------------------
CREATE TABLE amount_entered
(
    id                          UUID,
    timestamp                   DateTime,
    user_id                     FixedString(28),
    application_id              Nullable(FixedString(36)),
    app_session_id              Nullable(String),
    device                      Nullable(String),
    device_type                 LowCardinality(Nullable(String)),
    os                          LowCardinality(Nullable(String)),
    app_version                 LowCardinality(Nullable(String)),
    client_lib                  LowCardinality(Nullable(String)),
    geoip_country_code          LowCardinality(Nullable(String)),
    geoip_subdivision_1_code    Nullable(String),
    city                        LowCardinality(Nullable(String)),
    client_ip                   Nullable(String),
    latitude                    Nullable(Float64),
    longitude                   Nullable(Float64),
    locale                      Nullable(String),
    language                    Nullable(String),
    funnel_type                 Nullable(String),
    co_travelers                Nullable(UInt8),
    is_guest                    Nullable(UInt8),
    is_referral                 Nullable(UInt8),
    is_enterprise                Nullable(UInt8),
    gclid                       Nullable(String),
    fbclid                      Nullable(String),
    gad_source                  Nullable(String),
    citizenship                 Nullable(String),
    destination                 FixedString(2),
    is_back_filled               Nullable(UInt8),
    duplicate_id                Nullable(String),
    -- event-specific
    from_currency                FixedString(3),
    to_currency                  FixedString(3),
    amount                       UInt16
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (destination, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ---------------------------------------------------------------------
-- CREATE TABLE forex_added_to_cart
-- Source event: forex_added_to_cart (n=725 in profile.md)
-- ---------------------------------------------------------------------
CREATE TABLE forex_added_to_cart
(
    id                          UUID,
    timestamp                   DateTime,
    user_id                     FixedString(28),
    application_id              Nullable(FixedString(36)),
    app_session_id              Nullable(String),
    device                      Nullable(String),
    device_type                 LowCardinality(Nullable(String)),
    os                          LowCardinality(Nullable(String)),
    app_version                 LowCardinality(Nullable(String)),
    client_lib                  LowCardinality(Nullable(String)),
    geoip_country_code          LowCardinality(Nullable(String)),
    geoip_subdivision_1_code    Nullable(String),
    city                        LowCardinality(Nullable(String)),
    client_ip                   Nullable(String),
    latitude                    Nullable(Float64),
    longitude                   Nullable(Float64),
    locale                      Nullable(String),
    language                    Nullable(String),
    funnel_type                 Nullable(String),
    co_travelers                Nullable(UInt8),
    is_guest                    Nullable(UInt8),
    is_referral                 Nullable(UInt8),
    is_enterprise                Nullable(UInt8),
    gclid                       Nullable(String),
    fbclid                      Nullable(String),
    gad_source                  Nullable(String),
    citizenship                 Nullable(String),
    destination                 FixedString(2),
    is_back_filled               Nullable(UInt8),
    duplicate_id                Nullable(String),
    -- event-specific
    from_currency                FixedString(3),
    to_currency                  FixedString(3),
    amount                       UInt16,
    addon_value_inr              Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (destination, toDate(timestamp), user_id, id)
SETTINGS index_granularity = 8192;

-- ---------------------------------------------------------------------
-- ALTER TABLE purchase_completed
-- Source event: forex_purchased (n=546 in profile.md)
-- Grain: same moment as purchase_completed's own row (payment success);
-- add-on columns mirror insurance_added/insurance_amount naming and
-- nullability so they don't stick out as a foreign style on this
-- otherwise-consistent legacy table. Prefixed forex_* to avoid colliding
-- with the existing currency/value columns (D9-style collision risk),
-- which describe the visa payment, not the forex add-on.
-- ---------------------------------------------------------------------
ALTER TABLE purchase_completed
    ADD COLUMN forex_added            Nullable(UInt8),
    ADD COLUMN forex_from_currency    Nullable(String),
    ADD COLUMN forex_to_currency      Nullable(String),
    ADD COLUMN forex_amount           Nullable(Float64),
    ADD COLUMN forex_addon_value_inr  Nullable(Float64);

-- No materialized view is proposed for this spec — see justification.md
-- ("Materialized view decision") for why.
