from dotenv import load_dotenv
import os

def load_env():
    """Load environment variables from .env file"""
    # Try to load from .env file
    if os.path.exists('.env'):
        load_dotenv('.env')
        print("✅ Fichier .env chargé")
    else:
        print("⚠️ Fichier .env non trouvé")
    
    # Validation des variables critiques
    if not os.getenv('API_ID') or not os.getenv('BOT_TOKEN'):
        print("❌ Variables d'environnement manquantes")
        exit(1)
