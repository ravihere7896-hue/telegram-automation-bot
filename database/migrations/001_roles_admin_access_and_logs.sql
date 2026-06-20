PRAGMA foreign_keys=ON;

-- Migration: add role/is_banned, admin_account_access, action_logs
BEGIN;
-- The following ALTER statements can fail on some SQLite versions if columns already exist.
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';
ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0;
COMMIT;

CREATE TABLE IF NOT EXISTS admin_account_access (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  admin_user_id INTEGER NOT NULL,
  account_id INTEGER,
  all_access INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(admin_user_id, account_id)
);

CREATE TABLE IF NOT EXISTS action_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_user_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  target_type TEXT,
  target_id INTEGER,
  details TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
