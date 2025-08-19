# Enhanced Subtitle Merge Plugin
# Advanced subtitle integration with multiple language support

import os
import time
from typing import List, Optional
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config
from helpers.utils import UserSettings, get_readable_file_size, get_video_info
from helpers.ffmpeg_helper import FFmpegHelper
from __init__ import LOGGER, queueDB, SUBTITLE_EXTENSIONS

@Client.on_callback_query(filters.regex(r"merge_subtitles_(\d+)"))
async def merge_subtitles_callback(c: Client, cb: CallbackQuery):
    """Handle subtitle merge process"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ This is not your merge operation!", show_alert=True)
        return
    
    user = UserSettings(user_id, cb.from_user.first_name)
    
    # Check if user has video and subtitle files
    if user_id not in queueDB:
        await cb.answer("📂 No files in queue!", show_alert=True)
        return
    
    videos = queueDB[user_id].get("videos", [])
    subtitles = queueDB[user_id].get("subtitles", [])
    
    if not videos:
        await cb.answer("📹 No video files found!", show_alert=True)
        return
    
    if not subtitles:
        await cb.answer("📄 No subtitle files found!", show_alert=True)
        return
    
    await start_subtitle_merge_process(c, cb, user_id, user, videos, subtitles)

async def start_subtitle_merge_process(
    c: Client, 
    cb: CallbackQuery, 
    user_id: int, 
    user: UserSettings,
    video_files: List,
    subtitle_files: List
):
    """Enhanced subtitle merge process"""
    try:
        await cb.edit_message_text(
            f"📄 **Enhanced Subtitle Merge Starting...**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📹 **Video Files:** {len(video_files)}\n"
            f"📄 **Subtitle Files:** {len(subtitle_files)}\n"
            f"🎯 **User:** {user.name}\n"
            f"🔄 **Status:** Preparing subtitle integration..."
        )
        
        # Download video file (use first one)
        video_item = video_files[0]
        await cb.edit_message_text(
            f"📥 **Downloading Video...**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 **Status:** Processing main video file"
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
        
        if not video_path or not os.path.exists(video_path):
            await cb.edit_message_text("❌ Failed to download video file!")
            return
        
        # Download subtitle files
        subtitle_paths = []
        for i, subtitle_item in enumerate(subtitle_files):
            await cb.edit_message_text(
                f"📥 **Downloading Subtitles...**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔄 **Progress:** {i+1}/{len(subtitle_files)}\n"
                f"📄 **Processing:** Subtitle {i+1}"
            )
            
            if isinstance(subtitle_item, str):  # URL
                from helpers.downloader import EnhancedDownloader
                downloader = EnhancedDownloader(user_id)
                subtitle_path = await downloader.download_from_url(subtitle_item, cb.message)
                await downloader.cleanup()
            else:  # Message ID
                message = await c.get_messages(chat_id=user_id, message_ids=subtitle_item)
                from helpers.downloader import download_from_tg
                subtitle_path = await download_from_tg(message, user_id, cb.message)
            
            if subtitle_path and os.path.exists(subtitle_path):
                subtitle_paths.append(subtitle_path)
            else:
                LOGGER.warning(f"Failed to download subtitle {i+1}")
        
        if not subtitle_paths:
            await cb.edit_message_text("❌ No subtitles could be downloaded!")
            return
        
        # Start subtitle integration
        await cb.edit_message_text(
            f"📄 **Subtitle Integration Phase**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 **Status:** Adding {len(subtitle_paths)} subtitle tracks\n"
            f"⚡ **Method:** Soft-mux (preserves video quality)\n"
            f"🎯 **Compatibility:** Universal player support"
        )
        
        merged_path = await merge_video_with_subtitles(
            video_path, subtitle_paths, user_id, cb.message
        )
        
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
                [InlineKeyboardButton("📋 Subtitle Info", callback_data=f"subtitle_info_{user_id}")],
                [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_upload_{user_id}")]
            ])
            
            success_text = (
                f"✅ **Subtitle Integration Completed!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📁 **Output:** `{os.path.basename(merged_path)}`\n"
                f"📊 **Size:** `{get_readable_file_size(file_size)}`\n"
                f"📄 **Subtitles:** {len(subtitle_paths)} tracks added\n"
                f"🎬 **Duration:** `{file_info.get('duration', 0)}s`\n"
                f"🔧 **Method:** Soft-mux (no quality loss)\n"
                f"📱 **Compatibility:** All modern players\n\n"
                f"🚀 **Choose upload destination:**"
            )
            
            await cb.edit_message_text(success_text, reply_markup=keyboard)
            
            # Clear queues
            queueDB[user_id]["videos"].clear()
            queueDB[user_id]["subtitles"].clear()
        else:
            await cb.edit_message_text("❌ Subtitle integration failed! Please try again.")
    
    except Exception as e:
        LOGGER.error(f"Subtitle merge error for user {user_id}: {e}")
        await cb.edit_message_text(f"❌ **Subtitle merge failed:** `{str(e)}`")

async def merge_video_with_subtitles(
    video_path: str, 
    subtitle_paths: List[str], 
    user_id: int, 
    status_message
) -> Optional[str]:
    """Merge video with multiple subtitle tracks using FFmpeg"""
    try:
        output_filename = f"video_with_subtitles_{user_id}_{int(time.time())}.mp4"
        output_path = os.path.join(f"downloads/{user_id}", output_filename)
        
        # Use FFmpeg helper for subtitle integration
        ffmpeg_helper = FFmpegHelper()
        
        # Progress callback
        async def progress_callback(stage, elapsed):
            if status_message:
                await status_message.edit_text(
                    f"📄 **Subtitle Integration in Progress...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏱️ **Elapsed:** `{int(elapsed)}s`\n"
                    f"🔧 **Stage:** {stage}\n"
                    f"📄 **Tracks:** Adding {len(subtitle_paths)} subtitles\n"
                    f"⚡ **Method:** Soft-mux preservation"
                )
        
        # Start subtitle integration
        success = await ffmpeg_helper.add_subtitles_to_video(
            video_path, subtitle_paths, output_path, progress_callback
        )
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            return None
            
    except Exception as e:
        LOGGER.error(f"Subtitle integration process error: {e}")
        return None

@Client.on_callback_query(filters.regex(r"subtitle_info_(\d+)"))
async def subtitle_info_callback(c: Client, cb: CallbackQuery):
    """Show subtitle track information"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ Not your files!", show_alert=True)
        return
    
    # Get merged file info
    if user_id not in queueDB or "merged_file" not in queueDB[user_id]:
        await cb.answer("❌ No merged file found!", show_alert=True)
        return
    
    file_info = queueDB[user_id]["merged_file"]
    video_info = file_info.get("info", {})
    
    # Get subtitle stream information
    subtitle_streams = video_info.get('subtitle_streams', [])
    
    info_text = (
        f"📄 **Subtitle Track Information**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 **File:** `{file_info['filename']}`\n"
        f"📊 **Total Size:** `{get_readable_file_size(file_info['size'])}`\n"
        f"📄 **Subtitle Tracks:** {len(subtitle_streams)}\n\n"
    )
    
    if subtitle_streams:
        for i, sub_stream in enumerate(subtitle_streams[:5]):  # Show first 5
            language = sub_stream.get('language', 'Unknown')
            codec = sub_stream.get('codec', 'Unknown')
            title = sub_stream.get('title', f'Track {i+1}')
            
            info_text += (
                f"📄 **Track {i+1}:**\n"
                f"   • Language: `{language}`\n"
                f"   • Codec: `{codec}`\n"
                f"   • Title: `{title}`\n\n"
            )
        
        if len(subtitle_streams) > 5:
            info_text += f"... and {len(subtitle_streams) - 5} more tracks\n\n"
    else:
        info_text += "❌ No subtitle track information available\n\n"
    
    info_text += (
        f"**📱 Player Compatibility:**\n"
        f"• VLC Media Player: ✅\n"
        f"• MX Player: ✅\n"
        f"• Kodi: ✅\n"
        f"• Web browsers: ✅\n"
        f"• Smart TVs: ✅\n\n"
        f"**🎯 Features:**\n"
        f"• Selectable in player menu\n"
        f"• No quality loss (soft-mux)\n"
        f"• Multi-language support\n"
        f"• Universal compatibility"
    )
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Upload", callback_data=f"upload_options_{user_id}")]
    ])
    
    await cb.edit_message_text(info_text, reply_markup=back_keyboard)

