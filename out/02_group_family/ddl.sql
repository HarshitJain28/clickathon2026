-- ============================================================================
-- Spec 02 — Group / Family Applications
-- Four new raw-event tables (own grain each): group_started, traveller_added,
-- traveller_removed, group_submitted. See justification.md for the CREATE vs
-- ALTER analysis, column-type reasoning, ORDER BY reasoning, and the D2
-- application_id normalization / overlap-check requirement.
--
-- application_id is ingested pre-normalized from the spec's 32-char
-- unhyphenated-hex form to the live DB's 36-char hyphenated UUID form
-- (known_issues.md D2):
--   concat(substring(raw_id,1,8),'-',substring(raw_id,9,4),'-',substring(raw_id,13,4),
--          '-',substring(raw_id,17,4),'-',substring(raw_id,21,12)) AS application_id
-- ============================================================================

-- ----------------------------------------------------------------------------
-- group_started — group flow begins; creates group_id for an existing application
-- ----------------------------------------------------------------------------
CREATE TABLE group_started
(
    id                  UUID,
    timestamp           DateTime,
    user_id             FixedString(28),
    application_id      FixedString(36),
    group_id            String,
    group_size          UInt8,
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
ORDER BY (group_size, destination, toDate(timestamp), group_id, id)
SETTINGS index_granularity = 8192;

-- ----------------------------------------------------------------------------
-- traveller_added — a co-traveller is added to an in-progress group
-- ----------------------------------------------------------------------------
CREATE TABLE traveller_added
(
    id                  UUID,
    timestamp           DateTime,
    user_id             FixedString(28),
    application_id      FixedString(36),
    group_id            String,
    group_size          UInt8,
    app_version         LowCardinality(String),
    city                LowCardinality(String),
    client_lib          LowCardinality(String),
    destination         FixedString(2),
    device_type         LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    os                  LowCardinality(Nullable(String)),
    traveller_index     UInt8,
    docs_complete       Bool,
    relation            LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (group_size, destination, toDate(timestamp), group_id, id)
SETTINGS index_granularity = 8192;

-- ----------------------------------------------------------------------------
-- traveller_removed — a co-traveller is dropped from an in-progress group
-- ----------------------------------------------------------------------------
CREATE TABLE traveller_removed
(
    id                  UUID,
    timestamp           DateTime,
    user_id             FixedString(28),
    application_id      FixedString(36),
    group_id            String,
    group_size          UInt8,
    app_version         LowCardinality(String),
    city                LowCardinality(String),
    client_lib          LowCardinality(String),
    destination         FixedString(2),
    device_type         LowCardinality(String),
    geoip_country_code  LowCardinality(String),
    os                  LowCardinality(Nullable(String)),
    traveller_index     UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (group_size, destination, toDate(timestamp), group_id, id)
SETTINGS index_granularity = 8192;

-- ----------------------------------------------------------------------------
-- group_submitted — the group is submitted together (conversion event for this flow)
-- ----------------------------------------------------------------------------
CREATE TABLE group_submitted
(
    id                    UUID,
    timestamp             DateTime,
    user_id               FixedString(28),
    application_id        FixedString(36),
    group_id              String,
    group_size            UInt8,
    app_version           LowCardinality(String),
    city                  LowCardinality(String),
    client_lib            LowCardinality(String),
    destination           FixedString(2),
    device_type           LowCardinality(String),
    geoip_country_code    LowCardinality(String),
    os                    LowCardinality(Nullable(String)),
    travellers_submitted  UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (group_size, destination, toDate(timestamp), group_id, id)
SETTINGS index_granularity = 8192;

-- No ALTER TABLE statements: none of this spec's four events share the grain
-- (moment + row identity) of any existing table's event. See justification.md
-- "CREATE vs ALTER call".

-- No MATERIALIZED VIEW: raw event volume is tiny (max 3,495 rows in
-- traveller_added, 5,453 total across all four tables vs. millions in the
-- existing 8 tables) — a full scan per dashboard query is cheap, and every
-- PM question needs row-level detail (per-traveller docs_complete, per-group
-- add/remove sequencing) that a pre-aggregate would discard. See
-- justification.md "Materialized view decision".
