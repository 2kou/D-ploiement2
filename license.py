from telethon import events
import logging
import os
from bot.database import store_license, is_user_licensed

logger = logging.getLogger(__name__)

async def check_license(event, client):
    """
    Validate user license
    License format: starts with user_id and must be over 20 characters
    """
    try:
        user_id = str(event.sender_id)
        
        # Check if user is admin (owner always has access)
        admin_id = os.getenv("ADMIN_ID")
        if admin_id and str(user_id) == admin_id:
            await event.respond("✅ **Accès administrateur confirmé !**\n\n👑 Vous avez un accès complet à toutes les fonctionnalités.\n\nEn tant que propriétaire, toutes les fonctionnalités premium sont débloquées.")
            logger.info(f"Admin access confirmed for user {user_id}")
            return
        
        # Request license from user
        await event.respond("🔐 **Validation de licence**\n\nVeuillez entrer votre code de licence :")
        
        # For now, inform user to send license in next message
        await event.respond("📝 **Instructions :**\n\nEnvoyez votre code de licence dans le prochain message.")
        
        # Note: License validation will be handled by the message handler
        # This is a simplified approach - in production, you'd use conversation state
            
        # This function now only handles the /valide command
        # License validation will be handled by a separate function
                
    except Exception as e:
        logger.error(f"Error in license validation: {e}")
        await event.respond("❌ Erreur lors de la validation de licence. Veuillez réessayer.")

def validate_license_format(license_code, user_id):
    """
    Validate license format
    Rules: must start with user_id and be over 20 characters
    New format: [ID_USER] + [moitié de l'ID] + [date] + [heure] + [5 lettres aléatoires]
    """
    if not license_code:
        return False
    
    # Check if license starts with user_id
    if not license_code.startswith(user_id):
        return False
    
    # Validate exact format: [ID_USER] + [moitié_ID] + [date] + [5_lettres] + [heure]
    user_id_str = str(user_id)
    half_id = user_id_str[:len(user_id_str)//2]
    
    # Expected format parts
    expected_start = f"{user_id_str}{half_id}"
    
    # Check if it starts with user_id + half_id
    if not license_code.startswith(expected_start):
        return False
    
    # Calculate expected total length
    # user_id + half_id + date(8) + letters(5) + time(4)
    expected_length = len(user_id_str) + len(half_id) + 8 + 5 + 4
    
    # Check exact length
    if len(license_code) != expected_length:
        return False
    
    return True

async def validate_license_code(event, client, license_code):
    """
    Validate a license code sent by user
    """
    try:
        user_id = str(event.sender_id)
        
        # Check if user is admin (owner always has access)
        admin_id = os.getenv("ADMIN_ID")
        if admin_id and str(user_id) == admin_id:
            await event.respond("✅ **Accès administrateur confirmé !**\n\n👑 Vous avez un accès complet à toutes les fonctionnalités.\n\nEn tant que propriétaire, toutes les fonctionnalités premium sont débloquées.")
            logger.info(f"Admin access confirmed for user {user_id}")
            return True
        
        # Validate license format
        if validate_license_format(license_code, user_id):
            await event.respond("✅ **Licence validée avec succès !**\n\n🎉 Accès premium débloqué.\n\nVous pouvez maintenant utiliser toutes les fonctionnalités premium du bot.")
            logger.info(f"License validated successfully for user {user_id}")
            
            # Store license validation
            await store_license(user_id, license_code)
            return True
            
        else:
            # Check if license belongs to another user
            if license_code and not license_code.startswith(user_id):
                await event.respond("❌ **Licence volée**\n\n⚠️ Cette licence ne vous appartient pas.\n\nVeuillez contacter l'administrateur pour obtenir une licence valide.")
                logger.warning(f"Stolen license attempt by user {user_id}: {license_code}")
            else:
                await event.respond("❌ **Licence invalide**\n\n⚠️ La licence fournie est invalide.\n\nVeuillez contacter l'administrateur pour obtenir une licence valide.")
                logger.warning(f"Invalid license attempt by user {user_id}: {license_code}")
            
            # Notify admin of invalid license attempt (but skip if user is admin)
            admin_id = int(os.getenv("ADMIN_ID", "0"))
            if admin_id and str(user_id) != str(admin_id):
                await client.send_message(admin_id, f"⚠️ **Tentative de licence invalide**\n\nUtilisateur: {user_id}\nLicence: {license_code}")
            
            return False
            
    except Exception as e:
        logger.error(f"Error validating license code: {e}")
        await event.respond("❌ Erreur lors de la validation de licence. Veuillez réessayer.")
        return False
