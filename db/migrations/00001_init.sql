-- +goose Up
-- +goose StatementBegin

-- Per-fighter aggregated stats. Read on the hot inference path by the Go
-- backend (keyed by fighter_tag); written by the scraper/cleaning pipeline.
-- Column names mirror the Firestore document schema (and the Go Fighter
-- struct) exactly, so identifiers are quoted to preserve their casing.
CREATE TABLE IF NOT EXISTS fighters (
    "fighter_tag"       TEXT PRIMARY KEY,
    "Wins"              INTEGER,
    "WinsByKO"          INTEGER,
    "WinsBySubmission"  INTEGER,
    "WinsByDecision"    INTEGER,
    "Losses"            INTEGER,
    "HeightCms"         DOUBLE PRECISION,
    "ReachCms"          DOUBLE PRECISION,
    "AvgSigStrLanded"   DOUBLE PRECISION,
    "AvgTDLanded"       DOUBLE PRECISION,
    "AvgSigStrPct"      DOUBLE PRECISION,
    "AvgSubAtt"         DOUBLE PRECISION,
    "Stance"            TEXT,
    "WeightLbs"         INTEGER,
    "Age"               INTEGER,
    "KoPct"             DOUBLE PRECISION,
    "SubPct"            DOUBLE PRECISION,
    "DecPct"            DOUBLE PRECISION,
    "AvgRounds"         DOUBLE PRECISION,
    "Elo"               DOUBLE PRECISION,
    "OpponentElo"       DOUBLE PRECISION,
    "SigStrAbsorbed"    DOUBLE PRECISION,
    "CurrentWinStreak"  INTEGER,
    "FinishL5"          DOUBLE PRECISION,
    "LossesByKO"        INTEGER,
    "LossesBySub"       INTEGER,
    "LossesByDec"       INTEGER,
    "WinPct"            DOUBLE PRECISION,
    "TotalRoundsFought" INTEGER,
    "WeightClass"       TEXT,
    "Gender"            TEXT
);

