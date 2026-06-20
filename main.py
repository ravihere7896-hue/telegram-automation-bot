import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN, SCHEDULER_INTERVAL
from handlers import start, help_command, echo, schedule_task, list_tasks
from scheduler import start_scheduler
from handlers.admin_handlers import callback_router
from database.db_handler import get_conn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_migrations(conn):
    path = os.path.join(os.path.dirname(__file__), "database", "migrations", "001_roles_admin_access_and_logs.sql")
    if os.path.exists(path):
        with open(path, "r") as f:
            sql = f.read()
        try:
            conn.executescript(sql)
        except Exception as e:
            logger.info("Migration may have already been applied or returned an error: %s", e)


def main():
    token = BOT_TOKEN
    if not token or token.startswith("YOUR"):
        raise RuntimeError("BOT_TOKEN not set. Populate it in a local .env (do NOT commit .env).")

    application = Application.builder().token(token).build()

    conn = get_conn()
    ensure_migrations(conn)

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("schedule", schedule_task))
    application.add_handler(CommandHandler("tasks", list_tasks))

    # Echo handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Admin/owner callback router
    application.add_handler(CallbackQueryHandler(callback_router))

    # Start scheduler
    start_scheduler(application)

    application.run_polling()


if __name__ == "__main__":
    main()
