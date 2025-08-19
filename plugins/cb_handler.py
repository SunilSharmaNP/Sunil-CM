# Enhanced Callback Handler
# Centralized callback query processing for Enhanced MERGE-BOT

import os
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config
from helpers.utils import UserSettings, get_readable_file_size, get_system_info
from templates.keyboards import (
    create_main_keyboard, create_settings_keyboard, create_help_keyboard,
    create_merge_mode_keyboard, create_admin_keyboard, create_confirmation_keyboard
)
from templates.messages import (
    WELCOME_MESSAGE, HELP_MESSAGE, SETTINGS_MAIN, ADMIN_STATS, 
    ABOUT_MESSAGE, format_message_template
)
from __init__ import LOGGER, queueDB, botStartTime
import time
import psutil
import shutil

@Client.on_callback_query(filters.regex(r"start_main"))
async def start_main_callback(c: Client, cb: CallbackQuery):
    """Return to main menu"""
    user = UserSettings(cb.from_user.id, cb.from_user.first_name)
    
    welcome_text = format_message_template(
        WELCOME_MESSAGE,
        user_name=user.name,
        owner_username=Config.OWNER_USERNAME
    )
    
    keyboard = create_main_keyboard()
    await cb.edit_message_text(welcome_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"help_main"))
async def help_main_callback(c: Client, cb: CallbackQuery):
    """Show main help menu"""
    keyboard = create_help_keyboard()
    await cb.edit_message_text(HELP_MESSAGE, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"help_(\w+)"))
async def help_topic_callback(c: Client, cb: CallbackQuery):
    """Show specific help topics"""
    topic = cb.matches[0].group(1)
    
    help_topics = {
        "video": """📹 **Video Merge Guide**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Step-by-step process:**
1️⃣ Send 2 or more video files to the bot
2️⃣ Videos can be files or direct download links
3️⃣ Use `/merge` or **Merge Now** button
4️⃣ Wait for processing (auto-detects best method)
5️⃣ Choose upload destination

**Supported formats:**
• MP4, MKV, AVI, MOV, WEBM, FLV
• Up to 10 videos per merge
• Mixed formats automatically handled

**Quality modes:**
• **Fast:** Stream copy (if compatible)
• **Robust:** Re-encode with quality preservation
• **Auto-detect:** Best method selected automatically

**Pro Tips:**
• Send files in desired merge order
• Ensure good internet for large files
• Use compression for smaller output""",

        "audio": """🎵 **Audio Merge Guide**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**How to add audio tracks:**
1️⃣ Send 1 video file
2️⃣ Send 1 or more audio files  
3️⃣ Set merge mode to "Audio Merge"
4️⃣ Use **Merge Now** to start process
5️⃣ Audio tracks will be added to video

**Supported audio formats:**
• MP3, AAC, FLAC, WAV, OGG, M4A
• Multiple language tracks supported
• Original video quality preserved

**Features:**
• Multiple audio tracks per video
• Language metadata preservation
• Audio codec conversion if needed
• Bitrate optimization""",

        "subtitle": """📄 **Subtitle Merge Guide**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Adding subtitles to videos:**
1️⃣ Send 1 video file
2️⃣ Send subtitle files (SRT, ASS, VTT)
3️⃣ Set merge mode to "Subtitle Merge"
4️⃣ Process will soft-mux subtitles
5️⃣ Subtitles become selectable in players

**Supported formats:**
• SRT (SubRip)
• ASS/SSA (Advanced SubStation)
• VTT (WebVTT)
• SUB/IDX (VobSub)

**Benefits:**
• Soft-mux preserves video quality
• Multiple language support
• Compatible with most players
• Easy enable/disable in players""",

        "extract": """🔍 **Stream Extract Guide**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Extract audio/subtitle streams:**
1️⃣ Send video file(s)
2️⃣ Set merge mode to "Extract Streams"
3️⃣ Choose what to extract
4️⃣ Get separate files for each stream

**What can be extracted:**
• Audio tracks (as MP3, AAC, FLAC)
• Subtitle tracks (as SRT, ASS)
• Video streams (different qualities)
• Metadata and thumbnails

**Use cases:**
• Get audio for music/podcasts
• Extract subtitles for translation
• Backup specific streams
• Convert between formats""",

        "settings": """⚙️ **Settings Guide**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Customization options:**

**🎬 Merge Mode:**
• Video Merge: Combine videos
• Audio Merge: Add audio tracks
• Subtitle Merge: Add subtitles
• Extract Streams: Get separate files

**📤 Upload Settings:**
• Telegram: Direct upload (2GB/4GB)
• GoFile: External links (unlimited)
• Google Drive: Cloud storage
• As Document: Preserve filename

**🖼️ Thumbnail:**
• Auto-generate from video middle
• Upload custom thumbnail image
• Thumbnail appears in players

**🗜️ Compression:**
• Best Quality: Minimal compression
• Balanced: Size vs quality balance
• Small Size: Maximum compression
• Custom: Manual settings""",

        "faq": """❓ **Frequently Asked Questions**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Q: What's the file size limit?**
A: Free users: 2GB, Premium: 4GB per file

**Q: How many files can I merge?**
A: Up to 10 videos in a single merge operation

**Q: Do you store my files?**
A: Files are automatically deleted after processing

**Q: What if my files are incompatible?**
A: The bot auto-detects and converts formats as needed

**Q: Can I merge different video qualities?**
A: Yes, output will match the highest quality input

**Q: How long does processing take?**
A: Depends on file sizes. Usually 1-5 minutes

**Q: What about audio/video sync?**
A: Advanced algorithms ensure perfect sync

**Q: Can I cancel a running process?**
A: Use the Cancel button during processing

**Q: Is there a queue limit?**
A: 10 files maximum per user at a time"""
    }
    
    if topic in help_topics:
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Help", callback_data="help_main")]
        ])
        await cb.edit_message_text(help_topics[topic], reply_markup=back_keyboard)
    else:
        await cb.answer("❌ Help topic not found!", show_alert=True)

