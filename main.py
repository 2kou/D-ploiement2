from config.env_loader import load_env
from bot.handlers import start_bot_sync
import os

if __name__ == "__main__":
    load_env()

    # Log deployment success message
    print("🚀 bot déployé avec succès")

    # Start the bot
    start_bot_sync()