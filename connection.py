import logging
import re
import os
from telethon import TelegramClient
from telethon.errors import PhoneNumberInvalidError, FloodWaitError

logger = logging.getLogger(__name__)

# Store active connection sessions
active_connections = {}

async def handle_connect(event, client):
    """
    Handle /connect command
    Connects a phone number to TeleFeed
    """
    try:
        message_text = event.text.strip()
        
        # Check if command is used alone
        if message_text == "/connect":
            usage_message = """
🔗 **Utilisation de /connect :**

`/connect NUMERO`

**Exemple :**
`/connect 229900112233`

**Remarque :**
- Ajoutez toujours l'indicatif pays (ex : 229 pour Bénin).
- Lors de la saisie du code reçu par Telegram, ajoutez 'aa' devant.
  → Ex : code reçu 12345 → entrer : aa12345
            """
            await event.respond(usage_message)
            return
        
        # Extract phone number from command
        parts = message_text.split()
        if len(parts) != 2:
            await event.respond("❌ Format incorrect. Utilisez : `/connect NUMERO`")
            return
        
        phone_number = parts[1]
        
        # Validate phone number format
        if not re.match(r'^\d{10,15}$', phone_number):
            await event.respond("❌ Numéro de téléphone invalide. Utilisez le format : indicatif + numéro (ex: 229900112233)")
            return
        
        user_id = event.sender_id
        
        # Format phone number for Telegram API
        formatted_phone = f"+{phone_number}"
        
        await event.respond("🔄 **Initiation de la connexion...**\n\nTentative de connexion en cours...")
        
        # Create a new client session for this phone number
        session_name = f"session_{user_id}_{phone_number}"
        
        try:
            # Create new client for the phone number
            new_client = TelegramClient(
                session_name,
                int(os.getenv("API_ID")),
                os.getenv("API_HASH")
            )
            
            await new_client.connect()
            
            # Send code request
            result = await new_client.send_code_request(formatted_phone)
            
            # Store the connection session
            active_connections[user_id] = {
                'client': new_client,
                'phone': formatted_phone,
                'phone_code_hash': result.phone_code_hash,
                'session_name': session_name
            }
            
            success_message = f"""
✅ **Code de vérification envoyé !**

📞 **Numéro :** {formatted_phone}
📨 **Statut :** Code envoyé par Telegram

⚠️ **Important :**
- Vérifiez votre Telegram pour le code de vérification
- Quand vous le recevez, ajoutez 'aa' devant le code
- Exemple : code reçu 12345 → entrez : **aa12345**
- Le bot attendra votre prochain message avec le code

✍️ **Prochaine étape :** Envoyez le code avec 'aa' devant
            """
            
            await event.respond(success_message)
            logger.info(f"Verification code sent for user {user_id} with phone {formatted_phone}")
            
        except PhoneNumberInvalidError:
            await event.respond("❌ **Numéro de téléphone invalide**\n\nVeuillez vérifier le format du numéro et réessayer.")
            logger.error(f"Invalid phone number: {formatted_phone}")
            
        except FloodWaitError as e:
            await event.respond(f"❌ **Limite de tentatives atteinte**\n\nVeuillez attendre {e.seconds} secondes avant de réessayer.")
            logger.error(f"Flood wait error: {e.seconds} seconds")
            
        except Exception as e:
            await event.respond("❌ **Erreur lors de l'envoi du code**\n\nVeuillez réessayer dans quelques minutes.")
            logger.error(f"Error sending code: {e}")
        
    except Exception as e:
        logger.error(f"Error in connect command: {e}")
        await event.respond("❌ Erreur lors de la connexion. Veuillez réessayer.")

async def handle_verification_code(event, client):
    """
    Handle verification code input
    """
    try:
        user_id = event.sender_id
        message_text = event.text.strip()
        
        # Check if user has an active connection attempt
        if user_id not in active_connections:
            return False  # Not a verification code
        
        # Check if message starts with 'aa' (verification code format)
        if not message_text.startswith('aa'):
            return False  # Not a verification code
        
        # Extract the actual code
        verification_code = message_text[2:]  # Remove 'aa' prefix
        
        if not verification_code.isdigit():
            await event.respond("❌ **Code invalide**\n\nLe code doit contenir uniquement des chiffres après 'aa'.")
            return True
        
        connection_data = active_connections[user_id]
        new_client = connection_data['client']
        phone = connection_data['phone']
        phone_code_hash = connection_data['phone_code_hash']
        
        try:
            # Sign in with the verification code
            await new_client.sign_in(phone, verification_code, phone_code_hash=phone_code_hash)
            
            # Connection successful
            success_message = f"""
🎉 **Connexion réussie !**

📞 **Numéro :** {phone}
✅ **Statut :** Connecté avec succès

🚀 **Fonctionnalités débloquées :**
- Redirection de messages
- Gestion des chats
- Toutes les fonctionnalités premium

💡 **Prochaines étapes :**
- Utilisez `/chats {phone.replace('+', '')}` pour voir vos chats
- Configurez vos redirections avec `/redirection`
            """
            
            await event.respond(success_message)
            
            # Store the successful connection
            await store_successful_connection(user_id, phone)
            
            # Keep the client active for chat operations and redirections
            active_connections[user_id] = {
                'client': new_client,
                'phone': phone,
                'connected': True,
                'session_name': connection_data['session_name']
            }
            
            # Store session in persistent database
            from bot.session_manager import session_manager
            await session_manager.store_session(user_id, phone, connection_data['session_name'])
            
            # Setup message redirection handlers for existing redirections
            from bot.message_handler import message_redirector
            await message_redirector.setup_redirection_handlers()
            
            logger.info(f"Successful connection for user {user_id} with phone {phone}")
            return True
            
        except Exception as e:
            await event.respond("❌ **Code de vérification incorrect**\n\nVeuillez vérifier le code et réessayer avec le format : aa12345")
            logger.error(f"Verification failed for user {user_id}: {e}")
            return True
            
    except Exception as e:
        logger.error(f"Error handling verification code: {e}")
        return False

async def store_successful_connection(user_id, phone_number):
    """
    Store successful connection
    """
    from bot.database import store_connection
    await store_connection(user_id, phone_number)
    logger.info(f"Successful connection stored for user {user_id}: {phone_number}")

async def get_user_connections(user_id):
    """
    Get user's connected phone numbers
    In a real implementation, this would fetch from a database
    """
    # In real implementation, fetch from database
    return []

async def is_phone_connected(user_id, phone_number):
    """
    Check if a phone number is connected for a user
    In a real implementation, this would check a database
    """
    # In real implementation, check database
    return False