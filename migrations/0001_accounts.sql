CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  alias TEXT NOT NULL,
  account_id TEXT NOT NULL UNIQUE,
  token TEXT NOT NULL,
  token_last4 TEXT,
  token_status TEXT DEFAULT 'unknown',
  enabled INTEGER DEFAULT 1,
  daily_quota INTEGER DEFAULT 100000,
  notes TEXT DEFAULT '',
  email_hint TEXT DEFAULT '',
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resources (
  kind TEXT NOT NULL,
  account_db_id INTEGER NOT NULL,
  item_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (kind, account_db_id, item_id)
);
CREATE INDEX IF NOT EXISTS idx_resources_account ON resources(account_db_id);
