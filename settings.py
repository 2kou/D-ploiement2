import os
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

# Telegram API Configuration
API_ID = int(os.getenv("API_ID") or "0")
API_HASH = os.getenv("API_HASH") or ""
BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
ADMIN_ID = int(os.getenv("ADMIN_ID") or "0")

# Validate configuration
if not API_ID or not API_HASH or not BOT_TOKEN:
    print("❌ Erreur: Variables d'environnement manquantes")
    exit(1)

# Bot Configuration
BOT_NAME = "TeleFeed"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
