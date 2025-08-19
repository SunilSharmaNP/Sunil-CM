# Enhanced Downloader Module
# Combines modern async approach from SunilSharmaNP/Sunil-CM with old repo structure

import aiohttp
import os
import time
import asyncio
from typing import Optional, Dict, Any
from pyrogram.types import Message
from config import Config
from helpers.utils import get_readable_file_size, format_progress_time, is_valid_url
from __init__ import LOGGER, cache, performance_monitor

# Global throttling to prevent FloodWait errors
last_edit_time = {}
EDIT_THROTTLE_SECONDS = Config.EDIT_THROTTLE_SECONDS

async def smart_progress_editor(status_message, text: str):
    """
    Enhanced progress editor that prevents FloodWait errors
    Combines new repo's throttling with old repo's message handling
    """
    if not status_message or not hasattr(status_message, 'chat'):
        return
        
    message_key = f"{status_message.chat.id}_{status_message.id}"
    now = time.time()
    last_time = last_edit_time.get(message_key, 0)
    
    if (now - last_time) > EDIT_THROTTLE_SECONDS:
        try:
            await status_message.edit_text(text)
            last_edit_time[message_key] = now
        except Exception as e:
            LOGGER.warning(f"Failed to edit progress message: {e}")

class EnhancedDownloader:
    """
    Enhanced downloader combining old repo's structure with new repo's efficiency
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.download_dir = f"{Config.DOWNLOAD_DIR}/{user_id}"
        self.session = None
        self.downloaded_files = []
        self._ensure_directory()
        
        # Performance tracking
        performance_monitor.start_operation(f"downloader_init_{user_id}")
    
    def _ensure_directory(self):
        """Ensure download directory exists with proper permissions"""
        try:
            os.makedirs(self.download_dir, mode=0o755, exist_ok=True)
            LOGGER.debug(f"Download directory ready: {self.download_dir}")
        except Exception as e:
            LOGGER.error(f"Failed to create download directory {self.download_dir}: {e}")
            raise
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with optimized settings"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=Config.MAX_CONCURRENT_DOWNLOADS,
                limit_per_host=2,
                keepalive_timeout=300,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=Config.DOWNLOAD_TIMEOUT,
                connect=30,
                sock_read=60
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Enhanced-MERGE-BOT/6.0 (Telegram Bot)'
                }
            )
            
            LOGGER.debug(f"Created new HTTP session for user {self.user_id}")
        
        return self.session
    
    async def download_from_url(self, url: str, status_message, filename: str = None) -> Optional[str]:
        """
        Download file from direct URL with enhanced progress tracking
        Improved version of new repo's downloader with old repo compatibility
        """
        if not is_valid_url(url):
            await status_message.edit_text("❌ **Invalid URL!** Please provide a valid direct download link.")
            return None
        
        # Check cache first
        cache_key = f"url_info_{hash(url)}"
        cached_info = cache.get(cache_key)
        
        if not filename:
            filename = url.split('/')[-1] or f"download_{int(time.time())}.mp4"
            # Remove query parameters from filename
            filename = filename.split('?')[0]
        
        dest_path = os.path.join(self.download_dir, filename)
        
        # Avoid duplicate downloads
        if os.path.exists(dest_path):
            existing_size = os.path.getsize(dest_path)
            if existing_size > 0:
                LOGGER.info(f"File already exists, skipping download: {filename}")
                await status_message.edit_text(f"✅ **File Already Downloaded!**\n`{filename}`")
                return dest_path
        
        try:
            session = await self._get_session()
            
            performance_monitor.start_operation(f"url_download_{self.user_id}")
            LOGGER.info(f"Starting URL download for user {self.user_id}: {url}")
            
            # Initial progress message
            await smart_progress_editor(
                status_message,
                f"🔗 **Connecting to URL...**\n➢ `{filename[:50]}{'...' if len(filename) > 50 else ''}`\n➢ **Status:** Establishing connection..."
            )
            
            async with session.get(url) as resp:
                if resp.status != 200:
                    error_msg = f"❌ **Download Failed!**\n**Status:** {resp.status}\n**URL:** `{url[:50]}...`"
                    if resp.status == 403:
                        error_msg += "\n**Reason:** Access forbidden (may need authentication)"
                    elif resp.status == 404:
                        error_msg += "\n**Reason:** File not found"
                    elif resp.status == 429:
                        error_msg += "\n**Reason:** Rate limited, try again later"
                    
                    await status_message.edit_text(error_msg)
                    performance_monitor.end_operation(f"url_download_{self.user_id}", success=False)
                    return None
                
                # Get file information
                total_size = int(resp.headers.get('content-length', 0))
                content_type = resp.headers.get('content-type', 'unknown')
                
                # Cache file info
                file_info = {
                    'size': total_size,
                    'content_type': content_type,
                    'filename': filename
                }
                cache.set(cache_key, file_info, ttl=3600)  # Cache for 1 hour
                
                # Check file size limits
                max_size = Config.MAX_FILE_SIZE_PREMIUM if Config.IS_PREMIUM else Config.MAX_FILE_SIZE_FREE
                if total_size > max_size:
                    size_limit = "4GB" if Config.IS_PREMIUM else "2GB"
                    await status_message.edit_text(
                        f"❌ **File Too Large!**\n"
                        f"**File Size:** `{get_readable_file_size(total_size)}`\n"
                        f"**Limit:** `{size_limit}`\n"
                        f"**Solution:** Use premium account for larger files"
                    )
                    return None
                
                # Start download with progress tracking
                downloaded = 0
                start_time = time.time()
                last_update = 0
                
                with open(dest_path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(Config.DOWNLOAD_CHUNK_SIZE):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress with throttling
                        current_time = time.time()
                        if current_time - last_update >= 2.0:  # Update every 2 seconds
                            if total_size > 0:
                                progress = downloaded / total_size
                                speed = downloaded / (current_time - start_time + 1)
                                eta = (total_size - downloaded) / speed if speed > 0 else 0
                                
                                progress_text = (
                                    f"📥 **Downloading from URL...**\n"
                                    f"➢ `{filename}`\n"
                                    f"➢ {self._get_progress_bar(progress)} `{progress:.1%}`\n"
                                    f"➢ **Size:** `{get_readable_file_size(downloaded)}` / "
                                    f"`{get_readable_file_size(total_size)}`\n"
                                    f"➢ **Speed:** `{get_readable_file_size(int(speed))}/s`\n"
                                    f"➢ **ETA:** `{format_progress_time(int(eta))}`"
                                )
                                await smart_progress_editor(status_message, progress_text)
                            last_update = current_time
                
                # Verify download completion
                final_size = os.path.getsize(dest_path)
                if total_size > 0 and final_size != total_size:
                    await status_message.edit_text("❌ **Download Incomplete!** File may be corrupted.")
                    os.remove(dest_path)
                    return None
                
                # Success message
                download_time = time.time() - start_time
                avg_speed = final_size / download_time if download_time > 0 else 0
                
                await status_message.edit_text(
                    f"✅ **Download Complete!**\n"
                    f"➢ **File:** `{filename}`\n"
                    f"➢ **Size:** `{get_readable_file_size(final_size)}`\n"
                    f"➢ **Time:** `{format_progress_time(int(download_time))}`\n"
                    f"➢ **Speed:** `{get_readable_file_size(int(avg_speed))}/s`\n"
                    f"➢ **Type:** `{content_type}`"
                )
                
                self.downloaded_files.append(dest_path)
                performance_monitor.end_operation(f"url_download_{self.user_id}", success=True)
                LOGGER.info(f"Successfully downloaded: {filename} ({get_readable_file_size(final_size)})")
                
                return dest_path
                
        except asyncio.TimeoutError:
            error_msg = "❌ **Download Timeout!**\nThe download took too long and was cancelled."
            await status_message.edit_text(error_msg)
            LOGGER.error(f"Download timeout for {url}")
        except aiohttp.ClientError as e:
            error_msg = f"❌ **Network Error!**\nFailed to connect: `{str(e)}`"
            await status_message.edit_text(error_msg)
            LOGGER.error(f"Network error downloading {url}: {e}")
        except Exception as e:
            error_msg = f"❌ **Download Failed!**\nUnexpected error: `{str(e)}`"
            await status_message.edit_text(error_msg)
            LOGGER.error(f"Unexpected error downloading {url}: {e}")
        
        performance_monitor.end_operation(f"url_download_{self.user_id}", success=False)
        return None
    
    async def download_from_telegram(self, message: Message, status_message) -> Optional[str]:
        """
        Download file from Telegram with enhanced progress tracking
        Maintains compatibility with old repo's message handling
        """
        try:
            media = message.video or message.document or message.audio
            if not media:
                await status_message.edit_text("❌ **No Media Found!** The message doesn't contain a downloadable file.")
                return None
            
            filename = media.file_name or f"telegram_file_{int(time.time())}.{self._get_file_extension(media)}"
            dest_path = os.path.join(self.download_dir, filename)
            
            # Check file size limits
            max_size = Config.MAX_FILE_SIZE_PREMIUM if Config.IS_PREMIUM else Config.MAX_FILE_SIZE_FREE
            if media.file_size > max_size:
                size_limit = "4GB" if Config.IS_PREMIUM else "2GB"
                await status_message.edit_text(
                    f"❌ **File Too Large!**\n"
                    f"**File:** `{filename}`\n"
                    f"**Size:** `{get_readable_file_size(media.file_size)}`\n"
                    f"**Limit:** `{size_limit}`\n"
                    f"**Solution:** Use premium account for 4GB support"
                )
                return None
            
            performance_monitor.start_operation(f"tg_download_{self.user_id}")
            LOGGER.info(f"Starting Telegram download for user {self.user_id}: {filename}")
            
            # Progress callback for pyrogram download
            start_time = time.time()
            
            async def progress_callback(current, total):
                progress = current / total if total > 0 else 0
                elapsed_time = time.time() - start_time
                speed = current / elapsed_time if elapsed_time > 0 else 0
                eta = (total - current) / speed if speed > 0 else 0
                
                progress_text = (
                    f"📥 **Downloading from Telegram...**\n"
                    f"➢ `{filename}`\n"
                    f"➢ {self._get_progress_bar(progress)} `{progress:.1%}`\n"
                    f"➢ **Size:** `{get_readable_file_size(current)}` / "
                    f"`{get_readable_file_size(total)}`\n"
                    f"➢ **Speed:** `{get_readable_file_size(int(speed))}/s`\n"
                    f"➢ **ETA:** `{format_progress_time(int(eta))}`"
                )
                await smart_progress_editor(status_message, progress_text)
            
            # Download the file
            file_path = await message.download(
                file_name=dest_path,
                progress=progress_callback
            )
            
            # Verify download
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                await status_message.edit_text("❌ **Download Failed!** File may be corrupted or incomplete.")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return None
            
            # Success message
            download_time = time.time() - start_time
            file_size = os.path.getsize(file_path)
            avg_speed = file_size / download_time if download_time > 0 else 0
            
            await status_message.edit_text(
                f"✅ **Download Complete!**\n"
                f"➢ **File:** `{filename}`\n"
                f"➢ **Size:** `{get_readable_file_size(file_size)}`\n"
                f"➢ **Time:** `{format_progress_time(int(download_time))}`\n"
                f"➢ **Speed:** `{get_readable_file_size(int(avg_speed))}/s`"
            )
            
            self.downloaded_files.append(file_path)
            performance_monitor.end_operation(f"tg_download_{self.user_id}", success=True)
            LOGGER.info(f"Successfully downloaded from Telegram: {filename}")
            
            return file_path
            
        except Exception as e:
            error_msg = f"❌ **Telegram Download Failed!**\nError: `{str(e)}`"
            await status_message.edit_text(error_msg)
            LOGGER.error(f"Telegram download error: {e}")
            performance_monitor.end_operation(f"tg_download_{self.user_id}", success=False)
            return None
    
    def _get_progress_bar(self, progress: float, length: int = 20) -> str:
        """Generate progress bar similar to old repo style"""
        filled_len = int(length * progress)
        return Config.FINISHED_PROGRESS_STR * filled_len + Config.UN_FINISHED_PROGRESS_STR * (length - filled_len)
    
    def _get_file_extension(self, media) -> str:
        """Get appropriate file extension based on media type"""
        if hasattr(media, 'mime_type') and media.mime_type:
            mime_type = media.mime_type.lower()
            if 'video' in mime_type:
                return 'mp4'
            elif 'audio' in mime_type:
                return 'mp3'
            elif 'image' in mime_type:
                return 'jpg'
        
        # Fallback based on media type
        if hasattr(media, 'duration'):  # Video or audio with duration
            return 'mp4'
        return 'bin'
    
    async def cleanup(self):
        """Clean up resources and temporary files"""
        try:
            # Close HTTP session
            if self.session and not self.session.closed:
                await self.session.close()
                LOGGER.debug(f"Closed HTTP session for user {self.user_id}")
            
            # Optional: Clean up downloaded files (if auto-cleanup is enabled)
            if Config.AUTO_DELETE_FILES and hasattr(self, 'downloaded_files'):
                for file_path in self.downloaded_files:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except:
                        pass
                
                if self.downloaded_files:
                    LOGGER.info(f"Cleaned up {len(self.downloaded_files)} downloaded files for user {self.user_id}")
            
        except Exception as e:
            LOGGER.error(f"Error during downloader cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get downloader statistics"""
        return {
            'user_id': self.user_id,
            'download_dir': self.download_dir,
            'files_downloaded': len(self.downloaded_files) if hasattr(self, 'downloaded_files') else 0,
            'session_active': self.session and not self.session.closed if self.session else False
        }

# Legacy functions for compatibility with old repo
async def download_from_url(url: str, user_id: int, status_message, filename: str = None) -> Optional[str]:
    """Legacy wrapper function for compatibility with old repository"""
    downloader = EnhancedDownloader(user_id)
    try:
        result = await downloader.download_from_url(url, status_message, filename)
        return result
    finally:
        await downloader.cleanup()

async def download_from_tg(message: Message, user_id: int, status_message) -> Optional[str]:
    """Legacy wrapper function for compatibility with old repository"""
    downloader = EnhancedDownloader(user_id)
    try:
        result = await downloader.download_from_telegram(message, status_message)
        return result
    finally:
        await downloader.cleanup()

# Export main class and functions
__all__ = [
    'EnhancedDownloader',
    'download_from_url', 
    'download_from_tg',
    'smart_progress_editor'
]
