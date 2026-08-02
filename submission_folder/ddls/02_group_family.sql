-- Spec 02 — Group / Family Applications
-- All 4 events are new occurrences at their own grain (own row, own moment in
-- the group flow), none sharing a moment/grain with an existing table's event
-- or with spec 01's 5 Express Checkout tables (see justification.md
-- "CREATE vs ALTER call" per event).
-- => 4x CREATE TABLE, 0x ALTER TABLE, 0x MATERIALIZED VIEW.
--
-- Physical layout deliberately deviates from the 8 baseline tables per
-- known_issues.md D8: new tables must NOT lead ORDER BY with the random `id`
-- UUID. LowCardinality(String) used for tiny categoricals per the same entry.
--
-- application_id is typed Nullable(String) to match application_started's
-- join-key type (relationship.md "Application" + known_issues.md D2). D2 is
-- CRITICAL: this spec's raw application_id is confirmed 32-char unhyphenated
-- hex (e.g. group_submitted's "007b4af7f2f0a42e11cfc48e8d04f37a" in
-- profile.md), which will NOT join application_started's 36-char hyphenated
-- UUID as-is. The ingest pipeline MUST normalize (insert dashes at
-- 8-4-4-4-12) on write into every table below, and D2's mandatory
-- overlap-check query MUST be run against application_started before these
-- tables are declared join-ready (see justification.md "Risks / caveats").
--
-- group_id is typed FixedString(32): every sampled value across
-- group_started/group_submitted/traveller_removed's profile.md samples is
-- exactly 32 lowercase-hex characters (a raw, unhyphenated UUID-shaped
-- string), and group_id is a NEW entity's key that exists solely within
-- this spec's own 4 tables (it does not join application_started or any
-- existing table), so the column-policy exception for spec-local keys
-- applies — see justification.md "String-type decision".

CREATE TABLE IF NOT EXISTS clickathon.group_started
(
    id                  UUID,
    timestamp           DateTime,
    user_id             String,
    application_id      Nullable(String),
    device_type         LowCardinality(String),
    os                  LowCardinality(Nullable(String)),
    app_version         LowCardinality(String),
    client_lib          LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    city                LowCardinality(String),
    destination         LowCardinality(String),
    group_id            FixedString(32),
    group_size          UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), group_size, group_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.traveller_added
(
    id                  UUID,
    timestamp           DateTime,
    user_id             String,
    application_id      Nullable(String),
    device_type         LowCardinality(String),
    os                  LowCardinality(Nullable(String)),
    app_version         LowCardinality(String),
    client_lib          LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    city                LowCardinality(String),
    destination         LowCardinality(String),
    group_id            FixedString(32),
    group_size          UInt8,
    traveller_index     UInt8,
    relation            LowCardinality(String),
    docs_complete       Bool
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), group_size, group_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.traveller_removed
(
    id                  UUID,
    timestamp           DateTime,
    user_id             String,
    application_id      Nullable(String),
    device_type         LowCardinality(String),
    os                  LowCardinality(Nullable(String)),
    app_version         LowCardinality(String),
    client_lib          LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    city                LowCardinality(String),
    destination         LowCardinality(String),
    group_id            FixedString(32),
    group_size          UInt8,
    traveller_index     UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), group_size, group_id, id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS clickathon.group_submitted
(
    id                  UUID,
    timestamp           DateTime,
    user_id             String,
    application_id      Nullable(String),
    device_type         LowCardinality(String),
    os                  LowCardinality(Nullable(String)),
    app_version         LowCardinality(String),
    client_lib          LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    city                LowCardinality(String),
    destination         LowCardinality(String),
    group_id            FixedString(32),
    group_size          UInt8,
    travellers_submitted UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), group_size, group_id, id)
SETTINGS index_granularity = 8192;

-- No ALTER TABLE statements: no event in this spec shares a moment/grain with
-- an existing table's event (see justification.md "CREATE vs ALTER call").

-- No MATERIALIZED VIEW: all 4 source tables are O(1e2)-O(1e3) rows in the
-- profiled sample (70-3,495) — full scans, including the group_started ->
-- group_submitted completion-rate-by-group_size rollup the PM will ask for,
-- are already cheap; see justification.md "Materialized view decision".
