import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "automation_bot")
OWNER_IDS = [int(x.strip()) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip()]
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/bot.db")
BROADCAST_DELAY = float(os.getenv("BROADCAST_DELAY", "0.3"))
SCHEDULER_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL", "60"))
