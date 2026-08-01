-- =====================================================================
-- Spec 03 — Visa Status Sharing
-- All 5 events are new occurrences with no shared grain with any of the
-- 8 existing tables (no ALTERs). See justification.md for the CREATE-vs-
-- ALTER reasoning per event.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Event: share_clicked  (sharer taps share; full envelope; n=1,600)
-- ---------------------------------------------------------------------
CREATE TABLE share_clicked
(
    id                          UUID,
    timestamp                   DateTime,
    user_id                     FixedString(28),                 -- relationship.md: exactly 28 chars everywhere
    application_id              Nullable(String),                -- normalize 32-char spec hex -> 36-char hyphenated UUID on ingest (D2)
    app_session_id              Nullable(String),
    device                      Nullable(String),
    device_type                 LowCardinality(Nullable(String)), -- 4 values, ragged length (ios/android/Desktop/web-user-b2c)
    os                          LowCardinality(Nullable(String)), -- 4 values, 5.6% null in profile
    app_version                 LowCardinality(Nullable(String)), -- 3 values sampled; not a fixed-format code (see justification)
    client_lib                  LowCardinality(Nullable(String)), -- 2 values
    geoip_country_code          LowCardinality(Nullable(String)), -- envelope carries an "OTHER" (5-char) catch-all -> not FixedString
    geoip_subdivision_1_code    Nullable(String),
    city                        LowCardinality(Nullable(String)), -- 7 values, ragged length (Mumbai/Singapore/...)
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
    destination                 FixedString(2),                  -- 100% present, 27 known ISO-2 values, no catch-all (unlike geoip_country_code)
    is_back_filled               Nullable(UInt8),
    duplicate_id                Nullable(String),
    -- event-specific
    status_shared               LowCardinality(String),          -- 3 values, 100% present: submitted/processing/approved
    share_id                    FixedString(32)                  -- 32-char hex hash, 100% present, join key to recipient events
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (status_shared, toDate(timestamp), share_id, id);

-- ---------------------------------------------------------------------
-- Event: channel_selected  (sharer picks a channel; full envelope; n=1,144)
-- ---------------------------------------------------------------------
CREATE TABLE channel_selected
(
    id                          UUID,
    timestamp                   DateTime,
    user_id                     FixedString(28),
    application_id              Nullable(String),                -- normalize per D2
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
    channel                     LowCardinality(String),          -- 4 values, 100% present: whatsapp/copy_link/email/sms
    status_shared               LowCardinality(String),          -- 100% present in profile though not named in spec.md prose
    share_id                    FixedString(32)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (channel, toDate(timestamp), share_id, id);

-- ---------------------------------------------------------------------
-- Event: link_generated  (share link created; full envelope; n=1,144)
-- NOTE: field set and row count are identical to channel_selected (see
-- justification.md) -- kept as its own table anyway, per the "one table
-- per event" convention; not merged because nothing in spec.md/known_issues
-- authorizes collapsing two distinctly-named new events into one table.
-- ---------------------------------------------------------------------
CREATE TABLE link_generated
(
    id                          UUID,
    timestamp                   DateTime,
    user_id                     FixedString(28),
    application_id              Nullable(String),                -- normalize per D2
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
    channel                     LowCardinality(String),
    status_shared               LowCardinality(String),
    share_id                    FixedString(32)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (channel, toDate(timestamp), share_id, id);

-- ---------------------------------------------------------------------
-- Event: link_opened  (recipient opens the link; NO user_id — recipient
-- events are keyed by share_id only, per spec.md and relationship.md
-- "Entities the incoming specs will add"; n=2,310)
-- ---------------------------------------------------------------------
CREATE TABLE link_opened
(
    id                          UUID,
    timestamp                   DateTime,
    share_id                    FixedString(32),                 -- 39.9% unique here: recipients can reopen the same share_id
    channel                     LowCardinality(String),          -- 4 values, 100% present
    destination                 FixedString(2),                  -- 100% present, 14 of 27 known ISO-2 values sampled
    recipient_is_new_user       UInt8                             -- 100% present, 2 values (true/false); no nulls observed -> non-nullable flag
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (channel, toDate(timestamp), destination, share_id, id);

-- ---------------------------------------------------------------------
-- Event: recipient_cta_clicked  (recipient taps "start your own
-- application"; NO user_id, same recipient topology as link_opened;
-- n=305)
-- ---------------------------------------------------------------------
CREATE TABLE recipient_cta_clicked
(
    id                          UUID,
    timestamp                   DateTime,
    share_id                    FixedString(32),                 -- 86.2% unique: mostly one CTA click per share_id
    destination                 FixedString(2),                  -- 100% present
    cta                         LowCardinality(String)           -- distinct: 1 today (start_own_application); kept String-backed, not Enum (see justification)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (destination, toDate(timestamp), share_id, id);
