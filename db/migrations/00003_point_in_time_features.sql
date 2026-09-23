-- +goose Up
-- +goose StatementBegin

-- Migration to fix data integrity issues.  ufc_master remains the raw/source
-- table; this table contains only features that are rebuilt directly from
-- raw fight data for accurate, point-in-time fighter stats
CREATE TABLE IF NOT EXISTS fight_features (
    "FightTag" TEXT PRIMARY KEY,
    event_date DATE NOT NULL,
    event_key TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    raw_detail_complete BOOLEAN NOT NULL DEFAULT FALSE,
    eligible BOOLEAN NOT NULL DEFAULT FALSE,
    categorical_outcome INTEGER,
    winner_number INTEGER,
    "RedFighter" TEXT NOT NULL,
    "BlueFighter" TEXT NOT NULL,
    "Winner" TEXT,
    "Finish" TEXT,
    "RedWinPct" DOUBLE PRECISION,
    "BlueWinPct" DOUBLE PRECISION,
    "WinPctDif" DOUBLE PRECISION,
    "RedKoPct" DOUBLE PRECISION,
    "BlueKoPct" DOUBLE PRECISION,
    "KoPctDif" DOUBLE PRECISION,
    "RedSubPct" DOUBLE PRECISION,
    "BlueSubPct" DOUBLE PRECISION,
    "SubPctDif" DOUBLE PRECISION,
    "RedDecPct" DOUBLE PRECISION,
    "BlueDecPct" DOUBLE PRECISION,
    "DecPctDif" DOUBLE PRECISION,
    "RedLossesByKO" DOUBLE PRECISION,
    "BlueLossesByKO" DOUBLE PRECISION,
    "LossesByKODif" DOUBLE PRECISION,
    "RedLossesBySub" DOUBLE PRECISION,
    "BlueLossesBySub" DOUBLE PRECISION,
    "LossesBySubDif" DOUBLE PRECISION,
    "RedLossesByDec" DOUBLE PRECISION,
    "BlueLossesByDec" DOUBLE PRECISION,
    "LossesByDecDif" DOUBLE PRECISION,
    "RedWeightLbs" DOUBLE PRECISION,
    "HeightDif" DOUBLE PRECISION,
    "ReachDif" DOUBLE PRECISION,
    "AgeDif" DOUBLE PRECISION,
    "RedAge" DOUBLE PRECISION,
    "BlueAge" DOUBLE PRECISION,
    "SigStrDif" DOUBLE PRECISION,
    "StrPctDif" DOUBLE PRECISION,
    "TDDif" DOUBLE PRECISION,
    "SubAttDif" DOUBLE PRECISION,
    "RedAvgSigStrLanded" DOUBLE PRECISION,
    "BlueAvgSigStrLanded" DOUBLE PRECISION,
    "RedAvgTDLanded" DOUBLE PRECISION,
    "BlueAvgTDLanded" DOUBLE PRECISION,
    "RedAvgSigStrPct" DOUBLE PRECISION,
    "BlueAvgSigStrPct" DOUBLE PRECISION,
    "RedAvgSubAtt" DOUBLE PRECISION,
    "BlueAvgSubAtt" DOUBLE PRECISION,
    "SigStrAbsorbedDif" DOUBLE PRECISION,
    "RedSigStrAbsorbed" DOUBLE PRECISION,
    "BlueSigStrAbsorbed" DOUBLE PRECISION,
    "AvgRoundsDif" DOUBLE PRECISION,
    "RedAvgRounds" DOUBLE PRECISION,
    "BlueAvgRounds" DOUBLE PRECISION,
    "EloDif" DOUBLE PRECISION,
    "OpponentEloDif" DOUBLE PRECISION,
    "RedElo" DOUBLE PRECISION,
    "BlueElo" DOUBLE PRECISION,
    "WinStreakDif" DOUBLE PRECISION,
    "RedCurrentWinStreak" DOUBLE PRECISION,
    "BlueCurrentWinStreak" DOUBLE PRECISION,
    "RedFinishL5" DOUBLE PRECISION,
    "BlueFinishL5" DOUBLE PRECISION,
    "FinishL5Dif" DOUBLE PRECISION,
    "FinishPctDif" DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS fight_features_event_date_idx
    ON fight_features (event_date);
CREATE INDEX IF NOT EXISTS fight_features_version_idx
    ON fight_features (feature_version);

-- The live database already contains these detailed columns from the deployed
-- match-detail scraper.  Keep the migration idempotent for clean databases.
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "RedMatchSigStrAttempted" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "BlueMatchSigStrAttempted" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "RedMatchTotalStr" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "BlueMatchTotalStr" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "RedMatchTotalStrAttempted" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "BlueMatchTotalStrAttempted" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "RedMatchTDAttempted" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "BlueMatchTDAttempted" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "RedMatchKD" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "BlueMatchKD" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "RedMatchControlTime" DOUBLE PRECISION;
ALTER TABLE ufc_master ADD COLUMN IF NOT EXISTS "BlueMatchControlTime" DOUBLE PRECISION;
ALTER TABLE fighters ADD COLUMN IF NOT EXISTS "FeatureVersion" TEXT;
ALTER TABLE fighters ADD COLUMN IF NOT EXISTS "StateAsOfDate" DATE;

-- A small audit record makes the active feature contract explicit in Postgres.
CREATE TABLE IF NOT EXISTS feature_contract (
    id TEXT PRIMARY KEY,
    feature_version TEXT NOT NULL,
    source_table TEXT NOT NULL,
    description TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO feature_contract (id, feature_version, source_table, description)
VALUES (
    'training',
    'pit-v1',
    'fight_features',
    'Pre-event fighter state reconstructed from raw UFCStats bout results and detailed bout totals'
)
ON CONFLICT (id) DO UPDATE SET
    feature_version = EXCLUDED.feature_version,
    source_table = EXCLUDED.source_table,
    description = EXCLUDED.description,
    updated_at = now();

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS feature_contract;
DROP TABLE IF EXISTS fight_features;
-- +goose StatementEnd
