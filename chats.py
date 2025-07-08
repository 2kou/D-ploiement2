import logging

logger = logging.getLogger(__name__)

async def handle_chats_command(event, client):
    """
    Handle /chats command
    Shows all chats associated with a phone number
    """
    try:
        message_text = event.text.strip()
        
        # Check if command is used alone
        if message_text == "/chats":
            usage_message = """
📡 **Menu d'aide pour les Chats**

Utilisez cette commande pour obtenir tous les ID de chats à utiliser avec d'autres commandes. Vous pouvez utiliser un filtre pour indiquer à TeleFeed quel type de chats afficher.

**Arguments de commande :**
`/chats NUMERO_TELEPHONE`
`/chats FILTRE NUMERO_TELEPHONE`

**Obtenir tous les chats de 2759205517 :**
`/chats 2759205517`

**Obtenir des chats spécifiques de 2759205517 :**
`/chats user 2759205517`
`/chats bot 2759205517`
`/chats group 2759205517`
`/chats channel 2759205517`
            """
            await event.respond(usage_message)
            return
        
        # Parse command
        parts = message_text.split()
        if len(parts) < 2:
            await event.respond("❌ Format incorrect. Tapez `/chats` pour voir l'utilisation.")
            return
        
        # Handle different chat filters
        if len(parts) == 2:
            # Show all chats
            await show_all_chats(event, client, parts[1])
        elif len(parts) == 3:
            # Show specific chat type
            chat_type = parts[1]
            phone_number = parts[2]
            
            if chat_type in ["user", "bot", "group", "channel"]:
                await show_chats_by_type(event, client, chat_type, phone_number)
            else:
                await event.respond("❌ Type de chat invalide. Types supportés : user, bot, group, channel")
        else:
            await event.respond("❌ Format incorrect. Tapez `/chats` pour voir l'utilisation.")
        
    except Exception as e:
        logger.error(f"Error in chats command: {e}")
        await event.respond("❌ Erreur lors de l'affichage des chats. Veuillez réessayer.")

async def show_all_chats(event, client, phone_number):
    """Show all chats for a phone number"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.\nUtilisez `/valide` pour activer votre licence.")
            return
        
        # Get real chats from active connection
        chats = await get_real_user_chats(user_id, phone_number)
        
        if not chats:
            message = f"""
📡 **Chats pour {phone_number}**

Aucun chat trouvé pour ce numéro.

💡 **Astuce :** Assurez-vous que le numéro est correctement connecté avec `/connect`.
            """
        else:
            # Group chats by type
            users = [c for c in chats if c['type'] == 'user']
            bots = [c for c in chats if c['type'] == 'bot']
            groups = [c for c in chats if c['type'] == 'group']
            channels = [c for c in chats if c['type'] == 'channel']
            
            message = f"""
📡 **Chats pour {phone_number}**

👤 **Utilisateurs :** {len(users)}
🤖 **Bots :** {len(bots)}
👥 **Groupes :** {len(groups)}
📢 **Canaux :** {len(channels)}

📊 **Total :** {len(chats)} chat(s)

💡 **Astuce :** Utilisez `/chats TYPE {phone_number}` pour voir les détails avec IDs.
            """
        
        await event.respond(message)
        logger.info(f"All chats shown for user {user_id} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error showing all chats: {e}")
        await event.respond("❌ Erreur lors de l'affichage des chats.")

async def show_chats_by_type(event, client, chat_type, phone_number):
    """Show chats of a specific type for a phone number"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Get real chats from active connection
        chats = await get_real_user_chats_by_type(user_id, phone_number, chat_type)
        logger.info(f"Retrieved {len(chats)} chats of type {chat_type} for user {user_id}")
        
        # Get type emoji and name
        type_info = {
            'user': {'emoji': '👤', 'name': 'Utilisateurs'},
            'bot': {'emoji': '🤖', 'name': 'Bots'},
            'group': {'emoji': '👥', 'name': 'Groupes'},
            'channel': {'emoji': '📢', 'name': 'Canaux'}
        }
        
        emoji = type_info[chat_type]['emoji']
        name = type_info[chat_type]['name']
        
        if not chats:
            message = f"""
{emoji} **{name} pour {phone_number}**

Aucun {chat_type} trouvé pour ce numéro.
            """
        else:
            chat_list = "\n".join([f"• {c['name']} - ID: `{c['id']}` - {c['status']}" for c in chats])
            message = f"""
{emoji} **{name} pour {phone_number}**

{chat_list}

📊 **Total :** {len(chats)} {chat_type}(s)
            """
        
        await event.respond(message)
        logger.info(f"Chats of type {chat_type} shown for user {user_id} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error showing chats by type: {e}")
        await event.respond("❌ Erreur lors de l'affichage des chats.")

