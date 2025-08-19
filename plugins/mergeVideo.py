# Enhanced Video Merge Plugin
# Combines old repo UI with new repo core functionality

import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import Config
from helpers.merger import EnhancedMerger, merge_videos
from helpers.uploader import EnhancedTelegramUploader, GoFileUploader
from helpers.utils import UserSettings, get_readable_file_size, get_readable_time, get_video_info
from templates.keyboards import create_upload_options_keyboard, create_confirmation_keyboard
from templates.messages import MERGE_SUCCESS, get_error_message
from __init__ import LOGGER, queueDB, performance_monitor

@Client.on_callback_query(filters.regex(r"merge_now"))
async def merge_now_callback(c: Client, cb: CallbackQuery):
    """Handle merge now button from main interface"""
    user_id = cb.from_user.id
    user = UserSettings(user_id, cb.from_user.first_name)
    
    # Authentication check
    if user_id != int(Config.OWNER) and not user.allowed:
        await cb.answer("🔒 Access denied! Use /login first.", show_alert=True)
        return
    
    # Check queue
    if user_id not in queueDB or not queueDB[user_id].get("videos"):
        await cb.answer("📂 Queue is empty! Send some videos first.", show_alert=True)
        return
    
    queue_size = len(queueDB[user_id]["videos"])
    if queue_size < 2:
        await cb.answer(f"📹 Need at least 2 videos! Current: {queue_size}", show_alert=True)
        return
    
    # Start merge process
    await cb.answer("🚀 Starting enhanced merge process...")
    await start_video_merge_process(c, cb, user_id, user)