@Client.on_callback_query(filters.regex(r"settings_main"))
async def settings_main_callback(c: Client, cb: CallbackQuery):
    """Show main settings menu"""
    user = UserSettings(cb.from_user.id, cb.from_user.first_name)
    
    settings_text = format_message_template(
        SETTINGS_MAIN,
        merge_mode=user.get_merge_mode_text(),
        upload_mode="Document" if user.upload_as_doc else "Video",
        thumbnail_status="Custom" if user.custom_thumbnail else "Auto-generated",
        compression_status="Enabled" if user.compression_enabled else "Disabled",
        language=user.language.upper(),
        autoclean_status="Enabled" if user.auto_delete else "Disabled",
        user_name=user.name,
        user_id=user.user_id,
        join_date="Recently",  # Can be enhanced with actual date
        user_status="Premium" if Config.IS_PREMIUM else "Free"
    )
    
    keyboard = create_settings_keyboard(user.user_id)
    await cb.edit_message_text(settings_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"setting_merge_mode_(\d+)"))
async def setting_merge_mode_callback(c: Client, cb: CallbackQuery):
    """Show merge mode selection"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ Access denied!", show_alert=True)
        return
    
    user = UserSettings(user_id, cb.from_user.first_name)
    keyboard = create_merge_mode_keyboard(user_id, user.merge_mode)
    
    mode_text = """🎬 **Select Merge Mode**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose how you want to process your files:

**📹 Video Merge:** Combine multiple videos
**🎵 Audio Merge:** Add audio tracks to video  
**📄 Subtitle Merge:** Add subtitles to video
**🔍 Extract Streams:** Get audio/subtitle files

Select your preferred mode below:"""
    
    await cb.edit_message_text(mode_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"set_merge_mode_(\d+)_(\d+)"))
async def set_merge_mode_callback(c: Client, cb: CallbackQuery):
    """Set user's merge mode"""
    user_id = int(cb.matches[0].group(1))
    mode_id = int(cb.matches.group(2))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ Access denied!", show_alert=True)
        return
    
    user = UserSettings(user_id, cb.from_user.first_name)
    user.merge_mode = mode_id
    user.set()
    
    mode_names = ["📹 Video Merge", "🎵 Audio Merge", "📄 Subtitle Merge", "🔍 Extract Streams"]
    mode_name = mode_names[mode_id - 1] if 1 <= mode_id <= 4 else "Video Merge"
    
    await cb.answer(f"✅ Merge mode set to: {mode_name}", show_alert=True)
    
    # Return to settings
    await settings_main_callback(c, cb)

