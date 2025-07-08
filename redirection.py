import logging
from telethon import events
from telethon.errors import ChannelInvalidError, UsernameNotOccupiedError

logger = logging.getLogger(__name__)

async def handle_redirection_command(event, client):
    """
    Handle /redirection command
    Manages redirections between chats
    """
    try:
        message_text = event.text.strip()
        
        # Check if command is used alone
        if message_text == "/redirection":
            usage_message = """
🔁 **Menu d'aide pour les Redirections**

Commande utilisée pour configurer les redirections. Vous devez utiliser la commande /chats pour obtenir les ID des canaux/groupes ou utilisateurs à utiliser avec cette commande.

**Arguments de commande :**
`/redirection ACTION IDREDIRECTION on NUMERO_TELEPHONE`
`/redirection NUMERO_TELEPHONE`

**Ajouter, modifier ou supprimer des redirections groupe1 :**
`/redirection add groupe1 on 2759205517`
`/redirection change groupe1 on 2759205517`
`/redirection remove groupe1 on 2759205517`

**Afficher les redirections actives :**
`/redirection 2759205517`
            """
            await event.respond(usage_message)
            return
        
        # Parse command
        parts = message_text.split()
        if len(parts) < 2:
            await event.respond("❌ Format incorrect. Tapez `/redirection` pour voir l'utilisation.")
            return
        
        # Handle different redirection actions
        if parts[1] == "add" and len(parts) == 5 and parts[3] == "on":
            await add_redirection(event, client, parts[2], parts[4])
        elif parts[1] == "remove" and len(parts) == 5 and parts[3] == "on":
            await remove_redirection(event, client, parts[2], parts[4])
        elif parts[1] == "change" and len(parts) == 5 and parts[3] == "on":
            await change_redirection(event, client, parts[2], parts[4])
        elif len(parts) == 2 and parts[1].isdigit():
            await show_redirections(event, client, parts[1])
        else:
            await event.respond("❌ Format incorrect. Tapez `/redirection` pour voir l'utilisation.")
        
    except Exception as e:
        logger.error(f"Error in redirection command: {e}")
        await event.respond("❌ Erreur lors de la gestion des redirections. Veuillez réessayer.")

async def add_redirection(event, client, name, phone_number):
    """Add a new redirection"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.\nUtilisez `/valide` pour activer votre licence.")
            return
        
        # Store pending redirection (waiting for channel IDs)
        await store_pending_redirection(user_id, name, phone_number)
        
        # Ask for channel IDs format
        format_message = f"""
📋 **Configuration de la redirection "{name}"**

📞 **Numéro connecté :** {phone_number}
🔄 **Nom de la redirection :** {name}

**Maintenant, envoyez le format de redirection :**
`ID_CANAL_SOURCE - ID_CANAL_DESTINATION`

**Exemple :**
`1002370795564 - 1002682552255`

➡️ **Envoyez votre format maintenant :**
        """
        
        await event.respond(format_message)
        logger.info(f"Redirection format requested for user {user_id}: {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error adding redirection: {e}")
        await event.respond("❌ Erreur lors de l'ajout de la redirection.")

async def remove_redirection(event, client, name, phone_number):
    """Remove a redirection"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Remove redirection
        await store_redirection(user_id, name, phone_number, "remove")
        
        success_message = f"""
✅ **Redirection supprimée**

📝 **Nom :** {name}
📞 **Numéro :** {phone_number}
🔄 **Action :** Suppression

La redirection a été désactivée.
        """
        
        await event.respond(success_message)
        logger.info(f"Redirection removed by user {user_id}: {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error removing redirection: {e}")
        await event.respond("❌ Erreur lors de la suppression de la redirection.")

async def change_redirection(event, client, name, phone_number):
    """Change a redirection"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Check if redirection exists
        redirections = await get_user_redirections(user_id, phone_number)
        existing_redirect = None
        for r in redirections:
            if r['name'] == name:
                existing_redirect = r
                break
        
        if not existing_redirect:
            await event.respond(f"❌ **Redirection introuvable**\n\nAucune redirection nommée '{name}' trouvée pour le numéro {phone_number}.")
            return
        
        # Store pending redirection for modification (waiting for new channel IDs)
        await store_pending_redirection(user_id, name, phone_number)
        
        # Ask for new channel IDs format
        format_message = f"""
📋 **Modification de la redirection "{name}"**

📞 **Numéro connecté :** {phone_number}
🔄 **Nom de la redirection :** {name}
📺 **Configuration actuelle :** {existing_redirect.get('source_id', 'N/A')} → {existing_redirect.get('destination_id', 'N/A')}

**Maintenant, envoyez le nouveau format de redirection :**
`ID_CANAL_SOURCE - ID_CANAL_DESTINATION`

**Exemple :**
`1002370795564 - 1002682552255`

