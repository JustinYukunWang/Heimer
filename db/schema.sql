-- Run this in the Supabase SQL editor to initialize the database.

CREATE TABLE IF NOT EXISTS players (
    puuid    TEXT PRIMARY KEY,
    rank     TEXT NOT NULL,
    lp       INTEGER,
    region   TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS matches (
    match_id        TEXT PRIMARY KEY,
    patch           TEXT,
    duration        INTEGER,   -- seconds
    queue           TEXT,
    game_timestamp  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS participants (
    id        BIGSERIAL PRIMARY KEY,
    match_id  TEXT    NOT NULL REFERENCES matches(match_id),
    puuid     TEXT    NOT NULL REFERENCES players(puuid),
    champion  TEXT,
    role      TEXT,
    win       BOOLEAN,
    UNIQUE (match_id, puuid)
);

CREATE TABLE IF NOT EXISTS timeline_snapshots (
    id               BIGSERIAL PRIMARY KEY,
    match_id         TEXT    NOT NULL REFERENCES matches(match_id),
    puuid            TEXT    NOT NULL REFERENCES players(puuid),
    timestamp_minute INTEGER NOT NULL,  -- 5, 10, 15, 20, 25, 30
    cs               INTEGER,
    gold             INTEGER,
    xp               INTEGER,
    level            INTEGER,
    kills            INTEGER,
    deaths           INTEGER,
    assists          INTEGER,
    vision_score     INTEGER,
    items            JSONB,
    UNIQUE (match_id, puuid, timestamp_minute)
);

-- Persistent item lookup table — never cleared between pipeline runs.
-- Keyed by (item_id, patch) so data stays correct across game updates.
-- Populated automatically from DDragon whenever a new patch is encountered.
CREATE TABLE IF NOT EXISTS item_catalog (
    item_id     INTEGER NOT NULL,
    patch       TEXT    NOT NULL,
    name        TEXT,
    description TEXT,
    tags        JSONB,
    stats       JSONB,
    PRIMARY KEY (item_id, patch)
);