@Client.on_callback_query(filters.regex(r"subtitle_extract_(\d+)"))
async def subtitle_extract_callback(c: Client, cb: CallbackQuery):
    """Extract subtitles from video file"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ Access denied!", show_alert=True)
        return
    
    if user_id not in queueDB or not queueDB[user_id].get("videos"):
        await cb.answer("📹 No video files found!", show_alert=True)
        return
    
    try:
        video_item = queueDB[user_id]["videos"][0]
        
        await cb.edit_message_text(
            f"🔍 **Subtitle Extraction Starting...**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 **Status:** Analyzing video for subtitle streams\n"
            f"📹 **Processing:** Main video file"
        )
        
        # Download video
        if isinstance(video_item, str):  # URL
            from helpers.downloader import EnhancedDownloader
            downloader = EnhancedDownloader(user_id)
            video_path = await downloader.download_from_url(video_item, cb.message)
            await downloader.cleanup()
        else:  # Message ID
            message = await c.get_messages(chat_id=user_id, message_ids=video_item)
            from helpers.downloader import download_from_tg
            video_path = await download_from_tg(message, user_id, cb.message)
        
        if not video_path or not os.path.exists(video_path):
            await cb.edit_message_text("❌ Failed to download video file!")
            return
        
        # Extract subtitles
        output_dir = f"downloads/{user_id}/subtitles"
        os.makedirs(output_dir, exist_ok=True)
        
        ffmpeg_helper = FFmpegHelper()
        extracted_files = await ffmpeg_helper.extract_subtitles(video_path, output_dir)
        
        if extracted_files:
            # Send extracted subtitle files
            for subtitle_file in extracted_files:
                try:
                    await c.send_document(
                        chat_id=user_id,
                        document=subtitle_file,
                        caption=f"📄 **Extracted Subtitle**\nFrom: `{os.path.basename(video_path)}`"
                    )
                    
                    # Clean up after sending
                    os.remove(subtitle_file)
                    
                except Exception as e:
                    LOGGER.error(f"Failed to send subtitle file: {e}")
            
            await cb.edit_message_text(
                f"✅ **Subtitle Extraction Completed!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📄 **Extracted:** {len(extracted_files)} subtitle files\n"
                f"📤 **Status:** Files sent to chat\n\n"
                f"**Files extracted and sent to your chat!**"
            )
        else:
            await cb.edit_message_text(
                f"❌ **No Subtitles Found!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📹 **Video:** `{os.path.basename(video_path)}`\n"
                f"📄 **Result:** No subtitle streams detected\n\n"
                f"This video doesn't contain embedded subtitles."
            )
    
    except Exception as e:
        LOGGER.error(f"Subtitle extraction error: {e}")
        await cb.edit_message_text(f"❌ **Extraction failed:** `{str(e)}`")

# Export subtitle merge functions
__all__ = [
    'merge_subtitles_callback',
    'start_subtitle_merge_process',
    'merge_video_with_subtitles', 
    'subtitle_info_callback',
    'subtitle_extract_callback'
]