@Client.on_callback_query(filters.regex(r"merge_start_(\d+)"))
async def merge_start_callback(c: Client, cb: CallbackQuery):
    """Handle merge start from queue management"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ This is not your merge operation!", show_alert=True)
        return
    
    user = UserSettings(user_id, cb.from_user.first_name)
    await start_video_merge_process(c, cb, user_id, user)

async def start_video_merge_process(c: Client, cb: CallbackQuery, user_id: int, user: UserSettings):
    """Enhanced video merge process with progress tracking"""
    try:
        queue = queueDB[user_id]["videos"]
        queue_size = len(queue)
        
        # Create initial status message
        status_text = (
            f"🚀 **Enhanced Video Merge Starting...**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Queue Size:** {queue_size} videos\n"
            f"⚙️ **Mode:** {user.get_merge_mode_text()}\n"
            f"🎯 **User:** {user.name}\n"
            f"🔄 **Status:** Initializing enhanced workflow...\n\n"
            f"⏳ Please wait while we process your videos..."
        )
        
        await cb.edit_message_text(status_text)
        
        # Initialize enhanced merger
        merger = EnhancedMerger(user_id)
        
        # Phase 1: Download all videos
        video_paths = []
        total_size = 0
        
        for i, item in enumerate(queue):
            await cb.edit_message_text(
                f"📥 **Enhanced Download Phase**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔄 **Progress:** {i+1}/{queue_size}\n"
                f"📁 **Processing:** Video {i+1}\n"
                f"⏳ **Status:** Downloading..."
            )
            
            try:
                if isinstance(item, str):  # URL
                    from helpers.downloader import EnhancedDownloader
                    downloader = EnhancedDownloader(user_id)
                    file_path = await downloader.download_from_url(item, cb.message)
                    await downloader.cleanup()
                else:  # Message ID
                    message = await c.get_messages(chat_id=user_id, message_ids=item)
                    from helpers.downloader import download_from_tg
                    file_path = await download_from_tg(message, user_id, cb.message)
                
                if not file_path or not os.path.exists(file_path):
                    await cb.edit_message_text(
                        f"❌ **Download Failed!**\n"
                        f"Failed to download video {i+1}/{queue_size}\n\n"
                        f"**Action:** Merge cancelled\n"
                        f"**Suggestion:** Check files and try again"
                    )
                    return
                
                video_paths.append(file_path)
                total_size += os.path.getsize(file_path)
                
            except Exception as e:
                LOGGER.error(f"Download error for user {user_id}: {e}")
                await cb.edit_message_text(
                    f"❌ **Download Error!**\n"
                    f"Error downloading video {i+1}: `{str(e)}`\n\n"
                    f"Please try again or contact support."
                )
                return
        
        # Phase 2: Merge videos
        await cb.edit_message_text(
            f"🔧 **Enhanced Merge Phase**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Input Videos:** {len(video_paths)}\n"
            f"💾 **Total Size:** `{get_readable_file_size(total_size)}`\n"
            f"⚡ **Engine:** Enhanced hybrid merger\n"
            f"🔄 **Status:** Starting merge process..."
        )
        
        # Generate output filename
        timestamp = int(time.time())
        output_filename = f"merged_video_{user_id}_{timestamp}.mp4"
        
        # Start merge
        merged_path = await merger.merge_videos(video_paths, cb.message, output_filename)
        
        if not merged_path:
            await cb.edit_message_text(
                "❌ **Merge Failed!**\n"
                "The merge process encountered an error.\n\n"
                "Please check your videos and try again."
            )
            await merger.cleanup()
            return
        
        # Phase 3: Success - Show upload options
        file_size = os.path.getsize(merged_path)
        file_info = get_video_info(merged_path)
        
        # Store merged file info for upload callbacks
        queueDB[user_id]["merged_file"] = {
            "path": merged_path,
            "filename": os.path.basename(merged_path),
            "size": file_size,
            "info": file_info
        }
        
        # Create upload options keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Telegram", callback_data=f"upload_telegram_{user_id}")],
            [InlineKeyboardButton("🔗 GoFile.io", callback_data=f"upload_gofile_{user_id}")],
            [InlineKeyboardButton("☁️ Google Drive", callback_data=f"upload_gdrive_{user_id}")],
            [InlineKeyboardButton("📋 File Info", callback_data=f"file_info_{user_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_upload_{user_id}")]
        ])
        
        success_text = (
            f"✅ **Video Merge Completed!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 **Output:** `{os.path.basename(merged_path)}`\n"
            f"📊 **Size:** `{get_readable_file_size(file_size)}`\n"
            f"🎬 **Duration:** `{get_readable_time(file_info.get('duration', 0))}`\n"
            f"📺 **Resolution:** `{file_info.get('width', 0)}x{file_info.get('height', 0)}`\n"
            f"⚡ **Merge Type:** Enhanced hybrid\n"
            f"🎯 **Quality:** Original preserved\n\n"
            f"🚀 **Choose upload destination:**"
        )
        
        await cb.edit_message_text(success_text, reply_markup=keyboard)
        
        # Clear the video queue
        queueDB[user_id]["videos"].clear()
        
        # Cleanup merger resources
        await merger.cleanup()
        
        LOGGER.info(f"Video merge completed successfully for user {user_id}")
        
    except Exception as e:
        LOGGER.error(f"Video merge process error for user {user_id}: {e}")
        await cb.edit_message_text(
            f"❌ **Merge Process Failed!**\n\n"
            f"**Error:** `{str(e)}`\n"
            f"**Action:** Process terminated\n\n"
            f"Please try again or contact support if issue persists."
        )

@Client.on_callback_query(filters.regex(r"upload_telegram_(\d+)"))
async def upload_telegram_callback(c: Client, cb: CallbackQuery):
    """Handle Telegram upload"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ This is not your file!", show_alert=True)
        return
    
    # Get merged file info
    if user_id not in queueDB or "merged_file" not in queueDB[user_id]:
        await cb.answer("❌ No merged file found!", show_alert=True)
        return
    
    file_info = queueDB[user_id]["merged_file"]
    file_path = file_info["path"]
    
    if not os.path.exists(file_path):
        await cb.answer("❌ File not found!", show_alert=True)
        return
    
    try:
        # Check file size limits
        file_size = file_info["size"]
        max_size = 4 * 1024 * 1024 * 1024 if Config.IS_PREMIUM else 2 * 1024 * 1024 * 1024
        
        if file_size > max_size:
            size_limit = "4GB" if Config.IS_PREMIUM else "2GB"
            await cb.edit_message_text(
                f"❌ **File Too Large for Telegram!**\n\n"
                f"**File Size:** `{get_readable_file_size(file_size)}`\n"
                f"**Telegram Limit:** `{size_limit}`\n\n"
                f"**Alternative:** Use GoFile.io for unlimited uploads",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Upload to GoFile", callback_data=f"upload_gofile_{user_id}")],
                    [InlineKeyboardButton("🔙 Back", callback_data=f"upload_options_{user_id}")]
                ])
            )
            return
        
        await cb.answer("📤 Starting Telegram upload...")
        
        # Initialize uploader
        uploader = EnhancedTelegramUploader(c)
        user = UserSettings(user_id, cb.from_user.first_name)
        
        # Start upload
        success = await uploader.upload_to_telegram(
            chat_id=user_id,
            file_path=file_path,
            status_message=cb.message,
            upload_as_document=user.upload_as_doc
        )
        
        if success:
            # Clean up
            try:
                os.remove(file_path)
            except:
                pass
            
            # Remove from queue
            if "merged_file" in queueDB[user_id]:
                del queueDB[user_id]["merged_file"]
        
    except Exception as e:
        LOGGER.error(f"Telegram upload error: {e}")
        await cb.edit_message_text(f"❌ **Upload failed:** `{str(e)}`")

