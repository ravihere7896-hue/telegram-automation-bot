from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from database.db_handler import (
    get_conn, get_all_accounts, get_owner_ids_from_env,
    grant_admin_all, revoke_admin_all, grant_admin_account, revoke_admin_account,
    log_action, get_user_by_tg, get_account_by_id, set_user_role
)
import math
import logging

logger = logging.getLogger(__name__)
ACCOUNTS_PER_PAGE = 8

def _get_all_accounts_list(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts ORDER BY id DESC")
    return cur.fetchall()

def _build_accounts_keyboard(accounts, admin_db_id, page=0, selected_ids=None):
    selected_ids = set(selected_ids or [])
    kb = []
    start = page * ACCOUNTS_PER_PAGE
    end = start + ACCOUNTS_PER_PAGE
    for acc in accounts[start:end]:
        acc_id = acc["id"]
        label = f"{acc['username'] or acc_id}"
        btn_text = f"✅ {label}" if acc_id in selected_ids else label
        kb.append([InlineKeyboardButton(btn_text, callback_data=f"grant_toggle:{admin_db_id}:{acc_id}:{page}")])
    total_pages = max(1, math.ceil(len(accounts) / ACCOUNTS_PER_PAGE))
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"grant_page:{admin_db_id}:{page-1}"))
    nav_row.append(InlineKeyboardButton(f"Page {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"grant_page:{admin_db_id}:{page+1}"))
    kb.append(nav_row)
    kb.append([InlineKeyboardButton("✅ Done", callback_data=f"grant_done:{admin_db_id}:{page}"),
               InlineKeyboardButton("❌ Cancel", callback_data="grant_cancel")])
    return InlineKeyboardMarkup(kb)

def notify_owners_on_account_removed(context: CallbackContext, conn, removed_account_id: int, removed_by_tg_id: int):
    owners = get_owner_ids_from_env()
    account = get_account_by_id(conn, removed_account_id)
    remover = None
    if removed_by_tg_id:
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE tg_id = ?", (removed_by_tg_id,))
        r = cur.fetchone()
        remover = f"{removed_by_tg_id} (@{r['username']})" if r else str(removed_by_tg_id)
    message = (
        f"⚠️ Account removed\nAccount ID: {removed_account_id}\n"
        f"Username: {account['username'] if account else 'unknown'}\n"
        f"Removed by: {remover}\n"
    )
    for oid in owners:
        try:
            context.bot.send_message(chat_id=oid, text=message)
        except Exception:
            logger.exception("Failed to notify owner %s", oid)

def callback_router(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return
    data = query.data or ""
    query.answer()
    conn = get_conn()
    user = update.effective_user

    if data == "owner_menu":
        kb = [
            [InlineKeyboardButton("👥 Show All Users", callback_data="owner_show_users")],
            [InlineKeyboardButton("🛠 Grant Admin", callback_data="owner_grant_admin")],
            [InlineKeyboardButton("🚫 Revoke Admin", callback_data="owner_revoke_admin")],
            [InlineKeyboardButton("📣 Broadcast", callback_data="owner_broadcast")],
        ]
        query.edit_message_text("Owner menu:", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "owner_show_users":
        cur = conn.cursor()
        cur.execute(
            "SELECT u.id, u.tg_id, u.username, u.first_name, u.role, u.is_banned, COUNT(a.id) as account_count "
            "FROM users u LEFT JOIN accounts a ON a.owner_id = u.id GROUP BY u.id ORDER BY account_count DESC"
        )
        rows = cur.fetchall()
        if not rows:
            query.edit_message_text("No users found.")
            return
        lines = []
        for r in rows:
            lines.append(f"{r['tg_id']} | @{r['username'] or '—'} | {r['first_name'] or '—'} | role={r['role']} | accounts={r['account_count']} | banned={'yes' if r['is_banned'] else 'no'}")
        query.edit_message_text("Users:\n\n" + "\n".join(lines))
        return

    # Grant admin start
    if data == "owner_grant_admin":
        query.edit_message_text("Reply in chat with the target admin's TELEGRAM NUMERIC ID to grant admin role.")
        context.user_data["grant_admin_step"] = "await_id"
        return

    if data == "owner_revoke_admin":
        query.edit_message_text("Reply in chat with the admin's TELEGRAM NUMERIC ID to revoke admin role.")
        context.user_data["revoke_admin_step"] = "await_id"
        return

    # Grant flow: scope selection and account selection
    if data.startswith("grant_scope_all:"):
        admin_db_id = int(data.split(":", 1)[1])
        try:
            grant_admin_all(conn, admin_db_id, actor_user_id=get_user_by_tg(conn, user.id)["id"])
            query.edit_message_text("All accounts granted to admin.")
        except Exception:
            query.edit_message_text("Failed to grant all accounts.")
        return

    if data.startswith("grant_scope_select:"):
        admin_db_id = int(data.split(":",1)[1])
        accounts = _get_all_accounts_list(conn)
        context.user_data.setdefault("grant_selected_accounts", [])
        context.user_data["grant_admin_selecting"] = admin_db_id
        page = 0
        kb = _build_accounts_keyboard(accounts, admin_db_id, page, selected_ids=context.user_data["grant_selected_accounts"])
        query.edit_message_text("Select accounts to grant (toggle):", reply_markup=kb)
        return

    if data.startswith("grant_page:"):
        _, admin_db_id_str, page_str = data.split(":")
        admin_db_id = int(admin_db_id_str); page = int(page_str)
        accounts = _get_all_accounts_list(conn)
        selected = context.user_data.get("grant_selected_accounts", [])
        kb = _build_accounts_keyboard(accounts, admin_db_id, page, selected_ids=selected)
        query.edit_message_text("Select accounts to grant (toggle):", reply_markup=kb)
        return

    if data.startswith("grant_toggle:"):
        _, admin_db_id_str, acc_id_str, page_str = data.split(":")
        admin_db_id = int(admin_db_id_str); acc_id = int(acc_id_str); page = int(page_str)
        sel = set(context.user_data.get("grant_selected_accounts", []))
        if acc_id in sel:
            sel.remove(acc_id)
        else:
            sel.add(acc_id)
        context.user_data["grant_selected_accounts"] = list(sel)
        accounts = _get_all_accounts_list(conn)
        kb = _build_accounts_keyboard(accounts, admin_db_id, page, selected_ids=context.user_data["grant_selected_accounts"])
        query.edit_message_reply_markup(reply_markup=kb)
        return

    if data.startswith("grant_done:"):
        _, admin_db_id_str, page_str = data.split(":")
        admin_db_id = int(admin_db_id_str)
        selected = context.user_data.get("grant_selected_accounts", [])
        if not selected:
            query.edit_message_text("No accounts selected. Cancelled.")
            context.user_data.pop("grant_selected_accounts", None)
            context.user_data.pop("grant_admin_selecting", None)
            return
        ids_csv = ",".join(str(x) for x in selected)
        kb = [
            [InlineKeyboardButton("Confirm grant", callback_data=f"grant_confirm_selected:{admin_db_id}:{ids_csv}")],
            [InlineKeyboardButton("Cancel", callback_data="grant_cancel")]
        ]
        query.edit_message_text(f"Confirm granting {len(selected)} accounts to admin?", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("grant_confirm_selected:"):
        parts = data.split(":", 2)
        admin_db_id = int(parts[1])
        ids_csv = parts[2] if len(parts) > 2 else ""
        ids = [int(x) for x in ids_csv.split(",") if x.strip()]
        try:
            for aid in ids:
                grant_admin_account(conn, admin_db_id, aid, actor_user_id=get_user_by_tg(conn, user.id)["id"])
            query.edit_message_text(f"Granted {len(ids)} accounts to admin.")
        except Exception:
            query.edit_message_text("Failed to grant selected accounts.")
        context.user_data.pop("grant_selected_accounts", None)
        context.user_data.pop("grant_admin_selecting", None)
        return

    if data == "grant_cancel":
        query.edit_message_text("Grant flow cancelled.")
        context.user_data.pop("grant_selected_accounts", None)
        context.user_data.pop("grant_admin_selecting", None)
        context.user_data.pop("grant_admin_step", None)
        return

    if data.startswith("revoke_confirm_admin:"):
        admin_db_id = int(data.split(":",1)[1])
        try:
            revoke_admin_all(conn, admin_db_id, actor_user_id=get_user_by_tg(conn, user.id)["id"])
            set_user_role(conn, admin_db_id, "user")
            query.edit_message_text("Admin revoked successfully.")
        except Exception:
            query.edit_message_text("Failed to revoke admin.")
        return

    if data == "owner_broadcast":
        kb = [
            [InlineKeyboardButton("All Users", callback_data="broadcast_scope:all")],
            [InlineKeyboardButton("Only Admins", callback_data="broadcast_scope:admins")],
            [InlineKeyboardButton("Specific IDs", callback_data="broadcast_scope:specific")],
            [InlineKeyboardButton("Cancel", callback_data="broadcast_cancel")]
        ]
        query.edit_message_text("Choose broadcast scope:", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("broadcast_scope:"):
        scope = data.split(":",1)[1]
        context.user_data["broadcast_scope"] = scope
        if scope == "specific":
            query.edit_message_text("Reply in chat with comma-separated numeric TG IDs to broadcast to (e.g. 12345,67890).")
            context.user_data["broadcast_specific_step"] = True
            return
        context.user_data["broadcast_mode"] = True
        query.edit_message_text("Send the broadcast message text now.")
        return

    if data == "broadcast_cancel":
        query.edit_message_text("Broadcast cancelled.")
        context.user_data.pop("broadcast_scope", None)
        context.user_data.pop("broadcast_mode", None)
        return

    # noop / unknown
    return
