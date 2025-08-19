# Enhanced Message Utilities Module
# Message handling utilities from original yashoswalyo/MERGE-BOT with enhancements

import asyncio
import time
from typing import Optional, Dict, Any, List
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait, MessageNotModified, MessageDeleteForbidden

from config import Config
from __init__ import LOGGER

class MessageHandler:
    """Enhanced message handling with smart throttling and error recovery"""
    
    def __init__(self):
        self.edit_times: Dict[str, float] = {}
        self.throttle_delay = Config.EDIT_THROTTLE_SECONDS
    
    async def safe_edit_message(
        self, 
        message: Message, 
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "markdown",
        disable_web_page_preview: bool = True
    ) -> bool:
        """Safely edit message with FloodWait protection"""
        if not message or not hasattr(message, 'chat'):
            return False
        
        message_key = f"{message.chat.id}_{message.id}"
        current_time = time.time()
        last_edit = self.edit_times.get(message_key, 0)
        
        # Throttle check
        if (current_time - last_edit) < self.throttle_delay:
            return False
        
        try:
            await message.edit_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            self.edit_times[message_key] = current_time
            return True
            
        except FloodWait as e:
            LOGGER.warning(f"FloodWait: sleeping for {e.x} seconds")
            await asyncio.sleep(e.x)
            return await self.safe_edit_message(message, text, reply_markup, parse_mode, disable_web_page_preview)
        
        except MessageNotModified:
            # Message content is the same, consider it successful
            return True
        
        except Exception as e:
            LOGGER.error(f"Failed to edit message: {e}")
            return False
    
    async def safe_send_message(
        self,
        client: Client,
        chat_id: int,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "markdown",
        disable_web_page_preview: bool = True,
        reply_to_message_id: Optional[int] = None
    ) -> Optional[Message]:
        """Safely send message with error handling"""
        try:
            message = await client.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                reply_to_message_id=reply_to_message_id
            )
            return message
            
        except FloodWait as e:
            LOGGER.warning(f"FloodWait: sleeping for {e.x} seconds")
            await asyncio.sleep(e.x)
            return await self.safe_send_message(client, chat_id, text, reply_markup, parse_mode, disable_web_page_preview, reply_to_message_id)
        
        except Exception as e:
            LOGGER.error(f"Failed to send message: {e}")
            return None
    
    async def safe_delete_message(self, message: Message) -> bool:
        """Safely delete message"""
        try:
            await message.delete()
            return True
        except MessageDeleteForbidden:
            LOGGER.warning("Cannot delete message - insufficient permissions")
            return False
        except Exception as e:
            LOGGER.error(f"Failed to delete message: {e}")
            return False
    
    async def send_long_message(
        self,
        client: Client,
        chat_id: int,
        text: str,
        max_length: int = 4000,
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> List[Message]:
        """Send long message by splitting into chunks"""
        messages = []
        
        if len(text) <= max_length:
            message = await self.safe_send_message(client, chat_id, text, reply_markup)
            if message:
                messages.append(message)
            return messages
        
        # Split text into chunks
        chunks = []
        current_chunk = ""
        lines = text.split('\n')
        
        for line in lines:
            if len(current_chunk + line + '\n') > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = line + '\n'
                else:
                    # Line itself is too long, split by characters
                    while len(line) > max_length:
                        chunks.append(line[:max_length])
                        line = line[max_length:]
                    current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Send chunks
        for i, chunk in enumerate(chunks):
            # Only add reply markup to the last message
            markup = reply_markup if i == len(chunks) - 1 else None
            message = await self.safe_send_message(client, chat_id, chunk, markup)
            if message:
                messages.append(message)
            
            # Small delay between messages to avoid flood
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)
        
        return messages

