
import logging
import os
import asyncio
from telethon import TelegramClient, events
from config.settings import API_ID, API_HASH, BOT_TOKEN, ADMIN_ID
from bot.license import check_license, validate_license_code
from bot.payment import process_payment
from bot.deploy import handle_deploy
from bot.connection import handle_connect, handle_verification_code
from bot.redirection import handle_redirection_command
from bot.transformation import handle_transformation_command
from bot.whitelist import handle_whitelist_command
from bot.blacklist import handle_blacklist_command
from bot.chats import handle_chats_command
from bot.admin import handle_admin_commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/activity.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Telegram client without starting it yet
client = TelegramClient('bot', API_ID, API_HASH)

@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Handle /start command"""
    try:
        welcome_message = """
🌟 **Bienvenue sur TeleFeed !** 🌟

Votre bot premium pour la gestion de contenu Telegram.

**Commandes disponibles :**
• `/connect` - Connecter un numéro de téléphone
• `/valide` - Valider votre licence premium
• `/payer` - Effectuer un paiement (une semaine/un mois)
• `/redirection` - Gérer les redirections entre chats
• `/transformation` - Modifier le contenu des messages
• `/whitelist` - Filtrer les messages autorisés
• `/blacklist` - Ignorer certains messages
• `/chats` - Afficher les chats associés à un numéro
• `/deposer` - Déposer des fichiers (premium)

Pour accéder aux fonctionnalités premium, veuillez valider votre licence avec `/valide`.
        """
        await event.respond(welcome_message)
        logger.info(f"User {event.sender_id} started the bot")
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await event.respond("❌ Une erreur est survenue. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/valide"))
async def valide(event):
    """Handle /valide command for license validation"""
    try:
        await check_license(event, client)
        logger.info(f"License validation requested by user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in license validation: {e}")
        await event.respond("❌ Erreur lors de la validation de licence. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/payer une semaine"))
async def payer_semaine(event):
    """Handle /payer une semaine command"""
    try:
        await process_payment(event, client, "une semaine")
        logger.info(f"Weekly payment request from user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in weekly payment processing: {e}")
        await event.respond("❌ Erreur lors du traitement du paiement. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/payer un mois"))
async def payer_mois(event):
    """Handle /payer un mois command"""
    try:
        await process_payment(event, client, "un mois")
        logger.info(f"Monthly payment request from user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in monthly payment processing: {e}")
        await event.respond("❌ Erreur lors du traitement du paiement. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/payer"))
async def payer(event):
    """Handle /payer command for payment processing"""
    try:
        # Check if it's a specific payment command
        if "une semaine" in event.text or "un mois" in event.text:
            return  # Let the specific handlers handle it first

        # Show payment options
        payment_options = """
💳 **Options de paiement TeleFeed**

Choisissez votre formule d'abonnement :

🔹 `/payer une semaine` - Abonnement hebdomadaire
🔹 `/payer un mois` - Abonnement mensuel

💡 **Après paiement :**
- Vous recevrez une licence unique
- Utilisez `/valide` pour l'activer
- Accès immédiat à toutes les fonctionnalités premium
        """
        await event.respond(payment_options)
        logger.info(f"Payment options shown to user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in payment processing: {e}")
        await event.respond("❌ Erreur lors du traitement du paiement. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/deposer"))
async def deposer(event):
    """Handle /deposer command for file deployment"""
    try:
        await handle_deploy(event, client)
        logger.info(f"Deploy request from user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in deploy handling: {e}")
        await event.respond("❌ Erreur lors du traitement du dépôt. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/connect"))
async def connect(event):
    """Handle /connect command"""
    try:
        await handle_connect(event, client)
        logger.info(f"Connect command used by user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in connect command: {e}")
        await event.respond("❌ Erreur lors de la connexion. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/redirection"))
async def redirection(event):
    """Handle /redirection command"""
    try:
        await handle_redirection_command(event, client)
        logger.info(f"Redirection command used by user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in redirection command: {e}")
        await event.respond("❌ Erreur lors de la redirection. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/transformation"))
async def transformation(event):
    """Handle /transformation command"""
    try:
        await handle_transformation_command(event, client)
        logger.info(f"Transformation command used by user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in transformation command: {e}")
        await event.respond("❌ Erreur lors de la transformation. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/whitelist"))
async def whitelist(event):
    """Handle /whitelist command"""
    try:
        await handle_whitelist_command(event, client)
        logger.info(f"Whitelist command used by user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in whitelist command: {e}")
        await event.respond("❌ Erreur lors de la whitelist. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/blacklist"))
async def blacklist(event):
    """Handle /blacklist command"""
    try:
        await handle_blacklist_command(event, client)
        logger.info(f"Blacklist command used by user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in blacklist command: {e}")
        await event.respond("❌ Erreur lors de la blacklist. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/chats"))
async def chats(event):
    """Handle /chats command"""
    try:
        await handle_chats_command(event, client)
        logger.info(f"Chats command used by user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in chats command: {e}")
        await event.respond("❌ Erreur lors de l'affichage des chats. Veuillez réessayer.")

@client.on(events.NewMessage(pattern="/help"))
async def help_command(event):
    """Handle /help command"""
    try:
        help_message = """