➡️ **Envoyez votre nouveau format maintenant :**
        """
        
        await event.respond(format_message)
        logger.info(f"Redirection modification requested for user {user_id}: {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error changing redirection: {e}")
        await event.respond("❌ Erreur lors de la modification de la redirection.")

async def show_redirections(event, client, phone_number):
    """Show active redirections for a phone number"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Get redirections
        redirections = await get_user_redirections(user_id, phone_number)
        
        if not redirections:
            message = f"""
📋 **Redirections actives pour {phone_number}**

Aucune redirection active pour ce numéro.

💡 **Astuce :** Utilisez `/redirection add NOM on {phone_number}` pour créer une redirection.
            """
        else:
            redirection_list = []
            for r in redirections:
                channel_name = r.get('channel_name', r['name'])
                status = r.get('status', 'Actif')
                redirection_list.append(f"• **{r['name']}** → 📺 {channel_name} - {status}")
            
            message = f"""
📋 **Redirections actives pour {phone_number}**

{chr(10).join(redirection_list)}

🔄 **Total :** {len(redirections)} redirection(s)
            """
        
        await event.respond(message)
        logger.info(f"Redirections shown for user {user_id} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error showing redirections: {e}")
        await event.respond("❌ Erreur lors de l'affichage des redirections.")

async def is_premium_user(user_id):
    """Check if user has premium access"""
    from bot.database import is_user_licensed
    return await is_user_licensed(user_id)

async def store_redirection(user_id, name, phone_number, action, channel_name=None, source_id=None, destination_id=None):
    """Store redirection in database"""
    from bot.database import store_redirection as db_store_redirection
    await db_store_redirection(user_id, name, phone_number, action, channel_name, source_id, destination_id)
    logger.info(f"Redirection {action} for user {user_id}: {name} -> {channel_name or name}")

async def get_user_redirections(user_id, phone_number):
    """Get user redirections from database"""
    from bot.database import get_user_redirections as db_get_redirections
    return await db_get_redirections(user_id, phone_number)

async def get_channel_name(client, phone_number, fallback_name):
    """Get the actual channel/chat name for display"""
    try:
        # Try to get channel/chat info using the connected session
        # In a real implementation, you would:
        # 1. Use the user's connected session for this phone number
        # 2. Search for the channel/chat by name or ID
        # 3. Return the actual channel title
        
        # For now, return a formatted name based on the fallback
        # This would be replaced with actual Telegram API calls
        
        if fallback_name.lower().startswith('canal'):
            return f"📺 Canal {fallback_name.replace('canal', '').strip()}"
        elif fallback_name.lower().startswith('groupe'):
            return f"👥 Groupe {fallback_name.replace('groupe', '').strip()}"
        elif fallback_name.lower().startswith('chat'):
            return f"💬 Chat {fallback_name.replace('chat', '').strip()}"
        else:
            return f"📺 {fallback_name}"
            
    except Exception as e:
        logger.error(f"Error getting channel name: {e}")
        return f"📺 {fallback_name}"

async def store_pending_redirection(user_id, name, phone_number):
    """Store pending redirection waiting for channel IDs"""
    from bot.database import store_pending_redirection as db_store_pending
    await db_store_pending(user_id, name, phone_number)

async def handle_redirection_format(event, client, source_id, destination_id):
    """Handle redirection format input (ID - ID)"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Get pending redirection
        pending = await get_pending_redirection(user_id)
        
        if not pending:
            await event.respond("❌ **Aucune redirection en attente**\n\nVeuillez d'abord utiliser `/redirection add NOM on NUMERO`.")
            return
        
        name = pending['name']
        phone_number = pending['phone_number']
        
        # Get channel name for display
        channel_name = await get_channel_name(client, phone_number, name)
        
        # Store complete redirection with channel IDs
        await store_redirection(user_id, name, phone_number, "add", channel_name, source_id, destination_id)
        
        # Clear pending redirection
        await clear_pending_redirection(user_id)
        
        # Set up message redirection handler
        from bot.message_handler import message_redirector
        handler_added = await message_redirector.add_redirection_handler(user_id, name, source_id, destination_id)
        
        success_message = f"""
✅ **Redirection configurée avec succès**

📝 **Nom :** {name}
📺 **Canal de destination :** {channel_name}
📞 **Numéro source :** {phone_number}
🔄 **Canal source :** {source_id}
🎯 **Canal destination :** {destination_id}

{"🔄 **Transfert automatique :** Activé" if handler_added else "⚠️ **Transfert automatique :** Erreur d'activation"}

La redirection est maintenant active !
        """
        
        await event.respond(success_message)
        logger.info(f"Redirection configured for user {user_id}: {name} ({source_id} -> {destination_id})")
        
    except Exception as e:
        logger.error(f"Error handling redirection format: {e}")
        await event.respond("❌ Erreur lors de la configuration de la redirection.")

async def get_pending_redirection(user_id):
    """Get pending redirection for user"""
    from bot.database import get_pending_redirection as db_get_pending
    return await db_get_pending(user_id)

async def clear_pending_redirection(user_id):
    """Clear pending redirection for user"""
    from bot.database import clear_pending_redirection as db_clear_pending
    await db_clear_pending(user_id)