async def is_premium_user(user_id):
    """Check if user has premium access"""
    from bot.database import is_user_licensed
    return await is_user_licensed(user_id)

async def get_real_user_chats(user_id, phone_number):
    """Get all real chats for a user and phone number from active connection"""
    try:
        from bot.connection import active_connections
        
        # Check if user has an active connection for this phone
        if user_id not in active_connections:
            logger.warning(f"No active connection found for user {user_id}")
            return []
            
        connection_data = active_connections[user_id]
        active_client = connection_data.get('client')
        connection_phone = connection_data.get('phone', '').replace('+', '')
        target_phone = phone_number.replace('+', '')
        
        if not active_client or not active_client.is_connected():
            logger.warning(f"Client not connected for user {user_id}")
            return []
            
        # Check if the phone numbers match
        if connection_phone != target_phone:
            logger.warning(f"Phone mismatch: connected {connection_phone}, requested {target_phone}")
            return []
        
        # Update session activity
        from bot.session_manager import session_manager
        await session_manager.update_session_activity(user_id, connection_data.get('phone'))
            
        # Get all dialogs (chats) from the active client
        chats = []
        async for dialog in active_client.iter_dialogs():
            try:
                chat_entity = dialog.entity
                chat_type = 'user'
                
                # Determine chat type based on entity type
                entity_type = type(chat_entity).__name__
                
                if entity_type == 'User':
                    if getattr(chat_entity, 'bot', False):
                        chat_type = 'bot'
                    else:
                        chat_type = 'user'
                elif entity_type == 'Chat':
                    chat_type = 'group'
                elif entity_type == 'Channel':
                    if getattr(chat_entity, 'megagroup', False):
                        chat_type = 'group'
                    elif getattr(chat_entity, 'broadcast', False):
                        chat_type = 'channel'
                    elif getattr(chat_entity, 'gigagroup', False):
                        chat_type = 'group'
                    else:
                        chat_type = 'channel'
                
                # Get chat name safely
                chat_name = 'Chat inconnu'
                if hasattr(chat_entity, 'title') and chat_entity.title:
                    chat_name = chat_entity.title
                elif hasattr(chat_entity, 'first_name'):
                    chat_name = chat_entity.first_name
                    if hasattr(chat_entity, 'last_name') and chat_entity.last_name:
                        chat_name += f' {chat_entity.last_name}'
                elif hasattr(chat_entity, 'username') and chat_entity.username:
                    chat_name = f'@{chat_entity.username}'
                else:
                    chat_name = f'Chat {chat_entity.id}'
                
                chat_data = {
                    'id': chat_entity.id,
                    'name': chat_name,
                    'type': chat_type,
                    'username': getattr(chat_entity, 'username', None)
                }
                chats.append(chat_data)
                
            except Exception as e:
                logger.error(f"Error processing chat entity: {str(e)}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                continue
            
        return chats
        
    except Exception as e:
        logger.error(f"Error getting real chats: {e}")
        # Fallback to database chats
        from bot.database import get_user_chats_data
        return await get_user_chats_data(user_id, phone_number)

async def get_real_user_chats_by_type(user_id, phone_number, chat_type):
    """Get real chats of a specific type for a user and phone number"""
    try:
        logger.info(f"Getting chats of type '{chat_type}' for user {user_id}")
        all_chats = await get_real_user_chats(user_id, phone_number)
        logger.info(f"Retrieved {len(all_chats)} total chats")
        
        filtered_chats = []
        for chat in all_chats:
            if chat.get('type') == chat_type:
                filtered_chats.append(chat)
        
        logger.info(f"Filtered to {len(filtered_chats)} chats of type '{chat_type}'")
        return filtered_chats
        
    except Exception as e:
        logger.error(f"Error in get_real_user_chats_by_type: {e}")
        return []