from functools import wraps
from database.db_handler import get_user_by_tg, create_user_if_not_exists, is_admin_allowed_on_account, get_conn
from telegram import Update
from telegram.ext import CallbackContext
import os

def require_registered(fn):
    @wraps(fn)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
        tg_id = update.effective_user.id
        user = get_user_by_tg(conn, tg_id)
        if not user:
            create_user_if_not_exists(conn, tg_id, update.effective_user.username or "", update.effective_user.first_name or "")
        return fn(update, context, *args, **kwargs)
    return wrapper

def require_not_banned(fn):
    @wraps(fn)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
        tg_id = update.effective_user.id
        user = get_user_by_tg(conn, tg_id)
        if user and user["is_banned"]:
            try:
                update.effective_message.reply_text("You are banned from using this bot.")
            except:
                pass
            return
        return fn(update, context, *args, **kwargs)
    return wrapper

def require_role(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
            tg_id = update.effective_user.id
            user = get_user_by_tg(conn, tg_id)
            owner_ids = [int(x.strip()) for x in (os.getenv("OWNER_IDS") or "").split(",") if x.strip()]
            if user and (user["role"] == required_role or tg_id in owner_ids):
                return fn(update, context, *args, **kwargs)
            try:
                update.effective_message.reply_text("You don't have permission to perform this action.")
            except:
                pass
            return
        return wrapper
    return decorator

def require_owner_or_admin(fn):
    @wraps(fn)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
        tg_id = update.effective_user.id
        user = get_user_by_tg(conn, tg_id)
        owner_ids = [int(x.strip()) for x in (os.getenv("OWNER_IDS") or "").split(",") if x.strip()]
        if user and (user["role"] in ("owner", "admin") or tg_id in owner_ids):
            return fn(update, context, *args, **kwargs)
        try:
            update.effective_message.reply_text("Owner/Admin only command.")
        except:
            pass
        return
    return wrapper

def require_account_access(account_id_kw='account_id'):
    def decorator(fn):
        @wraps(fn)
        def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
            tg_id = update.effective_user.id
            user = get_user_by_tg(conn, tg_id)
            if not user:
                try:
                    update.effective_message.reply_text("Please /start to register first.")
                except:
                    pass
                return
            if user["role"] == "owner" or tg_id in [int(x.strip()) for x in (os.getenv("OWNER_IDS") or "").split(",") if x.strip()]:
                return fn(update, context, *args, **kwargs)
            if user["role"] == "admin":
                account_id = kwargs.get(account_id_kw)
                if account_id is None:
                    if context.args:
                        try:
                            account_id = int(context.args[0])
                        except:
                            account_id = None
                if account_id is None:
                    try:
                        update.effective_message.reply_text("Account ID missing.")
                    except:
                        pass
                    return
                if is_admin_allowed_on_account(conn, user["id"], int(account_id)):
                    return fn(update, context, *args, **kwargs)
                try:
                    update.effective_message.reply_text("You do not have access to that account.")
                except:
                    pass
                return
            # regular user: must own account
            account_id = kwargs.get(account_id_kw)
            if account_id is None and context.args:
                try:
                    account_id = int(context.args[0])
                except:
                    account_id = None
            if account_id is None:
                try:
                    update.effective_message.reply_text("Account ID missing.")
                except:
                    pass
                return
            from database.db_handler import get_account_by_id
            account = get_account_by_id(conn, int(account_id))
            if not account:
                try:
                    update.effective_message.reply_text("Account not found.")
                except:
                    pass
                return
            if account["owner_id"] != user["id"]:
                try:
                    update.effective_message.reply_text("You don't own that account.")
                except:
                    pass
                return
            return fn(update, context, *args, **kwargs)
        return wrapper
    return decorator
