import os
import logging
from telethon import events
from bot.payment import generate_license
from bot.database import store_license

logger = logging.getLogger(__name__)

async def handle_admin_commands(event, client):
    """
    Handle admin commands
    Only accessible to admin users
    """
    try:
        user_id = event.sender_id
        admin_id = int(os.getenv("ADMIN_ID", "0"))
        
        # Check if user is admin
        if user_id != admin_id:
            await event.respond("❌ Accès refusé. Commande réservée aux administrateurs.")
            return
        
        message_text = event.text.strip().lower()
        
        if message_text == "/admin":
            await show_admin_help(event, client)
        elif message_text.startswith("/confirm"):
            await handle_confirm_payment(event, client)
        elif message_text.startswith("/generate"):
            await handle_generate_license(event, client)
        elif message_text.startswith("/users"):
            await handle_list_users(event, client)
        elif message_text.startswith("/stats"):
            await handle_stats(event, client)
        elif message_text.startswith("/sessions"):
            await handle_sessions(event, client)
        else:
            await event.respond("❓ Commande admin non reconnue. Tapez /admin pour voir les commandes disponibles.")
            
    except Exception as e:
        logger.error(f"Error in admin command: {e}")
        await event.respond("❌ Erreur lors de l'exécution de la commande admin.")

async def show_admin_help(event, client):
    """Show admin help menu"""
    admin_help = """
🔧 **PANNEAU ADMINISTRATEUR**

📋 **Commandes disponibles :**

💰 **Gestion des paiements :**
• `/confirm USER_ID` - Confirmer paiement et envoyer licence
• `/generate USER_ID` - Générer une licence manuelle

👥 **Gestion des utilisateurs :**
• `/users` - Liste des utilisateurs inscrits
• `/stats` - Statistiques du bot
• `/sessions` - Sessions connectées et redirections actives

📝 **Formats d'exemple :**
• `/confirm 1190237801` - Confirme paiement pour l'utilisateur
• `/generate 1190237801` - Génère licence pour l'utilisateur

⚡ **Raccourcis :**
• Répondez "✅" à un message de demande de paiement
• Le bot confirmera automatiquement le paiement
    """
    await event.respond(admin_help)

async def handle_confirm_payment(event, client):
    """Handle payment confirmation"""
    try:
        parts = event.text.split()
        if len(parts) != 2:
            await event.respond("❌ Format : `/confirm USER_ID`\n\nExemple : `/confirm 1190237801`")
            return
        
        target_user_id = parts[1]
        
        # Generate and send license
        license_code = generate_license(target_user_id)
        
        # Store license in database
        await store_license(target_user_id, license_code)
        
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
        
        await client.send_message(int(target_user_id), license_message)
        
        # Confirm to admin
        admin_confirmation = f"""
✅ **Paiement confirmé avec succès**

👤 **Utilisateur :** {target_user_id}
🔐 **Licence générée :** {license_code[:20]}...
📤 **Licence envoyée :** Oui

L'utilisateur peut maintenant utiliser toutes les fonctionnalités premium.
        """
        
        await event.respond(admin_confirmation)
        logger.info(f"Payment confirmed for user {target_user_id} by admin")
        
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        await event.respond("❌ Erreur lors de la confirmation du paiement.")

async def handle_generate_license(event, client):
    """Generate license manually"""
    try:
        parts = event.text.split()
        if len(parts) != 2:
            await event.respond("❌ Format : `/generate USER_ID`\n\nExemple : `/generate 1190237801`")
            return
        
        target_user_id = parts[1]
        
        # Generate license
        license_code = generate_license(target_user_id)
        
        # Store license in database
        await store_license(target_user_id, license_code)
        
        # Show license to admin
        admin_message = f"""
🔐 **Licence générée**

👤 **Utilisateur :** {target_user_id}
🔑 **Code de licence :**
`{license_code}`

📋 **Actions possibles :**
• Envoyez cette licence à l'utilisateur
• La licence est déjà activée en base de données
• L'utilisateur peut l'utiliser avec /valide
        """
        
        await event.respond(admin_message)
        logger.info(f"Manual license generated for user {target_user_id}")
        
    except Exception as e:
        logger.error(f"Error generating license: {e}")
        await event.respond("❌ Erreur lors de la génération de la licence.")

async def handle_list_users(event, client):
    """List registered users"""
    try:
        from bot.database import load_data
        
        data = load_data()
        licenses = data.get("licenses", {})
        connections = data.get("connections", {})
        
        user_list = f"""
👥 **LISTE DES UTILISATEURS**

📊 **Statistiques :**
• {len(licenses)} utilisateurs avec licence
• {len(connections)} utilisateurs connectés

🔐 **Utilisateurs avec licence :**
"""
        
        for user_id, license_data in licenses.items():
            status = "✅ Actif" if license_data.get("active", False) else "❌ Inactif"
            user_list += f"• {user_id} - {status}\n"
        
        if not licenses:
            user_list += "Aucun utilisateur avec licence\n"
        
        user_list += "\n📱 **Utilisateurs connectés :**\n"
        for user_id, user_connections in connections.items():
            phone_count = len(user_connections)
            user_list += f"• {user_id} - {phone_count} numéro(s)\n"
        
        if not connections:
            user_list += "Aucun utilisateur connecté"
        
        await event.respond(user_list)
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        await event.respond("❌ Erreur lors de la récupération des utilisateurs.")

