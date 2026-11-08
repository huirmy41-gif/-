-- Additive migration. Preserve legacy child_state and essays.
CREATE TABLE IF NOT EXISTS wordpet_snapshots_v2(singleton TEXT PRIMARY KEY CHECK(singleton='main'),state_json TEXT NOT NULL,version INTEGER NOT NULL CHECK(version>0),updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS wordpet_limits_v2(bucket TEXT PRIMARY KEY,hits INTEGER NOT NULL);
