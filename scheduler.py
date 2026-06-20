import logging
from datetime import datetime
from telegram.ext import Application
from handlers import tasks
from config import SCHEDULER_INTERVAL

logger = logging.getLogger(__name__)


async def check_tasks(context):
    """Check and execute scheduled tasks."""
    current_time = datetime.now()
    
    for task_id, task in list(tasks.items()):
        if not task['executed'] and current_time >= task['execute_at']:
            try:
                # Send reminder to user
                await context.bot.send_message(
                    chat_id=task['chat_id'],
                    text=f"⏰ *Task Reminder*\n\n"
                         f"Task ID: {task_id}\n"
                         f"Description: {task['description']}\n"
                         f"Scheduled time: {task['execute_at'].strftime('%H:%M:%S')}\n"
                         f"Executed at: {current_time.strftime('%H:%M:%S')}",
                    parse_mode='Markdown'
                )
                task['executed'] = True
                logger.info(f"Task {task_id} executed successfully")
            except Exception as e:
                logger.error(f"Error executing task {task_id}: {e}")


def start_scheduler(application: Application):
    """Start the task scheduler."""
    # Add job to check tasks every SCHEDULER_INTERVAL seconds
    application.job_queue.run_repeating(
        check_tasks,
        interval=SCHEDULER_INTERVAL,
        first=0
    )
    logger.info(f"Scheduler started - checking tasks every {SCHEDULER_INTERVAL} seconds")