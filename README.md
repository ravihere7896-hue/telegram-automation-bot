# Telegram Automation Bot 🤖

A Python-based Telegram bot for automating tasks, scheduling reminders, and managing notifications.

## Features ✨

✅ Schedule tasks and reminders
✅ Automated task execution
✅ Task management and tracking
✅ Easy-to-use commands
✅ Memory-based task storage

## Prerequisites 📋

- Python 3.8 or higher
- pip (Python package manager)
- A Telegram account
- Telegram Bot Token (from @BotFather)

## Installation 🚀

1. Clone the repository:
```bash
git clone https://github.com/ravihere7896-hue/telegram-automation-bot.git
cd telegram-automation-bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file:
```bash
cp .env.example .env
```

5. Add your bot token to the .env file:
- Get your token from @BotFather on Telegram
- Open .env and replace `your_bot_token_here` with your actual token

## Usage 🎮

Start the bot:
```bash
python main.py
```

### Commands:
- `/start` - Start the bot
- `/help` - Show all available commands
- `/schedule <minutes> <task>` - Schedule a task
  - Example: `/schedule 5 Take a break`
- `/tasks` - List all scheduled tasks

## How to Get Your Bot Token 🔑

1. Open Telegram and search for @BotFather
2. Start a conversation and send `/newbot`
3. Follow the prompts to create your bot
4. Copy the token provided
5. Paste it in your .env file

## Project Structure 📁

```
telegram-automation-bot/
├── main.py              # Main bot application
├── config.py            # Configuration settings
├── handlers.py          # Command and message handlers
├── scheduler.py         # Task scheduler
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore file
└── README.md           # This file
```

## Examples 💡

Schedule a reminder in 10 minutes:
```
/schedule 10 Call mom
```

Schedule a task in 1 hour:
```
/schedule 60 Complete project
```

View all tasks:
```
/tasks
```

## Deployment 🌐

### Heroku Deployment:
```bash
# Install Heroku CLI and log in
heroku create your-bot-name
heroku config:set BOT_TOKEN=your_token_here
git push heroku main
```

## Troubleshooting 🔧

**Bot not responding?**
- Check if BOT_TOKEN is correct in .env
- Ensure bot is running: `python main.py`
- Check internet connection
- Verify Telegram API is accessible

**Tasks not executing?**
- Check if scheduler is started
- Verify system time is correct
- Check logs for errors

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is open source and available under the MIT License.

## Support 💬

For issues and questions, please create an issue on GitHub.

---

**Happy automating!** 🎉