class ProgressManager:
    """Manage progress messages with intelligent updates"""
    
    def __init__(self):
        self.active_progress: Dict[str, Dict[str, Any]] = {}
        self.message_handler = MessageHandler()
    
    async def start_progress(
        self,
        message: Message,
        operation: str,
        total_steps: int = 100,
        progress_id: Optional[str] = None
    ) -> str:
        """Start a progress tracking session"""
        if not progress_id:
            progress_id = f"{message.chat.id}_{message.id}_{int(time.time())}"
        
        self.active_progress[progress_id] = {
            'message': message,
            'operation': operation,
            'total_steps': total_steps,
            'current_step': 0,
            'start_time': time.time(),
            'last_update': 0,
            'status': 'Starting...'
        }
        
        await self._update_progress_message(progress_id)
        return progress_id
    
    async def update_progress(
        self,
        progress_id: str,
        current_step: int,
        status: str = None,
        force_update: bool = False
    ) -> bool:
        """Update progress"""
        if progress_id not in self.active_progress:
            return False
        
        progress_data = self.active_progress[progress_id]
        progress_data['current_step'] = current_step
        
        if status:
            progress_data['status'] = status
        
        current_time = time.time()
        
        # Only update if enough time has passed or forced
        if force_update or (current_time - progress_data['last_update']) >= 2.0:
            await self._update_progress_message(progress_id)
            progress_data['last_update'] = current_time
            return True
        
        return False
    
    async def complete_progress(self, progress_id: str, final_message: str = None):
        """Complete progress tracking"""
        if progress_id not in self.active_progress:
            return
        
        if final_message:
            message = self.active_progress[progress_id]['message']
            await self.message_handler.safe_edit_message(message, final_message)
        
        del self.active_progress[progress_id]
    
    async def _update_progress_message(self, progress_id: str):
        """Update the progress message display"""
        progress_data = self.active_progress[progress_id]
        message = progress_data['message']
        
        # Calculate progress metrics
        current = progress_data['current_step']
        total = progress_data['total_steps']
        progress_percent = (current / total * 100) if total > 0 else 0
        
        elapsed_time = time.time() - progress_data['start_time']
        speed = current / elapsed_time if elapsed_time > 0 and current > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0
        
        # Create progress bar
        bar_length = 20
        filled_length = int(bar_length * (current / total)) if total > 0 else 0
        progress_bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # Format time
        elapsed_str = self._format_time(int(elapsed_time))
        eta_str = self._format_time(int(eta)) if eta > 0 else "N/A"
        
        progress_text = f"""⏳ **{progress_data['operation']}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{progress_bar} `{progress_percent:.1f}%`

📊 **Progress:** {current}/{total}
⏱️ **Elapsed:** `{elapsed_str}`
🔮 **ETA:** `{eta_str}`
🔄 **Status:** {progress_data['status']}"""
        
        await self.message_handler.safe_edit_message(message, progress_text)
    
    def _format_time(self, seconds: int) -> str:
        """Format time duration"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds//60}m {seconds%60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

class BroadcastManager:
    """Manage broadcast messages to multiple users"""
    
    def __init__(self, client: Client):
        self.client = client
        self.message_handler = MessageHandler()
    
    async def broadcast_message(
        self,
        user_ids: List[int],
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, int]:
        """Broadcast message to multiple users"""
        results = {"sent": 0, "failed": 0, "blocked": 0}
        
        total_users = len(user_ids)
        
        for i, user_id in enumerate(user_ids):
            try:
                message = await self.message_handler.safe_send_message(
                    self.client, user_id, text, reply_markup
                )
                
                if message:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                
                # Progress callback
                if progress_callback:
                    await progress_callback(i + 1, total_users, results)
                
                # Small delay to avoid flood
                await asyncio.sleep(0.1)
                
            except Exception as e:
                error_str = str(e).lower()
                if "blocked" in error_str or "deleted" in error_str:
                    results["blocked"] += 1
                else:
                    results["failed"] += 1
                
                LOGGER.warning(f"Broadcast failed for user {user_id}: {e}")
        
        return results

# Global instances
message_handler = MessageHandler()
progress_manager = ProgressManager()

# Legacy functions for compatibility with old repo
async def EditMessage(message: Message, text: str, reply_markup=None):
    """Legacy message editing function"""
    return await message_handler.safe_edit_message(message, text, reply_markup)

async def SendMessage(client: Client, chat_id: int, text: str, reply_markup=None):
    """Legacy message sending function"""
    return await message_handler.safe_send_message(client, chat_id, text, reply_markup)

def create_keyboard(buttons: List[List[tuple]]) -> InlineKeyboardMarkup:
    """Create inline keyboard from button list"""
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for button_text, callback_data in row:
            keyboard_row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(keyboard)

def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    import math
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def format_duration(seconds: int) -> str:
    """Format duration in readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}:{seconds%60:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}:{minutes:02d}:{seconds%60:02d}"

# Export message utilities
__all__ = [
    'MessageHandler',
    'ProgressManager', 
    'BroadcastManager',
    'message_handler',
    'progress_manager',
    'EditMessage',
    'SendMessage',
    'create_keyboard',
    'format_file_size',
    'format_duration'
]
