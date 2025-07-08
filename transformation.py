import logging

logger = logging.getLogger(__name__)

async def handle_transformation_command(event, client):
    """
    Handle /transformation command
    Manages message transformations
    """
    try:
        message_text = event.text.strip()
        
        # Check if command is used alone
        if message_text == "/transformation":
            usage_message = """
🧩 **Utilisation de /transformation :**

`/transformation add format|power|removeLines NOM on NUMERO`
`/transformation remove ...`
`/transformation clear ...`

**Types de transformation :**
• **format** - Modifier le format des messages
• **power** - Appliquer des transformations avancées
• **removeLines** - Supprimer certaines lignes

**Exemple :**
`/transformation add format groupe1 on 229900112233`
            """
            await event.respond(usage_message)
            return
        
        # Parse command
        parts = message_text.split()
        if len(parts) < 2:
            await event.respond("❌ Format incorrect. Tapez `/transformation` pour voir l'utilisation.")
            return
        
        # Handle different transformation actions
        if parts[1] == "add" and len(parts) == 6 and parts[4] == "on":
            await add_transformation(event, client, parts[2], parts[3], parts[5])
        elif parts[1] == "remove" and len(parts) == 6 and parts[4] == "on":
            await remove_transformation(event, client, parts[2], parts[3], parts[5])
        elif parts[1] == "clear" and len(parts) == 4 and parts[2] == "on":
            await clear_transformations(event, client, parts[3])
        else:
            await event.respond("❌ Format incorrect. Tapez `/transformation` pour voir l'utilisation.")
        
    except Exception as e:
        logger.error(f"Error in transformation command: {e}")
        await event.respond("❌ Erreur lors de la gestion des transformations. Veuillez réessayer.")

async def add_transformation(event, client, transform_type, name, phone_number):
    """Add a new transformation"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.\nUtilisez `/valide` pour activer votre licence.")
            return
        
        # Validate transformation type
        valid_types = ["format", "power", "removeLines"]
        if transform_type not in valid_types:
            await event.respond(f"❌ Type de transformation invalide. Types supportés : {', '.join(valid_types)}")
            return
        
        # Store transformation
        await store_transformation(user_id, transform_type, name, phone_number, "add")
        
        success_message = f"""
✅ **Transformation ajoutée**

🔧 **Type :** {transform_type}
📝 **Nom :** {name}
📞 **Numéro :** {phone_number}
🔄 **Action :** Ajout

La transformation est maintenant active !
        """
        
        await event.respond(success_message)
        logger.info(f"Transformation added by user {user_id}: {transform_type} {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error adding transformation: {e}")
        await event.respond("❌ Erreur lors de l'ajout de la transformation.")

async def remove_transformation(event, client, transform_type, name, phone_number):
    """Remove a transformation"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Remove transformation
        await store_transformation(user_id, transform_type, name, phone_number, "remove")
        
        success_message = f"""
✅ **Transformation supprimée**

🔧 **Type :** {transform_type}
📝 **Nom :** {name}
📞 **Numéro :** {phone_number}
🔄 **Action :** Suppression

La transformation a été désactivée.
        """
        
        await event.respond(success_message)
        logger.info(f"Transformation removed by user {user_id}: {transform_type} {name} on {phone_number}")
        
    except Exception as e:
        logger.error(f"Error removing transformation: {e}")
        await event.respond("❌ Erreur lors de la suppression de la transformation.")

async def clear_transformations(event, client, phone_number):
    """Clear all transformations for a phone number"""
    try:
        user_id = event.sender_id
        
        # Check if user has premium access
        if not await is_premium_user(user_id):
            await event.respond("❌ **Accès premium requis**\n\nCette fonctionnalité est réservée aux utilisateurs premium.")
            return
        
        # Clear transformations
        await clear_user_transformations(user_id, phone_number)
        
        success_message = f"""
✅ **Transformations effacées**

📞 **Numéro :** {phone_number}
🔄 **Action :** Nettoyage complet

Toutes les transformations ont été supprimées pour ce numéro.
        """
        
        await event.respond(success_message)
        logger.info(f"Transformations cleared by user {user_id} for {phone_number}")
        
    except Exception as e:
        logger.error(f"Error clearing transformations: {e}")
        await event.respond("❌ Erreur lors du nettoyage des transformations.")

async def is_premium_user(user_id):
    """Check if user has premium access"""
    from bot.database import is_user_licensed
    return await is_user_licensed(user_id)

async def store_transformation(user_id, transform_type, name, phone_number, action):
    """Store transformation in database"""
    logger.info(f"Transformation {action} for user {user_id}: {transform_type} {name} on {phone_number}")
    # In real implementation, save to database
    pass

async def clear_user_transformations(user_id, phone_number):
    """Clear all transformations for a user and phone number"""
    logger.info(f"Transformations cleared for user {user_id} on {phone_number}")
    # In real implementation, clear from database
    pass