@Client.on_callback_query(filters.regex(r"queue_view"))
async def queue_view_callback(c: Client, cb: CallbackQuery):
    """Show current queue status"""
    user_id = cb.from_user.id
    
    if user_id not in queueDB:
        await cb.answer("📂 Queue is empty!", show_alert=True)
        return
    
    videos = queueDB[user_id].get("videos", [])
    audios = queueDB[user_id].get("audios", [])
    subtitles = queueDB[user_id].get("subtitles", [])
    
    total_items = len(videos) + len(audios) + len(subtitles)
    
    if total_items == 0:
        await cb.answer("📂 Queue is empty!", show_alert=True)
        return
    
    queue_text = f"""📋 **Current Queue Status**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📹 **Videos:** {len(videos)} files
🎵 **Audio:** {len(audios)} files  
📄 **Subtitles:** {len(subtitles)} files

📊 **Total Items:** {total_items}
⏱️ **Estimated Time:** {total_items * 30}s

{'🚀 **Ready to merge!**' if len(videos) >= 2 else '➕ **Add more videos to merge**'}"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Merge Now", callback_data="merge_now")] if len(videos) >= 2 else [],
        [
            InlineKeyboardButton("🗑️ Clear Queue", callback_data=f"queue_clear_{user_id}"),
            InlineKeyboardButton("🔙 Back", callback_data="start_main")
        ]
    ])
    
    await cb.edit_message_text(queue_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"queue_clear_(\d+)"))
async def queue_clear_callback(c: Client, cb: CallbackQuery):
    """Clear user's queue with confirmation"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ Access denied!", show_alert=True)
        return
    
    if user_id not in queueDB:
        await cb.answer("📂 Queue is already empty!", show_alert=True)
        return
    
    total_items = sum(len(queueDB[user_id].get(t, [])) for t in ["videos", "audios", "subtitles"])
    
    if total_items == 0:
        await cb.answer("📂 Queue is already empty!", show_alert=True)
        return
    
    confirm_text = f"""🗑️ **Clear Queue Confirmation**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**This will remove:**
📹 Videos: {len(queueDB[user_id].get('videos', []))} files
🎵 Audio: {len(queueDB[user_id].get('audios', []))} files
📄 Subtitles: {len(queueDB[user_id].get('subtitles', []))} files

📊 **Total:** {total_items} items will be removed

⚠️ **This action cannot be undone!**"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Clear", callback_data=f"confirm_clear_{user_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="queue_view")
        ]
    ])
    
    await cb.edit_message_text(confirm_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"confirm_clear_(\d+)"))
async def confirm_clear_callback(c: Client, cb: CallbackQuery):
    """Confirm and clear queue"""
    user_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != user_id:
        await cb.answer("❌ Access denied!", show_alert=True)
        return
    
    if user_id in queueDB:
        queueDB[user_id] = {"videos": [], "audios": [], "subtitles": []}
    
    await cb.edit_message_text(
        "✅ **Queue Cleared Successfully!**\n\n"
        "All files have been removed from your queue.\n"
        "You can start adding new files now!"
    )
    
    await cb.answer("Queue cleared successfully!", show_alert=True)

@Client.on_callback_query(filters.regex(r"about_main"))
async def about_main_callback(c: Client, cb: CallbackQuery):
    """Show about information"""
    # Get some stats for about page
    total_users = len(queueDB) if queueDB else 0
    
    about_text = format_message_template(
        ABOUT_MESSAGE,
        owner_username=Config.OWNER_USERNAME,
        user_count=total_users,
        file_count="1000+"  # Can be tracked with actual counter
    )
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="start_main")]
    ])
    
    await cb.edit_message_text(about_text, reply_markup=back_keyboard)

@Client.on_callback_query(filters.regex(r"stats_main"))
async def stats_main_callback(c: Client, cb: CallbackQuery):
    """Show bot statistics (owner only)"""
    if cb.from_user.id != int(Config.OWNER):
        await cb.answer("🔒 Owner only command!", show_alert=True)
        return
    
    # Get system info
    uptime = time.time() - botStartTime
    total, used, free = shutil.disk_usage(".")
    cpu_usage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk_usage = (used / total) * 100
    
    stats_text = format_message_template(
        ADMIN_STATS,
        uptime=f"{int(uptime//3600)}h {int((uptime%3600)//60)}m",
        cpu_usage=cpu_usage,
        memory_usage=memory,
        disk_usage=f"{disk_usage:.1f}",
        disk_used=get_readable_file_size(used),
        disk_total=get_readable_file_size(total),
        free_space=get_readable_file_size(free),
        bytes_sent=get_readable_file_size(psutil.net_io_counters().bytes_sent),
        bytes_received=get_readable_file_size(psutil.net_io_counters().bytes_recv),
        total_users=len(queueDB),
        active_sessions=len([q for q in queueDB.values() if q.get('videos')]),
        files_processed="N/A",
        avg_speed="N/A",
        version="6.0"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="stats_main"),
            InlineKeyboardButton("👨‍💼 Admin Panel", callback_data="admin_main")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="start_main")]
    ])
    
    await cb.edit_message_text(stats_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"admin_main"))
async def admin_main_callback(c: Client, cb: CallbackQuery):
    """Show admin panel (owner only)"""
    if cb.from_user.id != int(Config.OWNER):
        await cb.answer("🔒 Owner only!", show_alert=True)
        return
    
    admin_text = """👨‍💼 **Enhanced MERGE-BOT Admin Panel**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**System Management:**
• Monitor bot statistics and performance
• Manage user access and permissions
• Broadcast messages to all users
• View system logs and errors

**User Management:**
• Ban/unban users
• View user statistics
• Reset user settings
• Monitor active sessions

**Maintenance:**
• Clean temporary files
• Backup user data
• Update bot configuration
• Restart system services

Choose an option below:"""
    
    keyboard = create_admin_keyboard()
    await cb.edit_message_text(admin_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"noop"))
async def noop_callback(c: Client, cb: CallbackQuery):
    """No-operation callback for pagination buttons"""
    await cb.answer()

# Export callback handlers
__all__ = [
    'start_main_callback',
    'help_main_callback',
    'help_topic_callback',
    'settings_main_callback',
    'setting_merge_mode_callback',
    'set_merge_mode_callback',
    'queue_view_callback',
    'queue_clear_callback',
    'confirm_clear_callback',
    'about_main_callback',
    'stats_main_callback',
    'admin_main_callback',
    'noop_callback'
]
