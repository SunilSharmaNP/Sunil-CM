# Enhanced Uploader Module
# Combines Telegram upload from old repo with GoFile integration from new repo

import os
import time
import asyncio
from typing import Optional, Union
import aiohttp
from aiohttp import FormData
from random import choice
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery
from config import Config
from helpers.utils import get_readable_file_size, format_progress_time
from __init__ import LOGGER

# Smart progress tracking
last_edit_time = {}
EDIT_THROTTLE_SECONDS = 4.0

async def smart_progress_editor(status_message, text: str):
    """Enhanced progress editor with FloodWait prevention"""
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

class GoFileUploader:
    """Enhanced GoFile uploader from new repo with improved error handling"""
    
    def __init__(self, token: str = None):
        self.api_url = "https://api.gofile.io/"
        self.token = token or getattr(Config, 'GOFILE_TOKEN', None)
    
    async def _get_server(self) -> str:
        """Get available GoFile server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}servers") as resp:
                    resp.raise_for_status()
                    result = await resp.json()
                    
                    if result.get("status") == "ok":
                        servers = result["data"]["servers"]
                        return choice(servers)["name"]
                    
                    raise Exception(f"Failed to get server: {result}")
        except Exception as e:
            LOGGER.error(f"Failed to get GoFile server: {e}")
            raise Exception("Failed to fetch GoFile upload server.")
    
    async def upload_file(self, file_path: str, status_message=None) -> str:
        """Upload file to GoFile with progress tracking"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            server = await self._get_server()
            upload_url = f"https://{server}.gofile.io/uploadFile"
            
            if status_message:
                await smart_progress_editor(status_message, "🔗 **Uploading to GoFile.io...**\nGetting upload server...")
            
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            data = FormData()
            if self.token:
                data.add_field("token", self.token)
            
            with open(file_path, "rb") as f:
                data.add_field("file", f, filename=filename)
                
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    
                    if status_message:
                        await smart_progress_editor(
                            status_message, 
                            f"🔗 **Uploading to GoFile.io...**\n"
                            f"➢ `{filename}`\n"
                            f"➢ **Size:** `{get_readable_file_size(file_size)}`"
                        )
                    
                    async with session.post(upload_url, data=data) as resp:
                        resp.raise_for_status()
                        resp_json = await resp.json()
                        
                        if resp_json.get("status") == "ok":
                            download_page = resp_json["data"]["downloadPage"]
                            
                            if status_message:
                                elapsed_time = time.time() - start_time
                                await smart_progress_editor(
                                    status_message,
                                    f"✅ **GoFile Upload Complete!**\n"
                                    f"➢ **File:** `{filename}`\n"
                                    f"➢ **Size:** `{get_readable_file_size(file_size)}`\n"
                                    f"➢ **Time:** `{format_progress_time(int(elapsed_time))}`\n"
                                    f"➢ **Link:** {download_page}"
                                )
                            
                            LOGGER.info(f"Successfully uploaded to GoFile: {filename}")
                            return download_page
                        else:
                            raise Exception(f"GoFile upload failed: {resp_json.get('status')}")
                            
        except Exception as e:
            error_msg = f"Failed to upload to GoFile: {str(e)}"
            LOGGER.error(error_msg)
            if status_message:
                await status_message.edit_text(f"❌ **GoFile Upload Failed!**\nError: `{str(e)}`")
            raise Exception(error_msg)

