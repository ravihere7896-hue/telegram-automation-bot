import sqlite3
import os
from typing import List, Tuple
from utils.encryption import encrypt_value, decrypt_value

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///data/bot.db").replace("sqlite:///", "")

def get_conn():
    if os.path.dirname(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# --- Users ---
def get_user_by_tg(conn, tg_id: int):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    return cur.fetchone()

def create_user_if_not_exists(conn, tg_id: int, username: str, first_name: str):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute(
        "INSERT INTO users (tg_id, username, first_name, role, is_banned, created_at) VALUES (?, ?, ?, 'user', 0, CURRENT_TIMESTAMP)",
        (tg_id, username, first_name),
    )
    conn.commit()
    return cur.lastrowid

def set_user_role(conn, user_id: int, role: str):
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()

def set_user_banned(conn, user_id: int, banned: bool):
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = ? WHERE id = ?", (1 if banned else 0, user_id))
    conn.commit()

# --- Accounts ---
def add_account(conn, owner_user_id: int, username: str, token_plain: str):
    token_enc = encrypt_value(token_plain)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO accounts (owner_id, username, token_encrypted, is_active, created_at) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)",
        (owner_user_id, username, token_enc),
    )
    conn.commit()
    return cur.lastrowid

def get_account_by_id(conn, account_id: int):
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
    return cur.fetchone()

def delete_account(conn, account_id: int, removed_by_user_id: int):
    account = get_account_by_id(conn, account_id)
    if not account:
        return False
    cur = conn.cursor()
    cur.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    log_action(conn, actor_user_id=removed_by_user_id, action='remove_account', target_type='account', target_id=account_id, details=f"username={account['username']}")
    return True

def get_all_accounts(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts")
    return cur.fetchall()

def decrypt_account_token(conn, account_row):
    if account_row is None:
        return None
    return decrypt_value(account_row["token_encrypted"])

# --- Admin access helpers ---
def grant_admin_all(conn, admin_user_id: int, actor_user_id: int):
    cur = conn.cursor()
    cur.execute("DELETE FROM admin_account_access WHERE admin_user_id = ?", (admin_user_id,))
    cur.execute("INSERT OR IGNORE INTO admin_account_access (admin_user_id, account_id, all_access) VALUES (?, NULL, 1)", (admin_user_id,))
    conn.commit()
    log_action(conn, actor_user_id=actor_user_id, action='grant_admin_all', target_type='user', target_id=admin_user_id)

def revoke_admin_all(conn, admin_user_id: int, actor_user_id: int):
    cur = conn.cursor()
    cur.execute("DELETE FROM admin_account_access WHERE admin_user_id = ?", (admin_user_id,))
    conn.commit()
    log_action(conn, actor_user_id=actor_user_id, action='revoke_admin_all', target_type='user', target_id=admin_user_id)

def grant_admin_account(conn, admin_user_id: int, account_id: int, actor_user_id: int):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admin_account_access WHERE admin_user_id=? AND all_access=1", (admin_user_id,))
    if cur.fetchone():
        return
    cur.execute("INSERT OR IGNORE INTO admin_account_access (admin_user_id, account_id, all_access) VALUES (?, ?, 0)", (admin_user_id, account_id))
    conn.commit()
    log_action(conn, actor_user_id=actor_user_id, action='grant_admin_account', target_type='account', target_id=account_id, details=f"granted_to_admin={admin_user_id}")

def revoke_admin_account(conn, admin_user_id: int, account_id: int, actor_user_id: int):
    cur = conn.cursor()
    cur.execute("DELETE FROM admin_account_access WHERE admin_user_id=? AND account_id=?", (admin_user_id, account_id))
    conn.commit()
    log_action(conn, actor_user_id=actor_user_id, action='revoke_admin_account', target_type='account', target_id=account_id, details=f"revoked_from_admin={admin_user_id}")

def get_admin_accessible_accounts(conn, admin_user_id: int) -> Tuple[bool, List[sqlite3.Row]]:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admin_account_access WHERE admin_user_id=? AND all_access=1 LIMIT 1", (admin_user_id,))
    if cur.fetchone():
        cur2 = conn.cursor()
        cur2.execute("SELECT * FROM accounts")
        return True, cur2.fetchall()
    cur.execute("SELECT account_id FROM admin_account_access WHERE admin_user_id=? AND account_id IS NOT NULL", (admin_user_id,))
    ids = [r["account_id"] for r in cur.fetchall()]
    if not ids:
        return False, []
    placeholders = ",".join("?" for _ in ids)
    cur.execute(f"SELECT * FROM accounts WHERE id IN ({placeholders})", ids)
    return False, cur.fetchall()

def is_admin_allowed_on_account(conn, admin_user_id: int, account_id: int) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admin_account_access WHERE admin_user_id=? AND all_access=1 LIMIT 1", (admin_user_id,))
    if cur.fetchone():
        return True
    cur.execute("SELECT 1 FROM admin_account_access WHERE admin_user_id=? AND account_id=? LIMIT 1", (admin_user_id, account_id))
    return cur.fetchone() is not None

# --- Logging ---
def log_action(conn, actor_user_id: int, action: str, target_type: str = None, target_id: int = None, details: str = None):
    cur = conn.cursor()
    cur.execute("INSERT INTO action_logs (actor_user_id, action, target_type, target_id, details, timestamp) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (actor_user_id, action, target_type, target_id, details))
    conn.commit()

# --- Owner helpers ---
def get_owner_ids_from_env():
    raw = os.getenv("OWNER_IDS", "")
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]

def get_owner_users(conn):
    cur = conn.cursor()
    owner_ids = get_owner_ids_from_env()
    if not owner_ids:
        return []
    placeholders = ",".join("?" for _ in owner_ids)
    cur.execute(f"SELECT * FROM users WHERE tg_id IN ({placeholders})", owner_ids)
    return cur.fetchall()
