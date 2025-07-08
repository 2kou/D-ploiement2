import os
import logging
from telethon import events

logger = logging.getLogger(__name__)

async def process_payment(event, client, subscription_type="générique"):
    """
    Process payment request
    Forwards payment request to administrator
    """
    try:
        user_id = event.sender_id
        username = event.sender.username if hasattr(event.sender, 'username') else "Non défini"
        first_name = event.sender.first_name if hasattr(event.sender, 'first_name') else "Non défini"
        
        # Get admin ID from environment
        admin_id = int(os.getenv("ADMIN_ID", "0"))
        
        if not admin_id:
            await event.respond("❌ Erreur de configuration. Veuillez contacter le support.")
            logger.error("ADMIN_ID not configured")
            return
        
        # Create payment request message
        payment_message = f"""
💰 **Nouvelle demande de paiement**

👤 **Utilisateur :** {first_name}
🆔 **ID :** {user_id}
📱 **Username :** @{username}
⏰ **Date :** {event.date.strftime('%Y-%m-%d %H:%M:%S')}
📦 **Type d'abonnement :** {subscription_type}

💳 **Action requise :** Traitement du paiement
        """
        
        # Send to admin
        await client.send_message(admin_id, payment_message)
        
        # Confirm to user
        confirmation_message = """
✅ **Demande de paiement envoyée**

📤 Votre demande a été transmise à l'administrateur.
⏱️ Vous recevrez une réponse dans les plus brefs délais.

💡 **Prochaines étapes :**
1. L'administrateur examinera votre demande
2. Vous recevrez les instructions de paiement
3. Une fois le paiement confirmé, votre licence sera activée

Merci pour votre patience !
        """
        
        await event.respond(confirmation_message)
        logger.info(f"Payment request forwarded to admin for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        await event.respond("❌ Erreur lors du traitement de la demande de paiement. Veuillez réessayer.")

async def confirm_payment(admin_id, user_id, client):
    """
    Confirm payment (to be called by admin)
    """
    try:
        # Generate license for user
        license_code = generate_license(user_id)
        
        # Send license to user
        license_message = f"""
🎉 **Paiement confirmé !**

✅ Votre paiement a été validé avec succès.
🔐 Voici votre licence premium :

`{license_code}`

📝 **Instructions :**
1. Tapez /valide
2. Collez votre code de licence
3. Profitez de vos accès premium !

Merci pour votre confiance ! 🚀
        """
        
        await client.send_message(user_id, license_message)
        logger.info(f"License sent to user {user_id} after payment confirmation")
        
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")

def generate_license(user_id):
    """
    Generate a license code for the user
    Format: [ID_USER] + [moitié de l'ID] + [date] + [heure] + [5 lettres aléatoires]
    """
    import random
    import string
    from datetime import datetime
    
    # Get current date and time
    now = datetime.now()
    date_part = now.strftime('%Y%m%d')  # Format: 20241207
    time_part = now.strftime('%H%M')    # Format: 1425
    
    # Get half of user ID (first half)
    user_id_str = str(user_id)
    half_id = user_id_str[:len(user_id_str)//2]
    
    # Generate 5 random letters from French alphabet
    french_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    random_letters = ''.join(random.choices(french_letters, k=5))
    
    # Create license: [ID_USER] + [moitié_ID] + [date] + [5_lettres] + [heure]
    license_code = f"{user_id_str}{half_id}{date_part}{random_letters}{time_part}"
    
    # Log the generation for admin tracking
    logger.info(f"License generated for user {user_id}: {license_code[:15]}... (Format: ID+half+date+letters+time)")
    
    return license_code