class EnhancedTelegramUploader:
    """Enhanced Telegram uploader combining old repo features with new repo efficiency"""
    
    def __init__(self, client: Client):
        self.client = client
        self.userBot = None  # Premium user bot for large files
    
    async def create_thumbnail(self, video_path: str, custom_thumbnail: str = None) -> Optional[str]:
        """Create or use custom thumbnail"""
        try:
            if custom_thumbnail and os.path.exists(custom_thumbnail):
                return custom_thumbnail
            
            # Generate default thumbnail from video middle
            thumbnail_path = f"{os.path.splitext(video_path)[0]}.jpg"
            
            # Get video duration first
            import ffmpeg
            probe = ffmpeg.probe(video_path)
            duration = float(probe['format']['duration'])
            thumbnail_time = duration / 2
            
            # Create thumbnail
            command = [
                'ffmpeg', '-hide_banner', '-loglevel', 'error',
                '-i', video_path, '-ss', str(thumbnail_time),
                '-vframes', '1', '-c:v', 'mjpeg', '-f', 'image2',
                '-y', thumbnail_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(thumbnail_path):
                return thumbnail_path
            else:
                LOGGER.warning(f"Failed to create thumbnail: {stderr.decode().strip()}")
                return None
                
        except Exception as e:
            LOGGER.error(f"Thumbnail creation error: {e}")
            return None
    
    async def upload_to_telegram(
        self, 
        chat_id: int, 
        file_path: str, 
        status_message,
        custom_thumbnail: str = None,
        custom_filename: str = None,
        upload_as_document: bool = False,
        caption: str = None
    ) -> bool:
        """
        Upload file to Telegram with enhanced features from old repo
        """
        try:
            file_size = os.path.getsize(file_path)
            filename = custom_filename or os.path.basename(file_path)
            
            # Check file size limits
            max_size = 4 * 1024 * 1024 * 1024 if Config.IS_PREMIUM else 2 * 1024 * 1024 * 1024  # 4GB or 2GB
            
            if file_size > max_size:
                size_limit = "4GB" if Config.IS_PREMIUM else "2GB"
                await status_message.edit_text(
                    f"❌ **File too large!**\n"
                    f"Size: `{get_readable_file_size(file_size)}`\n"
                    f"Limit: `{size_limit}`"
                )
                return False
            
            # Create thumbnail
            thumbnail_path = await self.create_thumbnail(file_path, custom_thumbnail)
            
            # Get video properties for metadata
            video_metadata = {}
            try:
                import ffmpeg
                probe = ffmpeg.probe(file_path)
                video_stream = next(
                    (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), 
                    None
                )
                if video_stream:
                    video_metadata = {
                        'duration': int(float(probe['format'].get('duration', 0))),
                        'width': int(video_stream.get('width', 0)),
                        'height': int(video_stream.get('height', 0))
                    }
            except:
                pass
            
            # Default caption
            if not caption:
                caption = (
                    f"**Enhanced MERGE-BOT**\n"
                    f"➢ **File:** `{filename}`\n"
                    f"➢ **Size:** `{get_readable_file_size(file_size)}`"
                )
            
            # Progress callback
            async def progress_callback(current, total):
                progress = current / total
                speed = current / (time.time() - start_time + 1)
                eta = (total - current) / speed if speed > 0 else 0
                
                progress_text = (
                    f"📤 **Uploading to Telegram...**\n"
                    f"➢ `{filename}`\n"
                    f"➢ {self._get_progress_bar(progress)} `{progress:.1%}`\n"
                    f"➢ **Size:** `{get_readable_file_size(current)}` / `{get_readable_file_size(total)}`\n"
                    f"➢ **Speed:** `{get_readable_file_size(int(speed))}/s`\n"
                    f"➢ **ETA:** `{format_progress_time(int(eta))}`"
                )
                await smart_progress_editor(status_message, progress_text)
            
            start_time = time.time()
            
            # Choose upload method
            if upload_as_document or not video_metadata:
                # Upload as document
                await self.client.send_document(
                    chat_id=chat_id,
                    document=file_path,
                    caption=caption,
                    file_name=filename,
                    thumb=thumbnail_path,
                    progress=progress_callback
                )
            else:
                # Upload as video
                await self.client.send_video(
                    chat_id=chat_id,
                    video=file_path,
                    caption=caption,
                    file_name=filename,
                    duration=video_metadata.get('duration', 0),
                    width=video_metadata.get('width', 0),
                    height=video_metadata.get('height', 0),
                    thumb=thumbnail_path,
                    progress=progress_callback
                )
            
            # Clean up thumbnail if it was generated
            if thumbnail_path and thumbnail_path != custom_thumbnail and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            
            # Delete status message after successful upload
            try:
                await status_message.delete()
            except:
                pass
            
            # Copy to log channel if configured
            if hasattr(Config, 'LOGCHANNEL') and Config.LOGCHANNEL:
                try:
                    log_caption = f"{caption}\n\n**Uploaded by:** User ID `{chat_id}`"
                    if upload_as_document:
                        await self.client.send_document(
                            chat_id=int(Config.LOGCHANNEL),
                            document=file_path,
                            caption=log_caption,
                            file_name=filename
                        )
                    else:
                        await self.client.send_video(
                            chat_id=int(Config.LOGCHANNEL),
                            video=file_path,
                            caption=log_caption,
                            file_name=filename,
                            duration=video_metadata.get('duration', 0),
                            width=video_metadata.get('width', 0),
                            height=video_metadata.get('height', 0)
                        )
                except Exception as e:
                    LOGGER.error(f"Failed to copy to log channel: {e}")
            
            LOGGER.info(f"Successfully uploaded to Telegram: {filename}")
            return True
            
        except Exception as e:
            error_msg = f"❌ **Telegram Upload Failed!**\nError: `{str(e)}`"
            try:
                await status_message.edit_text(error_msg)
            except:
                pass
            LOGGER.error(f"Telegram upload error: {e}")
            return False
    
    def _get_progress_bar(self, progress: float, length: int = 20) -> str:
        """Generate progress bar matching old repo style"""
        filled_len = int(length * progress)
        return '█' * filled_len + '░' * (length - filled_len)

# Legacy functions for compatibility with old repo
async def uploadVideo(
    c: Client,
    cb: CallbackQuery,
    merged_video_path: str,
    width: int,
    height: int,
    duration: int,
    video_thumbnail: str,
    file_size: int,
    upload_mode: bool
) -> bool:
    """Legacy wrapper function for old repo compatibility"""
    uploader = EnhancedTelegramUploader(c)
    
    return await uploader.upload_to_telegram(
        chat_id=cb.message.chat.id,
        file_path=merged_video_path,
        status_message=cb.message,
        custom_thumbnail=video_thumbnail,
        upload_as_document=upload_mode
    )

async def upload_to_telegram(
    client: Client, 
    chat_id: int, 
    file_path: str, 
    status_message, 
    custom_thumbnail: str = None, 
    custom_filename: str = None
) -> bool:
    """New repo style function"""
    uploader = EnhancedTelegramUploader(client)
    
    return await uploader.upload_to_telegram(
        chat_id=chat_id,
        file_path=file_path,
        status_message=status_message,
        custom_thumbnail=custom_thumbnail,
        custom_filename=custom_filename
    )

# Export main classes and functions
__all__ = [
    'GoFileUploader',
    'EnhancedTelegramUploader',
    'uploadVideo',
    'upload_to_telegram',
    'smart_progress_editor'
]
