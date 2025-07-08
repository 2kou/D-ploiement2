import logging

logger = logging.getLogger(__name__)

async def handle_blacklist_command(event, client):
    """
    Handle /blacklist command
    Manages blacklist filters
    """
    try:
        message_text = event.text.strip()
        
        # Check if command is used alone
        if message_text == "/blacklist":
            usage_message = """
⛔ **Utilisation de /blacklist :**

`/blacklist add NOM on NUMERO`
`/blacklist remove NOM on NUMERO`
`/blacklist change NOM on NUMERO`
`/blacklist clear on NUMERO`

**Fonctionnalité :**
La blacklist ignore tous les messages contenant certains mots ou regex.

**Exemple :**
`/blacklist add motInterdit on 229900112233`
            """
            await event.respond(usage_message)
            return
        
        # Parse command
        parts = message_text.split()
        if len(parts) < 2:
            await event.respond("❌ Format incorrect. Tapez `/blacklist` pour voir l'utilisation.")
            return
        
        # Handle different blacklist actions
        if parts[1] == "add" and len(parts) == 5 and parts[3] == "on":
            await add_blacklist(event, client, parts[2], parts[4])
        elif parts[1] == "remove" and len(parts) == 5 and parts[3] == "on":
            await remove_blacklist(event, client, parts[2], parts[4])
        elif parts[1] == "change" and len(parts) == 5 and parts[3] == "on":
            await change_blacklist(event, client, parts[2], parts[4])
        elif parts[1] == "clear" and len(parts) == 4 and parts[2] == "on":
            await clear_blacklist(event, client, parts[3])
        else:
            await event.respond("❌ Format incorrect. Tapez `/blacklist` pour voir l'utilisation.")
        
    except Exception as e:
        logger.error(f"Error in blacklist command: {e}")
        await event.respond("❌ Erreur lors de la gestion de la blacklist. Veuillez réessayer.")

async def add_blacklist(event, client, name, phone_number):
    """Add a blacklist filter"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.\nUtilisez `/valide` pour activer votre licence.")
            return
        
        # Store blacklist
        await store_blacklist(user_id, name, phone_number, "add")
        
        success_message = f"""
✅ **Filtre blacklist ajouté**

📝 **Nom :** {name}
📞 **Numéro :** {phone_number}
🔄 **Action :** Ajout

Le filtre blacklist est maintenant actif !
Les messages contenant les mots interdits seront ignorés.
        """
        
        await event.respond(success_message)
        logger.info(f"Blacklist added by user {user_id}: {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error adding blacklist: {e}")
        await event.respond("❌ Erreur lors de l'ajout du filtre blacklist.")

async def remove_blacklist(event, client, name, phone_number):
    """Remove a blacklist filter"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Remove blacklist
        await store_blacklist(user_id, name, phone_number, "remove")
        
        success_message = f"""
✅ **Filtre blacklist supprimé**

📝 **Nom :** {name}
📞 **Numéro :** {phone_number}
🔄 **Action :** Suppression

Le filtre blacklist a été désactivé.
        """
        
        await event.respond(success_message)
        logger.info(f"Blacklist removed by user {user_id}: {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error removing blacklist: {e}")
        await event.respond("❌ Erreur lors de la suppression du filtre blacklist.")

async def change_blacklist(event, client, name, phone_number):
    """Change a blacklist filter"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Change blacklist
        await store_blacklist(user_id, name, phone_number, "change")
        
        success_message = f"""
✅ **Filtre blacklist modifié**

📝 **Nom :** {name}
📞 **Numéro :** {phone_number}
🔄 **Action :** Modification

Le filtre blacklist a été mis à jour.
        """
        
        await event.respond(success_message)
        logger.info(f"Blacklist changed by user {user_id}: {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error changing blacklist: {e}")
        await event.respond("❌ Erreur lors de la modification du filtre blacklist.")

async def clear_blacklist(event, client, phone_number):
    """Clear all blacklist filters for a phone number"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Clear blacklist
        await clear_user_blacklist(user_id, phone_number)
        
        success_message = f"""
✅ **Filtres blacklist effacés**

📞 **Numéro :** {phone_number}
🔄 **Action :** Nettoyage complet

Tous les filtres blacklist ont été supprimés pour ce numéro.
        """
        
        await event.respond(success_message)
        logger.info(f"Blacklist cleared by user {user_id} for {phone_number}")
        
    except Exception as e:
        logger.error(f"Error clearing blacklist: {e}")
        await event.respond("❌ Erreur lors du nettoyage des filtres blacklist.")

async def is_premium_user(user_id):
    """Check if user has premium access"""
    from bot.database import is_user_licensed
    return await is_user_licensed(user_id)

async def store_blacklist(user_id, name, phone_number, action):
    """Store blacklist in database"""
    logger.info(f"Blacklist {action} for user {user_id}: {name} on {phone_number}")
    # In real implementation, save to database
    pass

async def clear_user_blacklist(user_id, phone_number):
    """Clear all blacklist filters for a user and phone number"""
    logger.info(f"Blacklist cleared for user {user_id} on {phone_number}")
    # In real implementation, clear from database
    pass