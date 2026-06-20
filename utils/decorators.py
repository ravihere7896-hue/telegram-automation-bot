import inspect
from functools import wraps
from database.db_handler import get_user_by_tg, create_user_if_not_exists, is_admin_allowed_on_account, get_conn
from telegram import Update
from telegram.ext import CallbackContext
import os

def require_registered(fn):
    @wraps(fn)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
        tg_id = update.effective_user.id
        user = get_user_by_tg(conn, tg_id)
        if not user:
            create_user_if_not_exists(conn, tg_id, update.effective_user.username or "", update.effective_user.first_name or "")
        result = fn(update, context, *args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
    return wrapper

def require_not_banned(fn):
    @wraps(fn)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
        tg_id = update.effective_user.id
        user = get_user_by_tg(conn, tg_id)
        if user and user["is_banned"]:
            try:
                resp = update.effective_message.reply_text("You are banned from using this bot.")
                if inspect.isawaitable(resp):
                    await resp
            except Exception:
                pass
            return
        result = fn(update, context, *args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
    return wrapper

def require_role(required_role):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
            tg_id = update.effective_user.id
            user = get_user_by_tg(conn, tg_id)
            owner_ids = [int(x.strip()) for x in (os.getenv("OWNER_IDS") or "").split(",") if x.strip()]
            if user and (user["role"] == required_role or tg_id in owner_ids):
                result = fn(update, context, *args, **kwargs)
                if inspect.isawaitable(result):
                    return await result
                return result
            try:
                resp = update.effective_message.reply_text("You don't have permission to perform this action.")
                if inspect.isawaitable(resp):
                    await resp
            except Exception:
                pass
            return
        return wrapper
    return decorator

def require_owner_or_admin(fn):
    @wraps(fn)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
        tg_id = update.effective_user.id
        user = get_user_by_tg(conn, tg_id)
        owner_ids = [int(x.strip()) for x in (os.getenv("OWNER_IDS") or "").split(",") if x.strip()]
        if user and (user["role"] in ("owner", "admin") or tg_id in owner_ids):
            result = fn(update, context, *args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        try:
            resp = update.effective_message.reply_text("Owner/Admin only command.")
            if inspect.isawaitable(resp):
                await resp
        except Exception:
            pass
        return
    return wrapper

def require_account_access(account_id_kw='account_id'):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            conn = context.db_conn if hasattr(context, "db_conn") else get_conn()
            tg_id = update.effective_user.id
            user = get_user_by_tg(conn, tg_id)
            if not user:
                try:
                    resp = update.effective_message.reply_text("Please /start to register first.")
                    if inspect.isawaitable(resp):
                        await resp
                except:
                    pass
                return
            owner_ids = [int(x.strip()) for x in (os.getenv("OWNER_IDS") or "").split(",") if x.strip()]
            if user["role"] == "owner" or tg_id in owner_ids:
                result = fn(update, context, *args, **kwargs)
                if inspect.isawaitable(result):
                    return await result
                return result
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
                        resp = update.effective_message.reply_text("Account ID missing.")
                        if inspect.isawaitable(resp):
                            await resp
                    except:
                        pass
                    return
                if is_admin_allowed_on_account(conn, user["id"], int(account_id)):
                    result = fn(update, context, *args, **kwargs)
                    if inspect.isawaitable(result):
                        return await result
                    return result
                try:
                    resp = update.effective_message.reply_text("You do not have access to that account.")
                    if inspect.isawaitable(resp):
                        await resp
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
                    resp = update.effective_message.reply_text("Account ID missing.")
                    if inspect.isawaitable(resp):
                        await resp
                except:
                    pass
                return
            from database.db_handler import get_account_by_id
            account = get_account_by_id(conn, int(account_id))
            if not account:
                try:
                    resp = update.effective_message.reply_text("Account not found.")
                    if inspect.isawaitable(resp):
                        await resp
                except:
                    pass
                return
            if account["owner_id"] != user["id"]:
                try:
                    resp = update.effective_message.reply_text("You don't own that account.")
                    if inspect.isawaitable(resp):
                        await resp
                except:
                    pass
                return
            result = fn(update, context, *args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        return wrapper
    return decorator
