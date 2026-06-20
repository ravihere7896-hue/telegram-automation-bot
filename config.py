import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Bot settings
BOT_USERNAME = os.getenv('BOT_USERNAME', 'automation_bot')
MAX_TASKS = 10
SCHEDULER_INTERVAL = 60  # Check tasks every 60 seconds