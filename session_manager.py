import logging
import os
import asyncio
from telethon import TelegramClient
from bot.database import load_data, save_data
import psycopg2
from datetime import datetime

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages persistent Telegram sessions"""
    
    def __init__(self):
        self.sessions = {}  # In-memory active sessions
        self.db_connection = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection and tables"""
        try:
            self.db_connection = psycopg2.connect(os.getenv("DATABASE_URL"))
            cursor = self.db_connection.cursor()
            
            # Create sessions table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telegram_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    phone_number VARCHAR(20) NOT NULL,
                    session_file TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, phone_number)
                )
            """)
            
            self.db_connection.commit()
            cursor.close()
            logger.info("Session database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing session database: {e}")
    
    async def store_session(self, user_id, phone_number, session_name):
        """Store session information in database"""
        try:
            cursor = self.db_connection.cursor()
            
            # Insert or update session
            cursor.execute("""
                INSERT INTO telegram_sessions (user_id, phone_number, session_file, is_active, last_used)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, phone_number)
                DO UPDATE SET 
                    session_file = EXCLUDED.session_file,
                    is_active = EXCLUDED.is_active,
                    last_used = EXCLUDED.last_used
            """, (user_id, phone_number, session_name, True, datetime.now()))
            
            self.db_connection.commit()
            cursor.close()
            logger.info(f"Session stored for user {user_id}, phone {phone_number}")
            
        except Exception as e:
            logger.error(f"Error storing session: {e}")
    
    async def get_user_sessions(self, user_id):
        """Get all active sessions for a user"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT phone_number, session_file, last_used 
                FROM telegram_sessions 
                WHERE user_id = %s AND is_active = TRUE
            """, (user_id,))
            
            sessions = cursor.fetchall()
            cursor.close()
            
            return [{'phone': row[0], 'session_file': row[1], 'last_used': row[2]} for row in sessions]
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def restore_all_sessions(self):
        """Restore all active sessions on bot startup"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT user_id, phone_number, session_file 
                FROM telegram_sessions 
                WHERE is_active = TRUE
            """)
            
            sessions = cursor.fetchall()
            cursor.close()
            
            for user_id, phone_number, session_file in sessions:
                await self._restore_session(user_id, phone_number, session_file)
                
            logger.info(f"Restored {len(sessions)} active sessions")
            
        except Exception as e:
            logger.error(f"Error restoring sessions: {e}")
    
    async def _restore_session(self, user_id, phone_number, session_file):
        """Restore a single session"""
        try:
            # Check if session file exists
            if not os.path.exists(session_file):
                logger.warning(f"Session file not found: {session_file}")
                await self.deactivate_session(user_id, phone_number)
                return False
            
            # Create Telegram client with existing session
            client = TelegramClient(
                session_file.replace('.session', ''),  # Telethon expects name without .session
                int(os.getenv("API_ID")),
                os.getenv("API_HASH")
            )
            
            # Try to connect
            await client.connect()
            
            if await client.is_user_authorized():
                # Store in active sessions
                from bot.connection import active_connections
                active_connections[user_id] = {
                    'client': client,
                    'phone': phone_number,
                    'connected': True,
                    'session_name': session_file,
                    'restored': True
                }
                
                # Update last used time
                await self.update_session_activity(user_id, phone_number)
                
                logger.info(f"Session restored for user {user_id}, phone {phone_number}")
                return True
            else:
                # Session expired, deactivate
                await client.disconnect()
                await self.deactivate_session(user_id, phone_number)
                logger.warning(f"Session expired for user {user_id}, phone {phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring session for user {user_id}: {e}")
            await self.deactivate_session(user_id, phone_number)
            return False
    
    async def update_session_activity(self, user_id, phone_number):
        """Update last used timestamp for a session"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE telegram_sessions 
                SET last_used = %s 
                WHERE user_id = %s AND phone_number = %s
            """, (datetime.now(), user_id, phone_number))
            
            self.db_connection.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
    
    async def deactivate_session(self, user_id, phone_number):
        """Deactivate a session in database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE telegram_sessions 
                SET is_active = FALSE 
                WHERE user_id = %s AND phone_number = %s
            """, (user_id, phone_number))
            
            self.db_connection.commit()
            cursor.close()
            
            # Remove from active connections if present
            from bot.connection import active_connections
            if user_id in active_connections:
                client = active_connections[user_id].get('client')
                if client:
                    await client.disconnect()
                del active_connections[user_id]
            
            logger.info(f"Session deactivated for user {user_id}, phone {phone_number}")
            
        except Exception as e:
            logger.error(f"Error deactivating session: {e}")
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions (older than 7 days)"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE telegram_sessions 
                SET is_active = FALSE 
                WHERE last_used < NOW() - INTERVAL '7 days' 
                AND is_active = TRUE
            """)
            
            affected_rows = cursor.rowcount
            self.db_connection.commit()
            cursor.close()
            
            if affected_rows > 0:
                logger.info(f"Cleaned up {affected_rows} expired sessions")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    def close(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()

# Global session manager instance
session_manager = SessionManager()