async def handle_stats(event, client):
    """Show bot statistics"""
    try:
        from bot.database import load_data
        
        data = load_data()
        
        total_licenses = len(data.get("licenses", {}))
        active_licenses = sum(1 for license_data in data.get("licenses", {}).values() 
                            if license_data.get("active", False))
        total_connections = len(data.get("connections", {}))
        total_redirections = sum(len(redirections) for redirections in data.get("redirections", {}).values())
        
        stats_message = f"""
📊 **STATISTIQUES DU BOT**

👥 **Utilisateurs :**
• Total licences : {total_licenses}
• Licences actives : {active_licenses}
• Connexions : {total_connections}

⚙️ **Fonctionnalités :**
• Redirections configurées : {total_redirections}
• Transformations : {len(data.get("transformations", {}))}
• Listes blanches : {len(data.get("whitelists", {}))}
• Listes noires : {len(data.get("blacklists", {}))}

🚀 **Statut :** Bot opérationnel
        """
        
        await event.respond(stats_message)
        
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await event.respond("❌ Erreur lors de la récupération des statistiques.")

async def handle_sessions(event, client):
    """Show active sessions and redirections"""
    try:
        from bot.database import load_data
        from bot.connection import active_connections
        
        data = load_data()
        connections = data.get("connections", {})
        redirections = data.get("redirections", {})
        
        # Build sessions message
        sessions_message = "📱 **SESSIONS ACTIVES**\n\n"
        
        # Active connection attempts (temporary sessions)
        if active_connections:
            sessions_message += "🔄 **Connexions en cours :**\n"
            for user_id, conn_data in active_connections.items():
                phone = conn_data.get('phone', 'Inconnu')
                sessions_message += f"• Utilisateur {user_id} - {phone}\n"
            sessions_message += "\n"
        else:
            sessions_message += "🔄 **Connexions en cours :** Aucune\n\n"
        
        # Established connections
        if connections:
            sessions_message += "✅ **Connexions établies :**\n"
            for user_id, user_connections in connections.items():
                sessions_message += f"👤 **Utilisateur {user_id} :**\n"
                for conn in user_connections:
                    phone = conn.get('phone', 'Inconnu')
                    connected_at = conn.get('connected_at', 'Date inconnue')
                    replaced_at = conn.get('replaced_at', '')
                    status = "🟢 Actif" if conn.get('active', True) else "🔴 Inactif"
                    sessions_message += f"  📞 {phone} - {status}\n"
                    if replaced_at:
                        sessions_message += f"     🔄 Restauré le: {replaced_at}\n"
                    else:
                        sessions_message += f"     ⏰ Connecté le: {connected_at[:19]}\n"
                sessions_message += "\n"
        else:
            sessions_message += "✅ **Connexions établies :** Aucune\n\n"
        
        # Redirections actives
        sessions_message += "🔀 **REDIRECTIONS ACTIVES**\n\n"
        
        if redirections:
            total_redirections = 0
            for user_id, user_redirections in redirections.items():
                if user_redirections:
                    sessions_message += f"👤 **Utilisateur {user_id} :**\n"
                    for name, redir_data in user_redirections.items():
                        if redir_data.get('active', True):
                            phone = redir_data.get('phone', 'Inconnu')
                            created_at = redir_data.get('created_at', 'Date inconnue')
                            replaced_at = redir_data.get('replaced_at', '')
                            replacement_info = redir_data.get('replacement_info', '')
                            
                            sessions_message += f"  🔀 {name} → {phone}\n"
                            if replaced_at and replacement_info:
                                sessions_message += f"     🔄 Restauré le: {replaced_at}{replacement_info}\n"
                            else:
                                sessions_message += f"     ⏰ Créé le: {created_at[:19]}\n"
                            total_redirections += 1
                    sessions_message += "\n"
            
            if total_redirections == 0:
                sessions_message += "Aucune redirection active\n"
        else:
            sessions_message += "Aucune redirection configurée\n"
        
        # Summary
        total_active_connections = sum(len(conns) for conns in connections.values())
        total_temp_connections = len(active_connections)
        total_active_redirections = sum(
            sum(1 for redir in user_redirections.values() if redir.get('active', True))
            for user_redirections in redirections.values()
        )
        
        sessions_message += f"\n📊 **RÉSUMÉ :**\n"
        sessions_message += f"• Connexions temporaires : {total_temp_connections}\n"
        sessions_message += f"• Connexions établies : {total_active_connections}\n" 
        sessions_message += f"• Redirections actives : {total_active_redirections}\n"
        
        await event.respond(sessions_message)
        logger.info("Sessions information displayed to admin")
        
    except Exception as e:
        logger.error(f"Error showing sessions: {e}")
        await event.respond("❌ Erreur lors de la récupération des sessions.")