#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Téléfoot COMPLET pour Render.com
Version avec tous les composants TeleFeed et interfaces
"""

import asyncio
import signal
import sys
import os
import threading
import time
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import AuthKeyError, FloodWaitError
from flask import Flask, jsonify, request
import logging
import json
import requests
from telethon import events

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration depuis les variables d'environnement
API_ID = int(os.getenv('API_ID', '29177661'))
API_HASH = os.getenv('API_HASH', 'a8639172fa8d35dbfd8ea46286d349ab')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))
PORT = int(os.getenv('PORT', '10000'))

# Import des modules locaux
try:
    from user_manager import UserManager
    from advanced_user_manager import AdvancedUserManager
    from bot_handlers import BotHandlers
    from button_interface import ButtonInterface
    from telefeed_commands import register_all_handlers, telefeed_manager
    from keep_alive import keep_alive
except ImportError as e:
    logger.error(f"Erreur d'import: {e}")
    # Fallback vers les composants de base
    from user_manager import UserManager
    from bot_handlers import BotHandlers

# Application Flask
app = Flask(__name__)

# Variables globales
bot_instance = None
bot_running = False
flask_server = None

class CompleteTelefootBot:
    """Bot Téléfoot complet avec tous les composants"""
    
    def __init__(self):
        self.client = None
        self.user_manager = None
        self.advanced_user_manager = None
        self.handlers = None
        self.button_interface = None
        self.running = False
        self.telefeed_active = False
        self.reactivation_count = 0
        self.auto_reactivation_active = True
    
    async def initialize(self):
        """Initialise le bot avec tous les composants"""
        try:
            # Création du client
            self.client = TelegramClient('bot_session', API_ID, API_HASH)
            await self.client.start(bot_token=BOT_TOKEN)
            
            # Vérification de la connexion
            me = await self.client.get_me()
            logger.info(f"Bot connecté: @{me.username} ({me.id})")
            
            # Gestionnaires d'utilisateurs
            self.user_manager = UserManager()
            try:
                self.advanced_user_manager = AdvancedUserManager()
            except:
                logger.warning("AdvancedUserManager non disponible")
            
            # Handlers principaux
            self.handlers = BotHandlers(self.client, self.user_manager)
            
            # Interface à boutons
            try:
                self.button_interface = ButtonInterface(self.client, self.user_manager)
            except:
                logger.warning("ButtonInterface non disponible")
            
            # TeleFeed
            try:
                await register_all_handlers(self.client, ADMIN_ID, API_ID, API_HASH)
                await self.restore_telefeed_sessions()
                self.telefeed_active = True
                logger.info("TeleFeed activé")
            except Exception as e:
                logger.warning(f"TeleFeed non disponible: {e}")
            
            # Système de réactivation automatique
            await self.setup_auto_reactivation()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation: {e}")
            return False
    
    async def restore_telefeed_sessions(self):
        """Restaure les sessions TeleFeed"""
        try:
            from telefeed_commands import telefeed_manager
            
            restored_count = 0
            total_sessions = len(telefeed_manager.sessions)
            
            for phone_number, session_data in telefeed_manager.sessions.items():
                if isinstance(session_data, dict) and session_data.get('connected'):
                    try:
                        session_name = f"telefeed_{phone_number}"
                        
                        if os.path.exists(f"{session_name}.session"):
                            client = TelegramClient(session_name, API_ID, API_HASH)
                            await client.connect()
                            
                            if await client.is_user_authorized():
                                telefeed_manager.clients[phone_number] = client
                                await telefeed_manager.setup_redirection_handlers(client, phone_number)
                                restored_count += 1
                                logger.info(f"Session restaurée: {phone_number}")
                            else:
                                await client.disconnect()
                    except Exception as e:
                        logger.error(f"Erreur restauration {phone_number}: {e}")
            
            telefeed_manager.save_all_data()
            logger.info(f"Sessions restaurées: {restored_count}/{total_sessions}")
            
        except Exception as e:
            logger.error(f"Erreur restauration TeleFeed: {e}")
    
    async def start(self):
        """Démarre le bot"""
        if not await self.initialize():
            logger.error("Échec d'initialisation")
            return False
        
        self.running = True
        logger.info("Bot démarré")
        
        # Boucle principale
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Arrêt demandé")
        finally:
            await self.stop()
        
        return True
    
    async def stop(self):
        """Arrête le bot"""
        self.running = False
        
        try:
            if self.telefeed_active:
                from telefeed_commands import telefeed_manager
                for client in telefeed_manager.clients.values():
                    try:
                        await client.disconnect()
                    except:
                        pass
        except:
            pass
        
        if self.client:
            try:
                await self.client.disconnect()
            except:
                pass
        
        logger.info("Bot arrêté")
    
    async def setup_auto_reactivation(self):
        """Configure le système de réactivation automatique"""
        try:
            # Handler pour le message "réactiver le bot automatique"
            @self.client.on(events.NewMessage(pattern=r'(?i)réactiver le bot automatique'))
            async def reactivation_handler(event):
                await self.handle_reactivation_message(event)
            
            # Handler pour surveiller les déconnexions
            @self.client.on(events.Raw)
            async def connection_handler(event):
                await self.monitor_connection_status()
            
            logger.info("Système de réactivation automatique configuré")
            
        except Exception as e:
            logger.error(f"Erreur configuration réactivation: {e}")
    
    async def handle_reactivation_message(self, event):
        """Traite le message de réactivation automatique"""
        try:
            # Répondre "ok" comme demandé
            await event.respond("ok")
            
            self.reactivation_count += 1
            logger.info(f"Réactivation #{self.reactivation_count} - Réponse 'ok' envoyée")
            
            # Redémarrer les composants si nécessaire
            await self.restart_components()
            
            # Notifier l'admin
            await self.notify_admin_reactivation()
            
        except Exception as e:
            logger.error(f"Erreur traitement réactivation: {e}")
    
    async def restart_components(self):
        """Redémarre les composants du bot"""
        try:
            logger.info("Redémarrage des composants...")
            
            # Restaurer les sessions TeleFeed
            if self.telefeed_active:
                await self.restore_telefeed_sessions()
            
            # Vérifier la connexion
            if not self.client.is_connected():
                await self.client.connect()
                
            logger.info("Composants redémarrés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur redémarrage composants: {e}")
    
    async def notify_admin_reactivation(self):
        """Notifie l'admin de la réactivation"""
        try:
            message = (
                f"🔄 **Réactivation automatique effectuée**\n"
                f"⏰ Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📊 Nombre de réactivations: {self.reactivation_count}\n"
                f"✅ Réponse 'ok' envoyée"
            )
            
            await self.client.send_message(ADMIN_ID, message)
            logger.info("Notification admin envoyée")
            
        except Exception as e:
            logger.error(f"Erreur notification admin: {e}")
    
    async def monitor_connection_status(self):
        """Surveille l'état de la connexion"""
        try:
            if not self.client.is_connected() and self.auto_reactivation_active:
                logger.warning("Connexion perdue - Tentative de reconnexion...")
                await self.client.connect()
                
        except Exception as e:
            logger.error(f"Erreur surveillance connexion: {e}")

