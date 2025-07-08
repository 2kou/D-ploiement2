import logging
from telethon import events
from bot.database import load_data
from bot.connection import active_connections
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageRedirector:
    """Handles message redirection based on configured rules"""
    
    def __init__(self):
        self.redirection_clients = {}
        self.message_mapping = {}  # Maps original message ID to redirected message ID
        
    async def setup_redirection_handlers(self):
        """Setup message handlers for all active connections"""
        try:
            data = load_data()
            redirections = data.get("redirections", {})
            total_redirections = 0
            
            for user_id, user_redirections in redirections.items():
                if int(user_id) in active_connections:
                    connection_data = active_connections[int(user_id)]
                    client = connection_data.get('client')
                    if client and client.is_connected():
                        count = await self._setup_client_handlers(client, int(user_id), user_redirections)
                        total_redirections += count
                        logger.info(f"Setup {count} redirections for user {user_id}")
            
            logger.info(f"🔄 Redirections automatiques configurées: {total_redirections} redirections actives")
                        
        except Exception as e:
            logger.error(f"Error setting up redirection handlers: {e}")
    
    async def _setup_client_handlers(self, client, user_id, user_redirections):
        """Setup message handlers for a specific client"""
        setup_count = 0
        try:
            for name, redir_data in user_redirections.items():
                if redir_data.get('active', True):
                    source_id = redir_data.get('source_id')
                    destination_id = redir_data.get('destination_id')
                    
                    if source_id and destination_id:
                        # Create handler for new messages
                        @client.on(events.NewMessage(chats=int(source_id)))
                        async def message_handler(event, dest_id=destination_id, redirect_name=name):
                            await self._handle_message_redirection(event, dest_id, redirect_name, user_id, is_edit=False)
                        
                        # Create handler for edited messages
                        @client.on(events.MessageEdited(chats=int(source_id)))
                        async def edit_handler(event, dest_id=destination_id, redirect_name=name):
                            await self._handle_message_redirection(event, dest_id, redirect_name, user_id, is_edit=True)
                        
                        setup_count += 1
                        logger.info(f"✅ Redirection '{name}' configurée: {source_id} -> {destination_id}")
            
            return setup_count
                        
        except Exception as e:
            logger.error(f"Error setting up client handlers: {e}")
            return setup_count
    
    async def _handle_message_redirection(self, event, destination_id, redirect_name, user_id, is_edit=False):
        """Handle individual message redirection"""
        try:
            # Get the client for forwarding
            client = active_connections[user_id].get('client')
            if not client or not client.is_connected():
                logger.warning(f"Client not available for redirection {redirect_name}")
                return
            
            # Get message content
            message = event.message
            original_msg_id = message.id
            mapping_key = f"{event.chat_id}_{original_msg_id}_{destination_id}"
            
            # Get source and destination channel names for logging only
            source_name = await self._get_channel_name(client, event.chat_id)
            dest_name = await self._get_channel_name(client, int(destination_id))
            
            if is_edit:
                # Check if we have a mapping for this message
                if mapping_key in self.message_mapping:
                    redirected_msg_id = self.message_mapping[mapping_key]
                    try:
                        # Edit the existing message
                        if message.text:
                            await client.edit_message(int(destination_id), redirected_msg_id, message.text)
                            action = "edited and updated"
                            logger.info(f"Message {action} from {event.chat_id} ({source_name}) to {destination_id} ({dest_name}) via {redirect_name}")
                            return
                        elif message.media:
                            # For media edits, we need to delete and resend since Telegram doesn't allow editing media in the same way
                            try:
                                await client.delete_messages(int(destination_id), redirected_msg_id)
                            except:
                                pass  # Continue even if delete fails
                            # Fall through to send new message
                        else:
                            # Message was deleted or has no content, delete the redirected message too
                            try:
                                await client.delete_messages(int(destination_id), redirected_msg_id)
                                del self.message_mapping[mapping_key]
                                logger.info(f"Message deleted from {event.chat_id} to {destination_id} via {redirect_name}")
                                return
                            except Exception as delete_error:
                                logger.warning(f"Failed to delete message {redirected_msg_id}: {delete_error}")
                                return
                    except Exception as edit_error:
                        # Check if it's just a "content not modified" error
                        if "Content of the message was not modified" in str(edit_error):
                            logger.info(f"Message content unchanged for edit in {event.chat_id} to {destination_id} via {redirect_name}")
                            return  # Don't send duplicate message
                        else:
                            logger.warning(f"Failed to edit message {redirected_msg_id}: {edit_error}. Sending new message instead.")
                            # If edit fails for other reasons, continue to send new message
                else:
                    # This is an edit but we don't have the original message mapped
                    logger.info(f"Edit event for unmapped message {original_msg_id} in {event.chat_id}")
                    # Don't send anything for edits of unmapped messages
                    return
            
            # Send new message (either first time or edit/media replacement)
            sent_message = None
            if message.text:
                sent_message = await client.send_message(int(destination_id), message.text)
            elif message.media:
                # Forward media directly
                sent_message = await client.forward_messages(int(destination_id), message)
            
            # Store the mapping for future edits (only for new messages or successful replacements)
            if sent_message and not is_edit:
                if hasattr(sent_message, 'id'):
                    self.message_mapping[mapping_key] = sent_message.id
                elif isinstance(sent_message, list) and len(sent_message) > 0:
                    self.message_mapping[mapping_key] = sent_message[0].id
            elif sent_message and is_edit:
                # Update mapping for media replacements
                if hasattr(sent_message, 'id'):
                    self.message_mapping[mapping_key] = sent_message.id
                elif isinstance(sent_message, list) and len(sent_message) > 0:
                    self.message_mapping[mapping_key] = sent_message[0].id
            
            action = "edited and redirected" if is_edit else "redirected"
            logger.info(f"Message {action} from {event.chat_id} ({source_name}) to {destination_id} ({dest_name}) via {redirect_name}")
            
        except Exception as e:
            logger.error(f"Error handling message redirection: {e}")
    
    async def _get_channel_name(self, client, chat_id):
        """Get the actual channel/chat name"""
        try:
            entity = await client.get_entity(chat_id)
            
            # Get the proper name
            if hasattr(entity, 'title') and entity.title:
                return entity.title
            elif hasattr(entity, 'first_name') and entity.first_name:
                name = entity.first_name
                if hasattr(entity, 'last_name') and entity.last_name:
                    name += f" {entity.last_name}"
                return name
            elif hasattr(entity, 'username') and entity.username:
                return f"@{entity.username}"
            else:
                return f"Chat {chat_id}"
                
        except Exception as e:
            logger.error(f"Error getting channel name for {chat_id}: {e}")
            return f"Chat {chat_id}"
    
    async def add_redirection_handler(self, user_id, name, source_id, destination_id):
        """Add a new redirection handler for a user"""
        try:
            if user_id not in active_connections:
                return False
                
            client = active_connections[user_id].get('client')
            if not client or not client.is_connected():
                return False
            
            # Create handler for new messages
            @client.on(events.NewMessage(chats=int(source_id)))
            async def message_handler(event, dest_id=destination_id, redirect_name=name):
                await self._handle_message_redirection(event, dest_id, redirect_name, user_id, is_edit=False)
            
            # Create handler for edited messages
            @client.on(events.MessageEdited(chats=int(source_id)))
            async def edit_handler(event, dest_id=destination_id, redirect_name=name):
                await self._handle_message_redirection(event, dest_id, redirect_name, user_id, is_edit=True)
            
            logger.info(f"Added message and edit handlers for redirection {name}: {source_id} -> {destination_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding redirection handler: {e}")
            return False
    
    async def remove_redirection_handler(self, user_id, name):
        """Remove a redirection handler for a user"""
        try:
            # Note: Telethon doesn't provide direct handler removal
            # In a production system, you would need to track handlers
            # and remove them manually or restart the client
            logger.info(f"Redirection handler removal requested for {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing redirection handler: {e}")
            return False

# Global message redirector instance
message_redirector = MessageRedirector()