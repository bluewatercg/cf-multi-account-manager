CREATE TABLE IF NOT EXISTS resources (
  kind TEXT NOT NULL,
  account_db_id INTEGER NOT NULL,
  item_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (kind, account_db_id, item_id)
);
CREATE INDEX IF NOT EXISTS idx_resources_account ON resources(account_db_id);