# Endpoints Flask
@app.route('/')
def health_check():
    """Endpoint de santé"""
    global bot_instance, bot_running
    
    status = {
        "service": "Téléfoot Bot Complet",
        "status": "running" if bot_running else "starting",
        "bot_connected": bot_instance.client.is_connected() if bot_instance and bot_instance.client else False,
        "telefeed_active": bot_instance.telefeed_active if bot_instance else False,
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(status)

@app.route('/status')
def bot_status():
    """Status détaillé du bot"""
    global bot_instance
    
    if not bot_instance:
        return jsonify({"error": "Bot non initialisé"}), 500
    
    status = {
        "bot_running": bot_instance.running,
        "client_connected": bot_instance.client.is_connected() if bot_instance.client else False,
        "telefeed_active": bot_instance.telefeed_active,
        "reactivation_count": bot_instance.reactivation_count,
        "auto_reactivation_active": bot_instance.auto_reactivation_active,
        "components": {
            "user_manager": bot_instance.user_manager is not None,
            "advanced_user_manager": bot_instance.advanced_user_manager is not None,
            "handlers": bot_instance.handlers is not None,
            "button_interface": bot_instance.button_interface is not None
        }
    }
    
    return jsonify(status)

@app.route('/reactivate', methods=['POST'])
def trigger_reactivation():
    """Endpoint pour déclencher la réactivation automatique"""
    global bot_instance
    
    try:
        if not bot_instance or not bot_instance.client:
            return jsonify({"error": "Bot non disponible"}), 500
        
        # Envoyer le message de réactivation automatique
        async def send_reactivation():
            try:
                await bot_instance.client.send_message(
                    ADMIN_ID, 
                    "réactiver le bot automatique"
                )
                logger.info("Message de réactivation envoyé via endpoint")
                return True
            except Exception as e:
                logger.error(f"Erreur envoi réactivation: {e}")
                return False
        
        # Exécuter en arrière-plan
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(send_reactivation())
        loop.close()
        
        if success:
            return jsonify({
                "message": "Message de réactivation envoyé",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Échec envoi message"}), 500
            
    except Exception as e:
        logger.error(f"Erreur endpoint réactivation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health-monitor')
def health_monitor():
    """Endpoint spécial pour Render.com - Détecte et réactive automatiquement"""
    global bot_instance
    
    try:
        if not bot_instance:
            # Déclencher réactivation automatique
            return jsonify({
                "status": "bot_offline",
                "action": "reactivation_triggered",
                "message": "Bot hors ligne - Réactivation en cours"
            }), 503
        
        bot_connected = bot_instance.client.is_connected() if bot_instance.client else False
        
        if not bot_connected:
            # Bot déconnecté - Déclencher réactivation
            try:
                requests.post('http://localhost:10000/reactivate', timeout=5)
                logger.info("Réactivation déclenchée par health-monitor")
            except:
                pass
                
            return jsonify({
                "status": "bot_disconnected", 
                "action": "reactivation_triggered",
                "reactivation_count": bot_instance.reactivation_count
            }), 503
        
        # Bot OK
        return jsonify({
            "status": "healthy",
            "bot_connected": True,
            "telefeed_active": bot_instance.telefeed_active,
            "uptime": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur health-monitor: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/restart', methods=['POST'])
def restart_bot():
    """Redémarre le bot"""
    global bot_instance
    
    try:
        if bot_instance:
            asyncio.create_task(bot_instance.stop())
        
        # Redémarrer en arrière-plan
        def restart_async():
            asyncio.new_event_loop().run_until_complete(start_bot_async())
        
        threading.Thread(target=restart_async, daemon=True).start()
        
        return jsonify({"message": "Redémarrage en cours"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

async def start_bot_async():
    """Démarre le bot en mode async"""
    global bot_instance, bot_running
    
    bot_instance = CompleteTelefootBot()
    bot_running = True
    
    try:
        await bot_instance.start()
    except Exception as e:
        logger.error(f"Erreur bot: {e}")
        bot_running = False
    finally:
        bot_running = False

def start_flask_server():
    """Démarre le serveur Flask"""
    global flask_server
    
    logger.info(f"Démarrage serveur Flask sur port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

def main():
    """Point d'entrée principal"""
    logger.info("Démarrage du bot Téléfoot complet")
    
    # Démarrer Flask en arrière-plan
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    
    # Attendre que Flask démarre
    time.sleep(2)
    
    # Démarrer le bot
    try:
        asyncio.run(start_bot_async())
    except KeyboardInterrupt:
        logger.info("Arrêt demandé")
    except Exception as e:
        logger.error(f"Erreur principale: {e}")

if __name__ == "__main__":
    main()
