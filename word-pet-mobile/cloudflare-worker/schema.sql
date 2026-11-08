CREATE TABLE IF NOT EXISTS child_state (
  child_id TEXT PRIMARY KEY,
  state_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS essays (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  child_id TEXT NOT NULL,
  title TEXT NOT NULL,
  essay_text TEXT NOT NULL,
  created_at TEXT NOT NULL
);
