# Telegram Automation Bot (Auto Voter)

This repository contains a Telegram automation bot with owner/admin controls, secure account token storage, simple scheduling, and broadcasting.

Key points
- Owner Telegram ID is set to 5908999967 in .env.example
- Account tokens are encrypted using Fernet (ENCRYPTION_KEY)
- Admins can be granted access to all accounts or specific accounts by owner
- Owner receives notifications when accounts are removed

Local setup
1. Create a Python virtualenv:
   python -m venv venv
   source venv/bin/activate

2. Install dependencies:
   pip install -r requirements.txt

3. Create a local .env (do NOT commit this file):
   BOT_TOKEN=<your-bot-token-from-botfather>
   OWNER_IDS=5908999967
   ENCRYPTION_KEY=<generate-a-fernet-key-as-shown-in .env.example>
   DATABASE_URL=sqlite:///data/bot.db

4. Start the bot:
   python main.py

Testing
- From Telegram, send /start to the bot (owner account should see Owner Menu)
- Use /schedule and /tasks to test scheduler
- Test owner features: Grant Admin (reply with numeric tg id), Broadcast, etc.

Security
- Keep BOT_TOKEN and ENCRYPTION_KEY secret.
- Back up your database before running migrations if you have existing data.
