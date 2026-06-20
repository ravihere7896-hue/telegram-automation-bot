import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Store tasks in memory (in production, use a database)
tasks = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        "I'm an automation bot. Here are my commands:\n"
        "/help - Show all commands\n"
        "/schedule - Schedule a task\n"
        "/tasks - List all tasks\n"
        "/start - Start the bot"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🤖 *Automation Bot Commands*

/start - Start the bot
/help - Show this help message
/schedule - Schedule a new task
  Example: /schedule 5 "Take a break"
  (schedules a task after 5 minutes)
/tasks - List all scheduled tasks
/ping - Check if bot is alive

*How to use:*
1. Use /schedule to create tasks
2. Use /tasks to view all tasks
3. Tasks are stored in memory (will reset on bot restart)

*Features:*
✅ Schedule reminders
✅ Automated task execution
✅ Task management
✅ Easy-to-use commands
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    user_text = update.message.text
    await update.message.reply_text(f"You said: {user_text}")


async def schedule_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Schedule a task for later execution."""
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /schedule <minutes> <task_description>\n"
                "Example: /schedule 5 Take a break"
            )
            return

        minutes = int(context.args[0])
        task_desc = ' '.join(context.args[1:])
        
        if minutes < 1 or minutes > 1440:  # Max 24 hours
            await update.message.reply_text("Please specify minutes between 1 and 1440")
            return

        # Create task
        task_id = len(tasks) + 1
        execute_time = datetime.now() + timedelta(minutes=minutes)
        
        tasks[task_id] = {
            'description': task_desc,
            'execute_at': execute_time,
            'user_id': update.effective_user.id,
            'chat_id': update.message.chat_id,
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
    """List all scheduled tasks."""
    if not tasks:
        await update.message.reply_text("No tasks scheduled yet. Use /schedule to create one!")
        return

    task_list = "📋 *Scheduled Tasks*\n\n"
    for task_id, task in tasks.items():
        status = "✅ Done" if task['executed'] else "⏳ Pending"
        time_left = task['execute_at'] - datetime.now()
        minutes_left = int(time_left.total_seconds() / 60)
        
        task_list += (
            f"*Task {task_id}*\n"
            f"Description: {task['description']}\n"
            f"Status: {status}\n"
            f"Execute at: {task['execute_at'].strftime('%H:%M:%S')}\n"
            f"Time left: {max(0, minutes_left)} minutes\n\n"
        )

    await update.message.reply_text(task_list, parse_mode='Markdown')