📋 **Aide TeleFeed**

**Commandes disponibles :**

🔹 `/start` - Démarrer le bot
🔹 `/connect` - Connecter un numéro de téléphone
🔹 `/valide` - Valider votre licence premium
🔹 `/payer` - Effectuer un paiement (une semaine/un mois)
🔹 `/redirection` - Gérer les redirections entre chats
🔹 `/transformation` - Modifier le contenu des messages
🔹 `/whitelist` - Filtrer les messages autorisés
🔹 `/blacklist` - Ignorer certains messages
🔹 `/chats` - Afficher les chats associés à un numéro
🔹 `/deposer` - Déposer des fichiers (premium uniquement)
🔹 `/help` - Afficher cette aide

**Support :**
Pour toute question ou problème, contactez l'administrateur.
        """
        await event.respond(help_message)
        logger.info(f"Help requested by user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await event.respond("❌ Une erreur est survenue. Veuillez réessayer.")

# Admin commands
@client.on(events.NewMessage(pattern="/admin"))
async def admin_command(event):
    """Handle /admin command"""
    await handle_admin_commands(event, client)

@client.on(events.NewMessage(pattern="/confirm"))
async def confirm_command(event):
    """Handle /confirm command"""
    await handle_admin_commands(event, client)

@client.on(events.NewMessage(pattern="/generate"))
async def generate_command(event):
    """Handle /generate command"""
    await handle_admin_commands(event, client)

@client.on(events.NewMessage(pattern="/users"))
async def users_command(event):
    """Handle /users command"""
    await handle_admin_commands(event, client)

@client.on(events.NewMessage(pattern="/stats"))
async def stats_command(event):
    """Handle /stats command"""
    await handle_admin_commands(event, client)

@client.on(events.NewMessage(pattern="/sessions"))
async def sessions_command(event):
    """Handle /sessions command"""
    await handle_admin_commands(event, client)

@client.on(events.NewMessage)
async def handle_unknown_command(event):
    """Handle unknown commands and verification codes"""
    # First check if it's a verification code
    if await handle_verification_code(event, client):
        return  # Message was handled as verification code

    # Check if it's a redirection format (ID - ID)
    if event.text and " - " in event.text:
        parts = event.text.split(" - ")
        if len(parts) == 2 and len(parts[0].strip()) > 5 and len(parts[1].strip()) > 5:
            from bot.redirection import handle_redirection_format
            await handle_redirection_format(event, client, parts[0].strip(), parts[1].strip())
            return

    # Check if it's a license code (starts with user ID)
    if event.text and event.text.strip() and event.text.strip().startswith(str(event.sender_id)):
        if await validate_license_code(event, client, event.text.strip()):
            return  # License was validated successfully

    # Then check for unknown commands
    if event.text and event.text.startswith('/') and not any(event.text.startswith(cmd) for cmd in ['/start', '/connect', '/valide', '/payer', '/deposer', '/redirection', '/transformation', '/whitelist', '/blacklist', '/chats', '/help', '/admin', '/confirm', '/generate', '/users', '/stats', '/sessions']):
        await event.respond("❓ Commande non reconnue. Tapez /help pour voir les commandes disponibles.")

# Surveillance automatique pour Render
@client.on(events.NewMessage(pattern="Kouamé Appolinaire tu es là ?"))
async def surveillance_response(event):
    """Handle automatic surveillance from Render"""
    try:
        await event.respond("oui bb")
        logger.info(f"Surveillance response sent to {event.sender_id}")
    except Exception as e:
        logger.error(f"Error in surveillance response: {e}")

async def start_bot():
    """Start the bot and handle all initialization"""
    try:
        # Start client with bot token
        await client.start(bot_token=BOT_TOKEN)
        logger.info("🚀 Bot TeleFeed démarré avec succès!")
        print("Bot lancé !")

        # Initialize session manager and restore sessions
        from bot.session_manager import session_manager
        await session_manager.restore_all_sessions()

        # Wait a moment for sessions to be fully restored
        await asyncio.sleep(2)

        # Setup message redirection handlers AFTER sessions are restored
        from bot.message_handler import message_redirector
        await message_redirector.setup_redirection_handlers()

        await client.run_until_disconnected()

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

def start_bot_sync():
    """Synchronous wrapper to start the bot"""
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the bot
        loop.run_until_complete(start_bot())
    except Exception as e:
        logger.error(f"Error in start_bot_sync: {e}")
        raise

if __name__ == "__main__":
    start_bot_sync()