@Client.on_callback_query(filters.regex(r"upload_gofile_(\d+)"))
async def upload_gofile_callback(c: Client, cb: CallbackQuery):
    """Handle GoFile upload"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ This is not your file!", show_alert=True)
        return
    
    # Get merged file info
    if user_id not in queueDB or "merged_file" not in queueDB[user_id]:
        await cb.answer("❌ No merged file found!", show_alert=True)
        return
    
    file_info = queueDB[user_id]["merged_file"]
    file_path = file_info["path"]
    
    if not os.path.exists(file_path):
        await cb.answer("❌ File not found!", show_alert=True)
        return
    
    try:
        await cb.answer("🔗 Starting GoFile upload...")
        
        # Initialize GoFile uploader
        uploader = GoFileUploader(Config.GOFILE_TOKEN)
        
        # Start upload with progress
        download_link = await uploader.upload_file(file_path, cb.message)
        
        if download_link:
            file_size = get_readable_file_size(file_info["size"])
            filename = file_info["filename"]
            
            # Success message
            await cb.edit_message_text(
                f"✅ **GoFile Upload Completed!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📁 **File:** `{filename}`\n"
                f"📊 **Size:** `{file_size}`\n"
                f"🔗 **Link:** {download_link}\n\n"
                f"**Features:**\n"
                f"• No download limits\n"
                f"• High-speed servers\n"
                f"• Direct browser playback\n\n"
                f"Thank you for using Enhanced MERGE-BOT! 🎉"
            )
            
            # Clean up
            try:
                os.remove(file_path)
            except:
                pass
            
            # Remove from queue
            if "merged_file" in queueDB[user_id]:
                del queueDB[user_id]["merged_file"]
        
    except Exception as e:
        LOGGER.error(f"GoFile upload error: {e}")
        await cb.edit_message_text(f"❌ **GoFile upload failed:** `{str(e)}`")

@Client.on_callback_query(filters.regex(r"upload_gdrive_(\d+)"))
async def upload_gdrive_callback(c: Client, cb: CallbackQuery):
    """Handle Google Drive upload"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ This is not your file!", show_alert=True)
        return
    
    if not Config.IS_PREMIUM:
        await cb.answer("⚠️ Google Drive requires premium features!", show_alert=True)
        return
    
    # Get merged file info
    if user_id not in queueDB or "merged_file" not in queueDB[user_id]:
        await cb.answer("❌ No merged file found!", show_alert=True)
        return
    
    file_info = queueDB[user_id]["merged_file"]
    file_path = file_info["path"]
    
    if not os.path.exists(file_path):
        await cb.answer("❌ File not found!", show_alert=True)
        return
    
    try:
        await cb.answer("☁️ Starting Google Drive upload...")
        
        # Use rclone upload from helpers
        from helpers.rclone_upload import rclone_upload
        
        upload_result = await rclone_upload(file_path, cb.message)
        
        if upload_result:
            await cb.edit_message_text(
                f"✅ **Google Drive Upload Completed!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📁 **File:** `{file_info['filename']}`\n"
                f"📊 **Size:** `{get_readable_file_size(file_info['size'])}`\n"
                f"☁️ **Location:** Google Drive\n\n"
                f"**Benefits:**\n"
                f"• Permanent cloud storage\n"
                f"• Easy sharing options\n"
                f"• Integration with Google services\n\n"
                f"Thank you for using Enhanced MERGE-BOT! 🎉"
            )
            
            # Clean up
            try:
                os.remove(file_path)
            except:
                pass
            
            # Remove from queue
            if "merged_file" in queueDB[user_id]:
                del queueDB[user_id]["merged_file"]
        
    except Exception as e:
        LOGGER.error(f"Google Drive upload error: {e}")
        await cb.edit_message_text(f"❌ **Google Drive upload failed:** `{str(e)}`")

