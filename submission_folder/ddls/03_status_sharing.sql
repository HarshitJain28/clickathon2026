-- Spec 03 — Visa Status Sharing
-- All 5 spec events (share_clicked, channel_selected, link_generated,
-- link_opened, recipient_cta_clicked) are new occurrences at their own
-- grain, introduced by a new entity (Share, keyed by share_id) that does
-- not already exist in any of the 17 deployed tables. No existing table's
-- event fires at the same moment as any of these five, so every statement
-- below is CREATE TABLE — no ALTER candidates were found. See
-- justification.md for the per-event reasoning.

-- ============================================================
-- Sharer-side events (full available envelope subset + share_id)
-- ============================================================

CREATE TABLE IF NOT EXISTS clickathon.share_clicked
(
    id UUID,
    timestamp DateTime,
    user_id String,
    share_id FixedString(32),
    application_id Nullable(String),
    app_version LowCardinality(String),
    city LowCardinality(String),
    client_lib LowCardinality(String),
    destination FixedString(2),
    device_type LowCardinality(String),
    geoip_country_code LowCardinality(String),
    os LowCardinality(Nullable(String)),
    status_shared LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), status_shared, user_id, id);

CREATE TABLE IF NOT EXISTS clickathon.channel_selected
(
    id UUID,
    timestamp DateTime,
    user_id String,
    share_id FixedString(32),
    application_id Nullable(String),
    app_version LowCardinality(String),
    channel LowCardinality(String),
    city LowCardinality(String),
    client_lib LowCardinality(String),
    destination FixedString(2),
    device_type LowCardinality(String),
    geoip_country_code LowCardinality(String),
    os LowCardinality(Nullable(String)),
    status_shared LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), channel, user_id, id);

CREATE TABLE IF NOT EXISTS clickathon.link_generated
(
    id UUID,
    timestamp DateTime,
    user_id String,
    share_id FixedString(32),
    application_id Nullable(String),
    app_version LowCardinality(String),
    channel LowCardinality(String),
    city LowCardinality(String),
    client_lib LowCardinality(String),
    destination FixedString(2),
    device_type LowCardinality(String),
    geoip_country_code LowCardinality(String),
    os LowCardinality(Nullable(String)),
    status_shared LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), channel, user_id, id);

-- ============================================================
-- Recipient-side events — NO user_id, NO envelope (per spec.md:
-- "recipient events... are keyed by share_id"; confirmed by profile.md,
-- which shows no envelope columns present on either table)
-- ============================================================

CREATE TABLE IF NOT EXISTS clickathon.link_opened
(
    id UUID,
    timestamp DateTime,
    share_id FixedString(32),
    channel LowCardinality(String),
    destination FixedString(2),
    recipient_is_new_user Bool
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), channel, share_id, id);

CREATE TABLE IF NOT EXISTS clickathon.recipient_cta_clicked
(
    id UUID,
    timestamp DateTime,
    share_id FixedString(32),
    destination FixedString(2),
    cta LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), destination, share_id, id);

-- No ALTER TABLE statements: no spec event shares grain with an existing
-- table (see justification.md "CREATE vs ALTER call").
-- No MATERIALIZED VIEW: data volume (6,503 rows total across 5 tables)
-- does not warrant pre-aggregation (see justification.md "Materialized
-- view decision").