-- Historical per-fight rows: the training set consumed wholesale by the
-- retraining pipeline (SELECT * -> DataFrame). Schema mirrors the cleaned
-- feature CSV / Firestore ufc-master collection; keyed by FightTag.
CREATE TABLE IF NOT EXISTS ufc_master (
    "RedFighter" TEXT,
    "BlueFighter" TEXT,
    "RedOdds" DOUBLE PRECISION,
    "BlueOdds" DOUBLE PRECISION,
    "RedExpectedValue" DOUBLE PRECISION,
    "BlueExpectedValue" DOUBLE PRECISION,
    "Date" TEXT,
    "Location" TEXT,
    "Country" TEXT,
    "Winner" TEXT,
    "TitleBout" BOOLEAN,
    "WeightClass" TEXT,
    "Gender" TEXT,
    "NumberOfRounds" BIGINT,
    "BlueCurrentLoseStreak" BIGINT,
    "BlueCurrentWinStreak" BIGINT,
    "BlueDraws" BIGINT,
    "BlueAvgSigStrLanded" DOUBLE PRECISION,
    "BlueAvgSigStrPct" DOUBLE PRECISION,
    "BlueAvgSubAtt" DOUBLE PRECISION,
    "BlueAvgTDLanded" DOUBLE PRECISION,
    "BlueAvgTDPct" DOUBLE PRECISION,
    "BlueLongestWinStreak" BIGINT,
    "BlueLosses" BIGINT,
    "BlueTotalRoundsFought" BIGINT,
    "BlueTotalTitleBouts" BIGINT,
    "BlueWinsByDecisionMajority" BIGINT,
    "BlueWinsByDecisionSplit" BIGINT,
    "BlueWinsByDecisionUnanimous" BIGINT,
    "BlueWinsByKO" BIGINT,
    "BlueWinsBySubmission" BIGINT,
    "BlueWinsByTKODoctorStoppage" BIGINT,
    "BlueWins" BIGINT,
    "BlueStance" TEXT,
    "BlueHeightCms" DOUBLE PRECISION,
    "BlueReachCms" DOUBLE PRECISION,
    "BlueWeightLbs" BIGINT,
    "RedCurrentLoseStreak" BIGINT,
    "RedCurrentWinStreak" BIGINT,
    "RedDraws" BIGINT,
    "RedAvgSigStrLanded" DOUBLE PRECISION,
    "RedAvgSigStrPct" DOUBLE PRECISION,
    "RedAvgSubAtt" DOUBLE PRECISION,
    "RedAvgTDLanded" DOUBLE PRECISION,
    "RedAvgTDPct" DOUBLE PRECISION,
    "RedLongestWinStreak" BIGINT,
    "RedLosses" BIGINT,
    "RedTotalRoundsFought" BIGINT,
    "RedTotalTitleBouts" BIGINT,
    "RedWinsByDecisionMajority" BIGINT,
    "RedWinsByDecisionSplit" BIGINT,
    "RedWinsByDecisionUnanimous" BIGINT,
    "RedWinsByKO" BIGINT,
    "RedWinsBySubmission" BIGINT,
    "RedWinsByTKODoctorStoppage" BIGINT,
    "RedWins" BIGINT,
    "RedStance" TEXT,
    "RedHeightCms" DOUBLE PRECISION,
    "RedReachCms" DOUBLE PRECISION,
    "RedWeightLbs" BIGINT,
    "RedAge" BIGINT,
    "BlueAge" BIGINT,
    "LoseStreakDif" BIGINT,
    "WinStreakDif" BIGINT,
    "LongestWinStreakDif" BIGINT,
    "WinDif" BIGINT,
    "LossDif" BIGINT,
    "TotalRoundDif" BIGINT,
    "TotalTitleBoutDif" BIGINT,
    "KODif" BIGINT,
    "SubDif" BIGINT,
    "HeightDif" DOUBLE PRECISION,
    "ReachDif" DOUBLE PRECISION,
    "AgeDif" BIGINT,
    "SigStrDif" DOUBLE PRECISION,
    "AvgSubAttDif" DOUBLE PRECISION,
    "AvgTDDif" DOUBLE PRECISION,
    "EmptyArena" DOUBLE PRECISION,
    "BMatchWCRank" DOUBLE PRECISION,
    "RMatchWCRank" DOUBLE PRECISION,
    "RWFlyweightRank" DOUBLE PRECISION,
    "RWFeatherweightRank" DOUBLE PRECISION,
    "RWStrawweightRank" DOUBLE PRECISION,
    "RWBantamweightRank" DOUBLE PRECISION,
    "RHeavyweightRank" DOUBLE PRECISION,
    "RLightHeavyweightRank" DOUBLE PRECISION,
    "RMiddleweightRank" DOUBLE PRECISION,
    "RWelterweightRank" DOUBLE PRECISION,
    "RLightweightRank" DOUBLE PRECISION,
    "RFeatherweightRank" DOUBLE PRECISION,
    "RBantamweightRank" DOUBLE PRECISION,
    "RFlyweightRank" DOUBLE PRECISION,
    "RPFPRank" DOUBLE PRECISION,
    "BWFlyweightRank" DOUBLE PRECISION,
    "BWFeatherweightRank" DOUBLE PRECISION,
    "BWStrawweightRank" DOUBLE PRECISION,
    "BWBantamweightRank" DOUBLE PRECISION,
    "BHeavyweightRank" DOUBLE PRECISION,
    "BLightHeavyweightRank" DOUBLE PRECISION,
    "BMiddleweightRank" DOUBLE PRECISION,
    "BWelterweightRank" DOUBLE PRECISION,
    "BLightweightRank" DOUBLE PRECISION,
    "BFeatherweightRank" DOUBLE PRECISION,
    "BBantamweightRank" DOUBLE PRECISION,
    "BFlyweightRank" DOUBLE PRECISION,
    "BPFPRank" DOUBLE PRECISION,
    "BetterRank" TEXT,
    "Finish" TEXT,
    "FinishDetails" TEXT,
    "FinishRound" DOUBLE PRECISION,
    "FinishRoundTime" TEXT,
    "TotalFightTimeSecs" DOUBLE PRECISION,
    "RedDecOdds" DOUBLE PRECISION,
    "BlueDecOdds" DOUBLE PRECISION,
    "RSubOdds" DOUBLE PRECISION,
    "BSubOdds" DOUBLE PRECISION,
    "RKOOdds" DOUBLE PRECISION,
    "BKOOdds" DOUBLE PRECISION,
    "RedMatchSigStr" DOUBLE PRECISION,
    "BlueMatchSigStr" DOUBLE PRECISION,
    "RedMatchTD" DOUBLE PRECISION,
    "BlueMatchTD" DOUBLE PRECISION,
    "RedMatchSubAtt" DOUBLE PRECISION,
    "BlueMatchSubAtt" DOUBLE PRECISION,
    "MatchFightTime" DOUBLE PRECISION,
    "FightTag" TEXT PRIMARY KEY,
    "Result" BIGINT
);

-- Upcoming fight cards + predictions served by GET /upcoming. Loose display
-- payloads, so kept as JSONB (the backend already returns them as generic maps).
CREATE TABLE IF NOT EXISTS upcoming (
    doc_id TEXT PRIMARY KEY,
    data   JSONB NOT NULL
);

-- Previous fight cards + results served by GET /previous. Same rationale as above.
CREATE TABLE IF NOT EXISTS previous (
    doc_id TEXT PRIMARY KEY,
    data   JSONB NOT NULL
);

-- Single-row pointer to the current production model (mirrors the old
-- Firestore metadata/model_version doc). Superseded by the MLflow Model
-- Registry in Phase 2B, but kept here so Phase 2A fully retires Firestore.
CREATE TABLE IF NOT EXISTS model_version (
    id               TEXT PRIMARY KEY DEFAULT 'current',
    winner_accuracy  DOUBLE PRECISION NOT NULL DEFAULT 0,
    version          BIGINT NOT NULL DEFAULT 0,
    trained_at       TEXT
);

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS model_version;
DROP TABLE IF EXISTS previous;
DROP TABLE IF EXISTS upcoming;
DROP TABLE IF EXISTS ufc_master;
DROP TABLE IF EXISTS fighters;
-- +goose StatementEnd
