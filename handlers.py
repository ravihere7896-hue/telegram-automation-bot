import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from database.db_handler import get_conn, create_user_if_not_exists, get_owner_ids_from_env

logger = logging.getLogger(__name__)

# In-memory tasks (simple). For production replace with DB persistence.
tasks = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    conn = get_conn()
    # Ensure users table exists? If not, the migration should be applied.
    try:
        create_user_if_not_exists(conn, user.id, user.username or "", user.first_name or "")
    except Exception:
        # ignore DB errors here; still show welcome
        logger.exception("Failed to register user on /start")

    kb = [
        [InlineKeyboardButton("✏️ Add Account", callback_data="add_account"),
         InlineKeyboardButton("✅ My Accounts", callback_data="my_accounts")],
        [InlineKeyboardButton("⭐ New Campaign", callback_data="new_campaign"),
         InlineKeyboardButton("🎯 My Campaigns", callback_data="my_campaigns")],
        [InlineKeyboardButton("⏰ Scheduled", callback_data="scheduled"),
         InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
        [InlineKeyboardButton("❓ Help & Guide", callback_data="help"),
         InlineKeyboardButton("📞 Support", callback_data="support")],
    ]
    owner_ids = get_owner_ids_from_env()
    if user and str(user.id) in [str(x) for x in owner_ids]:
        kb.append([InlineKeyboardButton("🛡 Owner Menu", callback_data="owner_menu")])

    welcome_text = (
        f"Hi {user.mention_html()}! 👋\n\n"
        "I'm an automation bot. Here are my commands:\n"
        "/help - Show all commands\n"
        "/schedule - Schedule a task\n"
        "/tasks - List all tasks\n\n"
        "Developer: @YOU_KNOW_RAVI_XD"
    )
    await update.message.reply_html(welcome_text, reply_markup=InlineKeyboardMarkup(kb))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🤖 *Automation Bot Commands*\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/schedule - Schedule a new task\n"
        "  Example: /schedule 5 Take a break\n"
        "/tasks - List all scheduled tasks\n"
        "/ping - Check if bot is alive\n\n"
        "*How to use:*\n"
        "1. Use /schedule to create tasks\n"
        "2. Use /tasks to view all tasks\n"
        "3. Tasks are stored in memory (will reset on bot restart)\n\n"
        "*Features:*\n"
        "✅ Schedule reminders\n"
        "✅ Automated task execution\n"
        "✅ Task management\n"
    )
    await update.message.reply_markdown(help_text)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    await update.message.reply_text(f"You said: {user_text}")

async def schedule_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /schedule <minutes> <task_description>\nExample: /schedule 5 Take a break"
            )
            return

        minutes = int(context.args[0])
        task_desc = ' '.join(context.args[1:])

        if minutes < 1 or minutes > 1440:
            await update.message.reply_text("Please specify minutes between 1 and 1440")
            return

        task_id = len(tasks) + 1
        execute_time = datetime.now() + timedelta(minutes=minutes)

        tasks[task_id] = {
            'description': task_desc,
            'execute_at': execute_time,
            'user_id': update.effective_user.id,
            'chat_id': update.effective_chat.id,
            'executed': False
        }

        await update.message.reply_text(
            f"✅ Task scheduled!\n"
            f"Task ID: {task_id}\n"
            f"Description: {task_desc}\n"
            f"Will execute in {minutes} minute(s)\n"
            f"At: {execute_time.strftime('%H:%M:%S')}"
        )
    except ValueError:
        await update.message.reply_text("Please provide a valid number of minutes")
    except Exception as e:
        logger.error(f"Error scheduling task: {e}")
        await update.message.reply_text("Error scheduling task. Please try again.")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not tasks:
        await update.message.reply_text("No tasks scheduled yet. Use /schedule to create one!")
        return

    parts = []
    for task_id, task in tasks.items():
        status = "✅ Done" if task['executed'] else "⏳ Pending"
        time_left = task['execute_at'] - datetime.now()
        minutes_left = int(time_left.total_seconds() / 60)
        parts.append(
            f"*Task {task_id}*\n"
            f"Description: {task['description']}\n"
            f"Status: {status}\n"
            f"Execute at: {task['execute_at'].strftime('%H:%M:%S')}\n"
            f"Time left: {max(0, minutes_left)} minutes\n"
        )
    text = "📋 *Scheduled Tasks*\n\n" + "\n".join(parts)
    await update.message.reply_markdown(text)