@Client.on_callback_query(filters.regex(r"file_info_(\d+)"))
async def file_info_callback(c: Client, cb: CallbackQuery):
    """Show detailed file information"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ This is not your file!", show_alert=True)
        return
    
    # Get merged file info
    if user_id not in queueDB or "merged_file" not in queueDB[user_id]:
        await cb.answer("❌ No merged file found!", show_alert=True)
        return
    
    file_info = queueDB[user_id]["merged_file"]
    video_info = file_info.get("info", {})
    
    info_text = (
        f"📋 **Merged Video Information**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 **Filename:** `{file_info['filename']}`\n"
        f"📊 **Size:** `{get_readable_file_size(file_info['size'])}`\n"
        f"🎬 **Duration:** `{get_readable_time(video_info.get('duration', 0))}`\n"
        f"📺 **Resolution:** `{video_info.get('width', 0)}x{video_info.get('height', 0)}`\n"
        f"🎵 **Audio Codec:** `{video_info.get('audio_codec', 'Unknown')}`\n"
        f"🔧 **Video Codec:** `{video_info.get('video_codec', 'Unknown')}`\n"
        f"📈 **Bitrate:** `{video_info.get('bitrate', 0)} kbps`\n\n"
        f"**Compatibility:**\n"
        f"• Modern devices: ✅\n"
        f"• Web browsers: ✅\n"
        f"• Mobile players: ✅\n"
        f"• Social media: ✅"
    )
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Upload", callback_data=f"upload_options_{user_id}")]
    ])
    
    await cb.edit_message_text(info_text, reply_markup=back_keyboard)

@Client.on_callback_query(filters.regex(r"cancel_upload_(\d+)"))
async def cancel_upload_callback(c: Client, cb: CallbackQuery):
    """Cancel upload and clean up"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ This is not your operation!", show_alert=True)
        return
    
    # Clean up merged file
    if user_id in queueDB and "merged_file" in queueDB[user_id]:
        try:
            file_path = queueDB[user_id]["merged_file"]["path"]
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        
        del queueDB[user_id]["merged_file"]
    
    await cb.edit_message_text(
        "❌ **Upload Cancelled**\n\n"
        "The merged file has been deleted.\n"
        "You can start a new merge operation anytime!"
    )
    
    await cb.answer("Upload cancelled and file cleaned up", show_alert=True)

# Export plugin functions
__all__ = [
    'merge_now_callback',
    'merge_start_callback', 
    'start_video_merge_process',
    'upload_telegram_callback',
    'upload_gofile_callback',
    'upload_gdrive_callback',
    'file_info_callback',
    'cancel_upload_callback'
]
