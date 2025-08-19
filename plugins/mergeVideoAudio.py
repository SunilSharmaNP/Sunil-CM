# Enhanced Audio Merge Plugin
# Advanced audio track integration with video

import os
import time
import asyncio
from typing import List, Optional
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config
from helpers.utils import UserSettings, get_readable_file_size, get_video_info
from helpers.merger import EnhancedMerger
from __init__ import LOGGER, queueDB, AUDIO_EXTENSIONS

@Client.on_callback_query(filters.regex(r"merge_audio_(\d+)"))
async def merge_audio_callback(c: Client, cb: CallbackQuery):
    """Handle audio merge process"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ This is not your merge operation!", show_alert=True)
        return
    
    user = UserSettings(user_id, cb.from_user.first_name)
    
    # Check if user has video and audio files
    if user_id not in queueDB:
        await cb.answer("📂 No files in queue!", show_alert=True)
        return
    
    videos = queueDB[user_id].get("videos", [])
    audios = queueDB[user_id].get("audios", [])
    
    if not videos:
        await cb.answer("📹 No video files found!", show_alert=True)
        return
    
    if not audios:
        await cb.answer("🎵 No audio files found!", show_alert=True)
        return
    
    await start_audio_merge_process(c, cb, user_id, user, videos, audios)

async def start_audio_merge_process(
    c: Client, 
    cb: CallbackQuery, 
    user_id: int, 
    user: UserSettings,
    video_files: List,
    audio_files: List
):
    """Enhanced audio merge process"""
    try:
        await cb.edit_message_text(
            f"🎵 **Enhanced Audio Merge Starting...**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📹 **Video Files:** {len(video_files)}\n"
            f"🎵 **Audio Files:** {len(audio_files)}\n"
            f"🎯 **User:** {user.name}\n"
            f"🔄 **Status:** Preparing audio integration..."
        )
        
        # Download video files
        video_paths = []
        for i, video_item in enumerate(video_files):
            await cb.edit_message_text(
                f"📥 **Downloading Videos...**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔄 **Progress:** {i+1}/{len(video_files)}\n"
                f"📁 **Processing:** Video {i+1}"
            )
            
            if isinstance(video_item, str):  # URL
                from helpers.downloader import EnhancedDownloader
                downloader = EnhancedDownloader(user_id)
                video_path = await downloader.download_from_url(video_item, cb.message)
                await downloader.cleanup()
            else:  # Message ID
                message = await c.get_messages(chat_id=user_id, message_ids=video_item)
                from helpers.downloader import download_from_tg
                video_path = await download_from_tg(message, user_id, cb.message)
            
            if video_path and os.path.exists(video_path):
                video_paths.append(video_path)
            else:
                await cb.edit_message_text("❌ Failed to download video file!")
                return
        
        # Download audio files
        audio_paths = []
        for i, audio_item in enumerate(audio_files):
            await cb.edit_message_text(
                f"📥 **Downloading Audio...**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔄 **Progress:** {i+1}/{len(audio_files)}\n"
                f"🎵 **Processing:** Audio {i+1}"
            )
            
            if isinstance(audio_item, str):  # URL
                from helpers.downloader import EnhancedDownloader
                downloader = EnhancedDownloader(user_id)
                audio_path = await downloader.download_from_url(audio_item, cb.message)
                await downloader.cleanup()
            else:  # Message ID
                message = await c.get_messages(chat_id=user_id, message_ids=audio_item)
                from helpers.downloader import download_from_tg
                audio_path = await download_from_tg(message, user_id, cb.message)
            
            if audio_path and os.path.exists(audio_path):
                audio_paths.append(audio_path)
            else:
                await cb.edit_message_text("❌ Failed to download audio file!")
                return
        
        # Start audio merge process
        await cb.edit_message_text(
            f"🎵 **Audio Integration Phase**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 **Status:** Integrating audio tracks\n"
            f"⚡ **Engine:** Enhanced FFmpeg processing\n"
            f"🎯 **Quality:** Original audio preserved"
        )
        
        merged_path = await merge_video_with_audio(video_paths[0], audio_paths, user_id, cb.message)
        
        if merged_path and os.path.exists(merged_path):
            # Success - show upload options
            file_size = os.path.getsize(merged_path)
            file_info = get_video_info(merged_path)
            
            # Store merged file for upload
            queueDB[user_id]["merged_file"] = {
                "path": merged_path,
                "filename": os.path.basename(merged_path),
                "size": file_size,
                "info": file_info
            }
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Telegram", callback_data=f"upload_telegram_{user_id}")],
                [InlineKeyboardButton("🔗 GoFile.io", callback_data=f"upload_gofile_{user_id}")],
                [InlineKeyboardButton("☁️ Google Drive", callback_data=f"upload_gdrive_{user_id}")],
                [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_upload_{user_id}")]
            ])
            
            success_text = (
                f"✅ **Audio Merge Completed!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📁 **Output:** `{os.path.basename(merged_path)}`\n"
                f"📊 **Size:** `{get_readable_file_size(file_size)}`\n"
                f"🎵 **Audio Tracks:** {len(audio_paths)} integrated\n"
                f"🎬 **Duration:** `{file_info.get('duration', 0)}s`\n"
                f"🔧 **Process:** Enhanced audio integration\n\n"
                f"🚀 **Choose upload destination:**"
            )
            
            await cb.edit_message_text(success_text, reply_markup=keyboard)
            
            # Clear queues
            queueDB[user_id]["videos"].clear()
            queueDB[user_id]["audios"].clear()
        else:
            await cb.edit_message_text("❌ Audio merge failed! Please try again.")
    
    except Exception as e:
        LOGGER.error(f"Audio merge error for user {user_id}: {e}")
        await cb.edit_message_text(f"❌ **Audio merge failed:** `{str(e)}`")

async def merge_video_with_audio(video_path: str, audio_paths: List[str], user_id: int, status_message) -> Optional[str]:
    """Merge video with multiple audio tracks using FFmpeg"""
    try:
        output_filename = f"video_with_audio_{user_id}_{int(time.time())}.mp4"
        output_path = os.path.join(f"downloads/{user_id}", output_filename)
        
        # Build FFmpeg command
        cmd = ['ffmpeg', '-y', '-i', video_path]
        
        # Add audio inputs
        for audio_path in audio_paths:
            cmd.extend(['-i', audio_path])
        
        # Map video stream
        cmd.extend(['-map', '0:v'])
        
        # Map original audio if exists
        cmd.extend(['-map', '0:a?'])
        
        # Map additional audio streams
        for i in range(len(audio_paths)):
            cmd.extend(['-map', f'{i+1}:a'])
        
        # Output settings
        cmd.extend([
            '-c:v', 'copy',  # Copy video without re-encoding
            '-c:a', Config.AUDIO_CODEC,
            '-b:a', Config.AUDIO_BITRATE,
            output_path
        ])
        
        # Run FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        start_time = time.time()
        
        # Monitor progress
        while process.returncode is None:
            elapsed = time.time() - start_time
            if status_message:
                await status_message.edit_text(
                    f"🎵 **Audio Integration in Progress...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏱️ **Elapsed:** `{int(elapsed)}s`\n"
                    f"🔧 **Process:** Adding {len(audio_paths)} audio tracks\n"
                    f"⚡ **Codec:** {Config.AUDIO_CODEC} @ {Config.AUDIO_BITRATE}"
                )
            
            await asyncio.sleep(2)
            
            try:
                await asyncio.wait_for(process.wait(), timeout=0.1)
                break
            except asyncio.TimeoutError:
                continue
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            if stderr:
                error_output = stderr.decode('utf-8', errors='ignore')[-300:]
                LOGGER.error(f"Audio merge FFmpeg error: {error_output}")
            return None
    
    except Exception as e:
        LOGGER.error(f"Audio merge process error: {e}")
        return None

@Client.on_callback_query(filters.regex(r"audio_track_info_(\d+)"))
async def audio_track_info_callback(c: Client, cb: CallbackQuery):
    """Show audio track information"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ Not your files!", show_alert=True)
        return
    
    if user_id not in queueDB:
        await cb.answer("📂 No files in queue!", show_alert=True)
        return
    
    audios = queueDB[user_id].get("audios", [])
    
    if not audios:
        await cb.answer("🎵 No audio files!", show_alert=True)
        return
    
    info_text = (
        f"🎵 **Audio Files Information**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Total Audio Files:** {len(audios)}\n\n"
    )
    
    for i, audio_item in enumerate(audios[:5]):  # Show first 5
        info_text += f"🎵 **Audio {i+1}:** File ID `{audio_item}`\n"
    
    if len(audios) > 5:
        info_text += f"\n... and {len(audios) - 5} more files"
    
    info_text += (
        f"\n\n**Supported Formats:**\n"
        f"{', '.join(AUDIO_EXTENSIONS[:10])}"
    )
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="start_main")]
    ])
    
    await cb.edit_message_text(info_text, reply_markup=back_keyboard)

# Export audio merge functions
__all__ = [
    'merge_audio_callback',
    'start_audio_merge_process', 
    'merge_video_with_audio',
    'audio_track_info_callback'
]
