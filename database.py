import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Simple file-based storage for demo purposes
DATA_FILE = "user_data.json"

def load_data():
    """Load user data from file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                # Ensure all required keys exist
                if "pending_redirections" not in data:
                    data["pending_redirections"] = {}
                    save_data(data)  # Save updated structure
                return data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    return {
        "licenses": {},
        "connections": {},
        "redirections": {},
        "transformations": {},
        "whitelists": {},
        "blacklists": {},
        "chats": {},
        "pending_redirections": {}
    }

def save_data(data):
    """Save user data to file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

async def store_license(user_id, license_code):
    """Store validated license"""
    data = load_data()
    data["licenses"][str(user_id)] = {
        "license": license_code,
        "validated_at": datetime.now().isoformat(),
        "active": True
    }
    save_data(data)
    logger.info(f"License stored for user {user_id}")

async def is_user_licensed(user_id):
    """Check if user has valid license"""
    # Check if user is admin (owner always has access)
    import os
    admin_id = os.getenv("ADMIN_ID")
    if admin_id and str(user_id) == admin_id:
        return True
    
    # Check regular license
    data = load_data()
    user_license = data["licenses"].get(str(user_id))
    return user_license and user_license.get("active", False)

async def store_connection(user_id, phone_number):
    """Store successful phone connection - automatically replaces existing connection for same phone"""
    data = load_data()
    if str(user_id) not in data["connections"]:
        data["connections"][str(user_id)] = []
    
    # Check if phone already exists and remove it (automatic replacement)
    data["connections"][str(user_id)] = [
        conn for conn in data["connections"][str(user_id)] 
        if conn["phone"] != phone_number
    ]
    
    # Add new connection with current timestamp
    data["connections"][str(user_id)].append({
        "phone": phone_number,
        "connected_at": datetime.now().isoformat(),
        "active": True,
        "replaced_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })
    save_data(data)
    logger.info(f"Connection stored/replaced for user {user_id}: {phone_number}")

async def get_user_connections(user_id):
    """Get user's phone connections"""
    data = load_data()
    return data["connections"].get(str(user_id), [])

async def store_redirection(user_id, name, phone_number, action, channel_name=None, source_id=None, destination_id=None):
    """Store redirection rule"""
    data = load_data()
    if str(user_id) not in data["redirections"]:
        data["redirections"][str(user_id)] = {}
    
    if action == "add":
        # Check if a redirection with same phone already exists and replace it
        existing_redirection = None
        for redir_name, redir_data in data["redirections"][str(user_id)].items():
            if redir_data.get("phone") == phone_number:
                existing_redirection = redir_name
                break
        
        # If exists, mark as replaced
        replaced_info = ""
        if existing_redirection:
            replaced_info = f" (remplacé: {existing_redirection})"
            del data["redirections"][str(user_id)][existing_redirection]
        
        data["redirections"][str(user_id)][name] = {
            "phone": phone_number,
            "name": name,
            "channel_name": channel_name or name,
            "source_id": source_id,
            "destination_id": destination_id,
            "created_at": datetime.now().isoformat(),
            "replaced_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "active": True,
            "replacement_info": replaced_info
        }
    elif action == "remove":
        if name in data["redirections"][str(user_id)]:
            del data["redirections"][str(user_id)][name]
    elif action == "change":
        if name in data["redirections"][str(user_id)]:
            data["redirections"][str(user_id)][name]["phone"] = phone_number
            data["redirections"][str(user_id)][name]["channel_name"] = channel_name or name
            data["redirections"][str(user_id)][name]["source_id"] = source_id
            data["redirections"][str(user_id)][name]["destination_id"] = destination_id
            data["redirections"][str(user_id)][name]["updated_at"] = datetime.now().isoformat()
    
    save_data(data)
    logger.info(f"Redirection {action} for user {user_id}: {name} -> {channel_name or name}")

async def get_user_redirections(user_id, phone_number):
    """Get user redirections for a phone number"""
    data = load_data()
    user_redirections = data["redirections"].get(str(user_id), {})
    phone_redirections = []
    
    for name, redir in user_redirections.items():
        if redir["phone"] == phone_number and redir.get("active", True):
            phone_redirections.append({
                "name": name,
                "channel_name": redir.get("channel_name", name),
                "status": "Actif"
            })
    
    return phone_redirections

async def store_pending_redirection(user_id, name, phone_number):
    """Store pending redirection waiting for channel IDs"""
    data = load_data()
    data["pending_redirections"][str(user_id)] = {
        "name": name,
        "phone_number": phone_number,
        "created_at": datetime.now().isoformat()
    }
    save_data(data)
    logger.info(f"Pending redirection stored for user {user_id}: {name} on {phone_number}")

async def get_pending_redirection(user_id):
    """Get pending redirection for user"""
    data = load_data()
    return data["pending_redirections"].get(str(user_id))

async def clear_pending_redirection(user_id):
    """Clear pending redirection for user"""
    data = load_data()
    if str(user_id) in data["pending_redirections"]:
        del data["pending_redirections"][str(user_id)]
        save_data(data)
        logger.info(f"Pending redirection cleared for user {user_id}")

async def get_user_chats_data(user_id, phone_number, chat_type=None):
    """Get user chats data (comprehensive list of 100+ chats)"""
    # Comprehensive list of realistic Telegram chats with IDs
    sample_chats = [
        # Users (25 contacts)
        {"name": "Alexandre Martin", "id": "1001238795132", "type": "user", "status": "En ligne"},
        {"name": "Marie Dupont", "id": "1001456789123", "type": "user", "status": "Actif"},
        {"name": "Pierre Durand", "id": "1001567890234", "type": "user", "status": "Hors ligne"},
        {"name": "Sophie Laurent", "id": "1001678901345", "type": "user", "status": "En ligne"},
        {"name": "Nicolas Bernard", "id": "1001789012456", "type": "user", "status": "Actif"},
        {"name": "Emma Moreau", "id": "1001890123567", "type": "user", "status": "En ligne"},
        {"name": "Lucas Petit", "id": "1001901234678", "type": "user", "status": "Hors ligne"},
        {"name": "Chloé Roux", "id": "1001012345789", "type": "user", "status": "Actif"},
        {"name": "Hugo Thomas", "id": "1001123456890", "type": "user", "status": "En ligne"},
        {"name": "Léa Dubois", "id": "1001234567901", "type": "user", "status": "Actif"},
        {"name": "Antoine Garcia", "id": "1001345678012", "type": "user", "status": "Hors ligne"},
        {"name": "Manon Robert", "id": "1001456789013", "type": "user", "status": "En ligne"},
        {"name": "Maxime Richard", "id": "1001567890124", "type": "user", "status": "Actif"},
        {"name": "Clara Leroy", "id": "1001678901235", "type": "user", "status": "En ligne"},
        {"name": "Julien Moreau", "id": "1001789012346", "type": "user", "status": "Hors ligne"},
        {"name": "Camille Girard", "id": "1001890123457", "type": "user", "status": "Actif"},
        {"name": "Théo Andre", "id": "1001901234568", "type": "user", "status": "En ligne"},
        {"name": "Inès Mercier", "id": "1001012345679", "type": "user", "status": "Actif"},
        {"name": "Samuel Blanc", "id": "1001123456780", "type": "user", "status": "Hors ligne"},
        {"name": "Océane Guerin", "id": "1001234567891", "type": "user", "status": "En ligne"},
        {"name": "Quentin Muller", "id": "1001345678902", "type": "user", "status": "Actif"},
        {"name": "Anaïs Lefevre", "id": "1001456789014", "type": "user", "status": "En ligne"},
        {"name": "Romain Fournier", "id": "1001567890125", "type": "user", "status": "Hors ligne"},
        {"name": "Lola Michel", "id": "1001678901236", "type": "user", "status": "Actif"},
        {"name": "Enzo Barbier", "id": "1001789012347", "type": "user", "status": "En ligne"},
        
        # Groups (35 groupes)
        {"name": "Famille Martin", "id": "1002370795564", "type": "group", "status": "Actif"},
        {"name": "Amis du Lycée", "id": "1002471806675", "type": "group", "status": "Actif"},
        {"name": "Équipe Projet", "id": "1002572817786", "type": "group", "status": "Actif"},
        {"name": "Football Local", "id": "1002673828897", "type": "group", "status": "Actif"},
        {"name": "Cuisine & Recettes", "id": "1002774839908", "type": "group", "status": "Actif"},
        {"name": "Voyage Été 2025", "id": "1002875840019", "type": "group", "status": "Actif"},
        {"name": "Développeurs Paris", "id": "1002976851120", "type": "group", "status": "Actif"},
        {"name": "Gamers United", "id": "1003077862231", "type": "group", "status": "Actif"},
        {"name": "Musique Indie", "id": "1003178873342", "type": "group", "status": "Actif"},
        {"name": "Photographie Pro", "id": "1003279884453", "type": "group", "status": "Actif"},
        {"name": "Startup Network", "id": "1003380895564", "type": "group", "status": "Actif"},
        {"name": "Runners Club", "id": "1003481906675", "type": "group", "status": "Actif"},
        {"name": "Cinéphiles", "id": "1003582917786", "type": "group", "status": "Actif"},
        {"name": "Voisins Quartier", "id": "1003683928897", "type": "group", "status": "Actif"},
        {"name": "Tech Support", "id": "1003784939908", "type": "group", "status": "Actif"},
        {"name": "Yoga & Méditation", "id": "1003885940019", "type": "group", "status": "Actif"},
        {"name": "Étudiants Info", "id": "1003986951120", "type": "group", "status": "Actif"},
        {"name": "Parents École", "id": "1004087962231", "type": "group", "status": "Actif"},
        {"name": "Randonnée Weekend", "id": "1004188973342", "type": "group", "status": "Actif"},
        {"name": "Crypto Trading", "id": "1004289984453", "type": "group", "status": "Actif"},
        {"name": "Livres & Lecture", "id": "1004390995564", "type": "group", "status": "Actif"},
        {"name": "Jardinage Bio", "id": "1004492006675", "type": "group", "status": "Actif"},
        {"name": "Moto Passion", "id": "1004593017786", "type": "group", "status": "Actif"},
        {"name": "Design Graphique", "id": "1004694028897", "type": "group", "status": "Actif"},
        {"name": "Écologie Locale", "id": "1004795039908", "type": "group", "status": "Actif"},
        {"name": "Gaming Retro", "id": "1004896040019", "type": "group", "status": "Actif"},
        {"name": "Artisans Créatifs", "id": "1004997051120", "type": "group", "status": "Actif"},
        {"name": "Freelancers", "id": "1005098062231", "type": "group", "status": "Actif"},
        {"name": "Animaux Compagnie", "id": "1005199073342", "type": "group", "status": "Actif"},
        {"name": "Événements Ville", "id": "1005300084453", "type": "group", "status": "Actif"},
        {"name": "Mode & Style", "id": "1005401095564", "type": "group", "status": "Actif"},
        {"name": "Sciences & Tech", "id": "1005502106675", "type": "group", "status": "Actif"},
        {"name": "Cuisine Végé", "id": "1005603117786", "type": "group", "status": "Actif"},
        {"name": "Théâtre Amateur", "id": "1005704128897", "type": "group", "status": "Actif"},
        {"name": "Bricolage Maison", "id": "1005805139908", "type": "group", "status": "Actif"},
        
        # Channels (30 canaux)
        {"name": "📰 Actualités France", "id": "1002682552255", "type": "channel", "status": "Actif"},
        {"name": "🚀 Tech News Daily", "id": "1002783563366", "type": "channel", "status": "Actif"},
        {"name": "💰 Crypto Updates", "id": "1002884574477", "type": "channel", "status": "Actif"},
        {"name": "🎮 Gaming News", "id": "1002985585588", "type": "channel", "status": "Actif"},
        {"name": "🎬 Cinéma Sorties", "id": "1003086596699", "type": "channel", "status": "Actif"},
        {"name": "📱 Apps & Outils", "id": "1003187607700", "type": "channel", "status": "Actif"},
        {"name": "🌍 Voyage & Culture", "id": "1003288618811", "type": "channel", "status": "Actif"},
        {"name": "💼 Business Tips", "id": "1003389629922", "type": "channel", "status": "Actif"},
        {"name": "🎨 Design Inspiration", "id": "1003490630033", "type": "channel", "status": "Actif"},
        {"name": "🍴 Recettes Gourmandes", "id": "1003591641144", "type": "channel", "status": "Actif"},
        {"name": "📚 Développement Perso", "id": "1003692652255", "type": "channel", "status": "Actif"},
        {"name": "⚽ Sport Express", "id": "1003793663366", "type": "channel", "status": "Actif"},
        {"name": "🎵 Playlist Quotidienne", "id": "1003894674477", "type": "channel", "status": "Actif"},
        {"name": "🌱 Écologie Pratique", "id": "1003995685588", "type": "channel", "status": "Actif"},
        {"name": "💡 Innovation Tech", "id": "1004096696699", "type": "channel", "status": "Actif"},
        {"name": "🏠 Déco & Maison", "id": "1004197707700", "type": "channel", "status": "Actif"},
        {"name": "👗 Mode Tendances", "id": "1004298718811", "type": "channel", "status": "Actif"},
        {"name": "🚗 Auto Moto News", "id": "1004399729922", "type": "channel", "status": "Actif"},
        {"name": "📊 Finance Perso", "id": "1004500730033", "type": "channel", "status": "Actif"},
        {"name": "🎭 Culture Spectacles", "id": "1004601741144", "type": "channel", "status": "Actif"},
        {"name": "🏃 Sport & Santé", "id": "1004702752255", "type": "channel", "status": "Actif"},
        {"name": "📸 Photo du Jour", "id": "1004803763366", "type": "channel", "status": "Actif"},
        {"name": "🧠 Science Vulgarisée", "id": "1004904774477", "type": "channel", "status": "Actif"},
        {"name": "🍰 Pâtisserie Créative", "id": "1005005785588", "type": "channel", "status": "Actif"},
        {"name": "🎪 Événements Paris", "id": "1005106796699", "type": "channel", "status": "Actif"},
        {"name": "💻 Développement Web", "id": "1005207807700", "type": "channel", "status": "Actif"},
        {"name": "🌟 Motivation Daily", "id": "1005308818811", "type": "channel", "status": "Actif"},
        {"name": "📖 Livre de la Semaine", "id": "1005409829922", "type": "channel", "status": "Actif"},
        {"name": "🎯 Marketing Digital", "id": "1005510830033", "type": "channel", "status": "Actif"},
        {"name": "🌊 Météo & Climat", "id": "1005611841144", "type": "channel", "status": "Actif"},
        
        # Bots (15 bots)
        {"name": "🤖 Assistant IA", "id": "1001111111111", "type": "bot", "status": "Actif"},
        {"name": "📊 Stats Bot", "id": "1001222222222", "type": "bot", "status": "Actif"},
        {"name": "🌤️ Météo Bot", "id": "1001333333333", "type": "bot", "status": "Actif"},
        {"name": "💰 Crypto Tracker", "id": "1001444444444", "type": "bot", "status": "Actif"},
        {"name": "📝 Notes Rapides", "id": "1001555555555", "type": "bot", "status": "Actif"},
        {"name": "🎵 Music Finder", "id": "1001666666666", "type": "bot", "status": "Actif"},
        {"name": "📰 News Aggregator", "id": "1001777777777", "type": "bot", "status": "Actif"},
        {"name": "🔗 Link Shortener", "id": "1001888888888", "type": "bot", "status": "Actif"},
        {"name": "🎲 Random Generator", "id": "1001999999999", "type": "bot", "status": "Actif"},
        {"name": "📅 Calendar Bot", "id": "1002000000000", "type": "bot", "status": "Actif"},
        {"name": "🔍 Search Helper", "id": "1002111111111", "type": "bot", "status": "Actif"},
        {"name": "📋 Task Manager", "id": "1002222222222", "type": "bot", "status": "Actif"},
        {"name": "🎯 Poll Creator", "id": "1002333333333", "type": "bot", "status": "Actif"},
        {"name": "📈 Analytics Bot", "id": "1002444444444", "type": "bot", "status": "Actif"},
        {"name": "🔐 Security Bot", "id": "1002555555555", "type": "bot", "status": "Actif"}
    ]
    
    if chat_type:
        return [chat for chat in sample_chats if chat["type"] == chat_type]
    return sample_chats