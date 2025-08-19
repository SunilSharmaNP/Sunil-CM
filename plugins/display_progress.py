# Enhanced Progress Display Module
# Improved progress tracking from original yashoswalyo/MERGE-BOT

import time
import math
import asyncio
from typing import Optional, Callable, Dict, Any
from pyrogram.types import Message
from config import Config
from __init__ import LOGGER

class ProgressTracker:
    """Enhanced progress tracking with smart throttling"""
    
    def __init__(self, message: Message, operation: str = "Processing"):
        self.message = message
        self.operation = operation
        self.start_time = time.time()
        self.last_update = 0
        self.update_interval = Config.EDIT_THROTTLE_SECONDS
        self.total_size = 0
        self.completed_size = 0
    
    async def update_progress(
        self,
        current: int,
        total: int,
        status: str = None,
        extra_info: Dict[str, Any] = None
    ):
        """Update progress with smart throttling"""
        now = time.time()
        
        # Update internal tracking
        self.completed_size = current
        self.total_size = total
        
        # Only update if enough time has passed
        if (now - self.last_update) < self.update_interval:
            return
        
        try:
            # Calculate progress metrics
            progress_percent = (current / total) * 100 if total > 0 else 0
            elapsed_time = now - self.start_time
            speed = current / elapsed_time if elapsed_time > 0 else 0
            eta = (total - current) / speed if speed > 0 else 0
            
            # Create progress text
            progress_text = self._format_progress_message(
                current, total, progress_percent, speed, eta, status, extra_info
            )
            
            # Update message
            await self.message.edit_text(progress_text)
            self.last_update = now
            
        except Exception as e:
            LOGGER.warning(f"Progress update failed: {e}")
    
    def _format_progress_message(
        self,
        current: int,
        total: int,
        progress_percent: float,
        speed: float,
        eta: float,
        status: str = None,
        extra_info: Dict[str, Any] = None
    ) -> str:
        """Format progress message with enhanced styling"""
        
        # Progress bar
        progress_bar = self._create_progress_bar(progress_percent / 100)
        
        # Size formatting
        current_size = self._format_bytes(current)
        total_size = self._format_bytes(total)
        speed_str = f"{self._format_bytes(speed)}/s"
        
        # Time formatting
        eta_str = self._format_time(int(eta))
        elapsed_str = self._format_time(int(time.time() - self.start_time))
        
        # Base message
        message = f"""⏳ **{self.operation}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{progress_bar} `{progress_percent:.1f}%`

📊 **Size:** `{current_size}` / `{total_size}`
⚡ **Speed:** `{speed_str}`
⏱️ **Time:** `{elapsed_str}` | ETA: `{eta_str}`"""
        
        # Add status if provided
        if status:
            message += f"\n🔄 **Status:** {status}"
        
        # Add extra info if provided
        if extra_info:
            for key, value in extra_info.items():
                message += f"\n• **{key}:** {value}"
        
        return message
    
    def _create_progress_bar(self, progress: float, length: int = 20) -> str:
        """Create visual progress bar"""
        filled_length = int(length * progress)
        filled_char = Config.FINISHED_PROGRESS_STR
        empty_char = Config.UN_FINISHED_PROGRESS_STR
        
        return filled_char * filled_length + empty_char * (length - filled_length)
    
    def _format_bytes(self, bytes_value: float) -> str:
        """Format bytes to human readable format"""
        if bytes_value == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(bytes_value, 1024)))
        p = math.pow(1024, i)
        s = round(bytes_value / p, 2)
        
        return f"{s} {size_names[i]}"
    
    def _format_time(self, seconds: int) -> str:
        """Format time duration"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds//60}:{seconds%60:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}:{minutes:02d}:{seconds%60:02d}"

class EnhancedProgressDisplay:
    """Enhanced progress display system"""
    
    @staticmethod
    async def display_download_progress(
        message: Message,
        current: int,
        total: int,
        filename: str = "Unknown",
        source: str = "Unknown"
    ):
        """Display download progress"""
        tracker = ProgressTracker(message, "📥 Downloading")
        
        extra_info = {
            "File": f"`{filename[:30]}{'...' if len(filename) > 30 else ''}`",
            "Source": source
        }
        
        await tracker.update_progress(current, total, extra_info=extra_info)
    
    @staticmethod
    async def display_upload_progress(
        message: Message,
        current: int,
        total: int,
        filename: str = "Unknown",
        destination: str = "Unknown"
    ):
        """Display upload progress"""
        tracker = ProgressTracker(message, "📤 Uploading")
        
        extra_info = {
            "File": f"`{filename[:30]}{'...' if len(filename) > 30 else ''}`",
            "Destination": destination
        }
        
        await tracker.update_progress(current, total, extra_info=extra_info)
    
    @staticmethod
    async def display_merge_progress(
        message: Message,
        stage: str,
        current_file: int = 0,
        total_files: int = 0,
        additional_info: Dict[str, Any] = None
    ):
        """Display merge progress"""
        if total_files > 0:
            progress_percent = (current_file / total_files) * 100
            progress_bar = "█" * int(20 * (current_file / total_files)) + "░" * (20 - int(20 * (current_file / total_files)))
        else:
            progress_percent = 0
            progress_bar = "░" * 20
        
        message_text = f"""🔧 **Enhanced Merge Process**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{progress_bar} `{progress_percent:.1f}%`

🔄 **Stage:** {stage}
📊 **Progress:** {current_file}/{total_files} files"""
        
        if additional_info:
            for key, value in additional_info.items():
                message_text += f"\n• **{key}:** {value}"
        
        try:
            await message.edit_text(message_text)
        except Exception as e:
            LOGGER.warning(f"Merge progress update failed: {e}")

# Legacy functions for compatibility with old repo
async def progress_bar(
    current: int,
    total: int,
    status: Message,
    task: str = "Processing",
    file_name: str = "Unknown"
):
    """Legacy progress bar function"""
    tracker = ProgressTracker(status, task)
    extra_info = {"File": f"`{file_name}`"} if file_name != "Unknown" else None
    await tracker.update_progress(current, total, extra_info=extra_info)

async def EditMessage(
    message: Message,
    text: str,
    parse_mode: str = None,
    disable_web_page_preview: bool = True
):
    """Legacy message editing function with throttling"""
    current_time = time.time()
    
    # Simple throttling using message ID as key
    throttle_key = f"{message.chat.id}_{message.id}"
    if not hasattr(EditMessage, 'last_edits'):
        EditMessage.last_edits = {}
    
    last_edit = EditMessage.last_edits.get(throttle_key, 0)
    
    if (current_time - last_edit) >= Config.EDIT_THROTTLE_SECONDS:
        try:
            await message.edit_text(
                text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            EditMessage.last_edits[throttle_key] = current_time
        except Exception as e:
            LOGGER.warning(f"Message edit failed: {e}")

def get_progress_bar_str(progress: float) -> str:
    """Get progress bar string"""
    length = 20
    filled_length = int(length * progress)
    filled_char = Config.FINISHED_PROGRESS_STR
    empty_char = Config.UN_FINISHED_PROGRESS_STR
    
    return filled_char * filled_length + empty_char * (length - filled_length)

def humanbytes(size: int) -> str:
    """Convert bytes to human readable format"""
    if not size:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    
    return f"{s} {size_names[i]}"

def time_formatter(seconds: int) -> str:
    """Format time in human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m {seconds%60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

# Export progress display functions
__all__ = [
    'ProgressTracker',
    'EnhancedProgressDisplay',
    'progress_bar',
    'EditMessage',
    'get_progress_bar_str',
    'humanbytes',
    'time_formatter'
]
