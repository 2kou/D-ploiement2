
import logging
import os
import zipfile
import shutil
from telethon import events
from datetime import datetime

logger = logging.getLogger(__name__)

async def handle_deploy(event, client):
    """
    Handle deployment command - creates ZIP file with all bot files
    Premium feature for licensed users
    """
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.\nUtilisez `/valide` pour activer votre licence.")
            return
        
        await event.respond("📦 **Création du package de déploiement...**\n\n⏳ Préparation des fichiers en cours...")
        
        # Create deployment ZIP
        zip_path = await create_deployment_zip()
        
        if zip_path and os.path.exists(zip_path):
            # Send the ZIP file
            await client.send_file(
                user_id,
                zip_path,
                caption="""
✅ **Package de déploiement TeleFeed**

📁 **Contenu du package :**
• Tous les fichiers du bot
• Configuration de déploiement
• Variables d'environnement (.env.example)
• Documentation complète

🚀 **Prêt pour le déploiement sur Render.com**

📋 **Instructions :**
1. Décompressez le fichier ZIP
2. Configurez vos variables d'environnement
3. Déployez sur Render.com
4. Votre bot sera opérationnel !
                """,
                attributes=[],
                force_document=True
            )
            
            # Clean up
            os.remove(zip_path)
            logger.info(f"Deployment package sent to user {user_id}")
            
        else:
            await event.respond("❌ **Erreur lors de la création du package**\n\nVeuillez réessayer plus tard.")
            
    except Exception as e:
        logger.error(f"Error in deploy handling: {e}")
        await event.respond("❌ Erreur lors du traitement du déploiement. Veuillez réessayer.")

async def create_deployment_zip():
    """Create a ZIP file with all necessary deployment files"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"TeleFeed_deployment_{timestamp}.zip"
        zip_path = os.path.join(os.getcwd(), zip_filename)
        
        # Files and directories to include
        files_to_include = [
            'main.py',
            'bot/',
            'config/',
            'logs/',
            'requirements.txt',
            'Procfile',
            'runtime.txt',
            '.env.example'
        ]
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in files_to_include:
                if os.path.exists(item):
                    if os.path.isfile(item):
                        # Add file
                        zipf.write(item, item)
                        logger.info(f"Added file to ZIP: {item}")
                    elif os.path.isdir(item):
                        # Add directory and all its contents
                        for root, dirs, files in os.walk(item):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Skip session files and __pycache__
                                if not file.endswith('.session') and '__pycache__' not in file_path:
                                    zipf.write(file_path, file_path)
                                    logger.info(f"Added file to ZIP: {file_path}")
            
            # Create deployment instructions
            instructions = """
# TeleFeed Bot - Instructions de Déploiement

## Configuration requise

1. **Variables d'environnement (.env) :**
   - API_ID=votre_api_id
   - API_HASH=votre_api_hash
   - BOT_TOKEN=votre_bot_token
   - DATABASE_URL=votre_database_url
   - ADMIN_ID=votre_admin_id

2. **Base de données :**
   - PostgreSQL requis
   - Configurez DATABASE_URL avec vos credentials

## Déploiement sur Render.com

1. Créez un nouveau service Web
2. Connectez votre repository
3. Configurez les variables d'environnement
4. Le bot se lancera automatiquement avec `python main.py`

## Fonctionnalités incluses

- ✅ Gestion des sessions persistantes
- ✅ Redirections automatiques
- ✅ Système de licences
- ✅ Paiements intégrés
- ✅ Administration complète

## Support

Pour toute assistance, contactez le support TeleFeed.
            """
            
            zipf.writestr("DEPLOYMENT_INSTRUCTIONS.md", instructions)
            
            # Create .env.example if it doesn't exist
            env_example = """
# TeleFeed Bot Configuration
API_ID=your_api_id_here
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://user:password@host:port/database
ADMIN_ID=your_admin_id_here
            """
            
            if not os.path.exists('.env.example'):
                zipf.writestr(".env.example", env_example)
        
        logger.info(f"Deployment ZIP created: {zip_path}")
        return zip_path
        
    except Exception as e:
        logger.error(f"Error creating deployment ZIP: {e}")
        return None

async def is_premium_user(user_id):
    """Check if user has premium access"""
    from bot.database import is_user_licensed
    return await is_user_licensed(user_id)
