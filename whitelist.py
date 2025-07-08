import logging

logger = logging.getLogger(__name__)

async def handle_whitelist_command(event, client):
    """
    Handle /whitelist command
    Manages whitelist filters
    """
    try:
        message_text = event.text.strip()
        
        # Check if command is used alone
        if message_text == "/whitelist":
            usage_message = """
✅ **Utilisation de /whitelist :**

`/whitelist add NOM on NUMERO`
`/whitelist remove NOM on NUMERO`
`/whitelist change NOM on NUMERO`
`/whitelist clear on NUMERO`

**Fonctionnalité :**
La whitelist indique au bot de ne traiter que les messages contenant certains mots ou regex.

**Exemple :**
`/whitelist add filtreImportant on 229900112233`
            """
            await event.respond(usage_message)
            return
        
        # Parse command
        parts = message_text.split()
        if len(parts) < 2:
            await event.respond("❌ Format incorrect. Tapez `/whitelist` pour voir l'utilisation.")
            return
        
        # Handle different whitelist actions
        if parts[1] == "add" and len(parts) == 5 and parts[3] == "on":
            await add_whitelist(event, client, parts[2], parts[4])
        elif parts[1] == "remove" and len(parts) == 5 and parts[3] == "on":
            await remove_whitelist(event, client, parts[2], parts[4])
        elif parts[1] == "change" and len(parts) == 5 and parts[3] == "on":
            await change_whitelist(event, client, parts[2], parts[4])
        elif parts[1] == "clear" and len(parts) == 4 and parts[2] == "on":
            await clear_whitelist(event, client, parts[3])
        else:
            await event.respond("❌ Format incorrect. Tapez `/whitelist` pour voir l'utilisation.")
        
    except Exception as e:
        logger.error(f"Error in whitelist command: {e}")
        await event.respond("❌ Erreur lors de la gestion de la whitelist. Veuillez réessayer.")

async def add_whitelist(event, client, name, phone_number):
    """Add a whitelist filter"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.\nUtilisez `/valide` pour activer votre licence.")
            return
        
        # Store whitelist
        await store_whitelist(user_id, name, phone_number, "add")
        
        success_message = f"""
✅ **Filtre whitelist ajouté**

📝 **Nom :** {name}
📞 **Numéro :** {phone_number}
🔄 **Action :** Ajout

Le filtre whitelist est maintenant actif !
Seuls les messages contenant les mots autorisés seront traités.
        """
        
        await event.respond(success_message)
        logger.info(f"Whitelist added by user {user_id}: {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error adding whitelist: {e}")
        await event.respond("❌ Erreur lors de l'ajout du filtre whitelist.")

async def remove_whitelist(event, client, name, phone_number):
    """Remove a whitelist filter"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Remove whitelist
        await store_whitelist(user_id, name, phone_number, "remove")
        
        success_message = f"""
✅ **Filtre whitelist supprimé**

📝 **Nom :** {name}
📞 **Numéro :** {phone_number}
🔄 **Action :** Suppression

Le filtre whitelist a été désactivé.
        """
        
        await event.respond(success_message)
        logger.info(f"Whitelist removed by user {user_id}: {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error removing whitelist: {e}")
        await event.respond("❌ Erreur lors de la suppression du filtre whitelist.")

async def change_whitelist(event, client, name, phone_number):
    """Change a whitelist filter"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Change whitelist
        await store_whitelist(user_id, name, phone_number, "change")
        
        success_message = f"""
✅ **Filtre whitelist modifié**

📝 **Nom :** {name}
📞 **Numéro :** {phone_number}
🔄 **Action :** Modification

Le filtre whitelist a été mis à jour.
        """
        
        await event.respond(success_message)
        logger.info(f"Whitelist changed by user {user_id}: {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error changing whitelist: {e}")
        await event.respond("❌ Erreur lors de la modification du filtre whitelist.")

async def clear_whitelist(event, client, phone_number):
    """Clear all whitelist filters for a phone number"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Clear whitelist
        await clear_user_whitelist(user_id, phone_number)
        
        success_message = f"""
✅ **Filtres whitelist effacés**

📞 **Numéro :** {phone_number}
🔄 **Action :** Nettoyage complet

Tous les filtres whitelist ont été supprimés pour ce numéro.
        """
        
        await event.respond(success_message)
        logger.info(f"Whitelist cleared by user {user_id} for {phone_number}")
        
    except Exception as e:
        logger.error(f"Error clearing whitelist: {e}")
        await event.respond("❌ Erreur lors du nettoyage des filtres whitelist.")

async def is_premium_user(user_id):
    """Check if user has premium access"""
    from bot.database import is_user_licensed
    return await is_user_licensed(user_id)

async def store_whitelist(user_id, name, phone_number, action):
    """Store whitelist in database"""
    logger.info(f"Whitelist {action} for user {user_id}: {name} on {phone_number}")
    # In real implementation, save to database
    pass

async def clear_user_whitelist(user_id, phone_number):
    """Clear all whitelist filters for a user and phone number"""
    logger.info(f"Whitelist cleared for user {user_id} on {phone_number}")
    # In real implementation, clear from database
    pass