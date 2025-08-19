# Enhanced MERGE-BOT - Main Bot Entry Point
# Combines rich UI from yashoswalyo/MERGE-BOT with modern core from SunilSharmaNP/Sunil-CM

import os
import shutil
import time
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config.env", override=True)

import psutil
import pyromod
from PIL import Image
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, InputUserDeactivated, PeerIdInvalid, UserIsBlocked
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, User

# Enhanced imports
from __init__ import (
    LOGGER, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS, SUBTITLE_EXTENSIONS,
    MERGE_MODE, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE, bMaker, formatDB, 
    gDict, queueDB, replyDB, BROADCAST_MSG
)
from config import Config
from helpers import database
from helpers.downloader import EnhancedDownloader, download_from_url, download_from_tg
from helpers.merger import EnhancedMerger, merge_videos
from helpers.uploader import EnhancedTelegramUploader, GoFileUploader
from helpers.utils import UserSettings, get_readable_file_size, get_readable_time

# Bot initialization
botStartTime = time.time()
parent_id = Config.GDRIVE_FOLDER_ID

class EnhancedMergeBot(Client):
    """Enhanced MergeBot combining old repo UI with new repo core"""
    
    def start(self):
        super().start()
        try:
            self.send_message(
                chat_id=int(Config.OWNER), 
                text="**🚀 Enhanced MERGE-BOT v6.0 Started!**\n\n"
                     "✅ Rich UI + Modern Core\n"
                     "✅ All original features preserved\n"
                     "✅ New: GoFile integration\n"
                     "✅ New: Smart progress tracking\n"
                     "✅ New: Robust merge engine"
            )
            LOGGER.info("Enhanced Bot Started Successfully!")
        except Exception as err:
            LOGGER.error(f"Boot alert failed: {err}")
        return LOGGER.info("Enhanced MERGE-BOT Started!")

    def stop(self):
        super().stop()
        return LOGGER.info("Enhanced MERGE-BOT Stopped")

# Initialize enhanced bot
mergeApp = EnhancedMergeBot(
    name="enhanced-merge-bot",
    api_hash=Config.API_HASH,
    api_id=Config.TELEGRAM_API,
    bot_token=Config.BOT_TOKEN,
    workers=300,
    plugins=dict(root="plugins"),
    app_version="6.0+enhanced-mergebot",
)

# Ensure directories exist
for directory in ["downloads", "logs", "temp"]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# ===== ENHANCED COMMAND HANDLERS =====

@mergeApp.on_message(filters.command(["start"]) & filters.private)
async def start_handler(c: Client, m: Message):
    """Enhanced start command with rich UI"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if m.from_user.id != int(Config.OWNER):
        if not user.allowed:
            await m.reply_text(
                f"👋 **Welcome {m.from_user.first_name}!**\n\n"
                f"🔐 **Enhanced MERGE-BOT v6.0** requires authentication.\n"
                f"Use `/login <password>` to access the bot.\n\n"
                f"**Features:**\n"
                f"• 🎬 Advanced video merging\n"
                f"• 🎵 Audio track integration\n"
                f"• 📄 Subtitle support\n"
                f"• 🔗 GoFile.io sharing\n"
                f"• ☁️ Google Drive upload\n\n"
                f"**Contact:** @{Config.OWNER_USERNAME}",
                quote=True
            )
            return
    else:
        user.allowed = True
        user.set()
    
    welcome_text = (
        f"👋 **Welcome {m.from_user.first_name}!**\n\n"
        f"🤖 **Enhanced MERGE-BOT v6.0**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌟 **NEW FEATURES:**\n"
        f"• 🚀 **Smart Download System** with flood protection\n"
        f"• ⚡ **Robust Merge Engine** with fallback modes\n" 
        f"• 🔗 **GoFile.io Integration** for easy sharing\n"
        f"• 📊 **Enhanced Progress Tracking**\n"
        f"• 🛡️ **Advanced Error Handling**\n\n"
        f"🎯 **MERGE MODES:**\n"
        f"• 📹 **Video Merge** - Combine multiple videos\n"
        f"• 🎵 **Audio Merge** - Add audio tracks to video\n"
        f"• 📄 **Subtitle Merge** - Add subtitles to video\n"
        f"• 🔍 **Stream Extract** - Extract audio/subs\n\n"
        f"📋 **HOW TO USE:**\n"
        f"1. Send videos/links or upload files\n"
        f"2. Configure settings with `/settings`\n" 
        f"3. Use `/merge` to start processing\n"
        f"4. Choose upload destination\n\n"
        f"**Owner:** @{Config.OWNER_USERNAME}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings_main"),
            InlineKeyboardButton("❓ Help", callback_data="help_main")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats_main"),
            InlineKeyboardButton("ℹ️ About", callback_data="about_main")
        ]
    ])
    
    await m.reply_text(welcome_text, quote=True, reply_markup=keyboard)
    del user

@mergeApp.on_message(filters.command(["login"]) & filters.private)
async def login_handler(c: Client, m: Message):
    """Enhanced login with better UX"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if user.banned:
        await m.reply_text(
            "🚫 **Account Banned!**\n"
            f"Unfortunately you can't use this bot.\n\n"
            f"**Reason:** Violation of terms\n"
            f"**Contact:** @{Config.OWNER_USERNAME}",
            quote=True
        )
        return
    
    if user.user_id == int(Config.OWNER):
        user.allowed = True
        await m.reply_text(
            "👑 **Owner Access Granted!**\n"
            "All features unlocked automatically.",
            quote=True
        )
    elif user.allowed:
        await m.reply_text(
            "✅ **Already Authenticated!**\n"
            "You can use all bot features.\n\n"
            "Use `/start` to see the main menu.",
            quote=True
        )
    else:
        try:
            passwd = m.text.split(" ", 1)[1].strip()
            if passwd == Config.PASSWORD:
                user.allowed = True
                await m.reply_text(
                    "✅ **Login Successful!**\n"
                    "🎉 Welcome to Enhanced MERGE-BOT v6.0!\n\n"
                    "🌟 **New Features Available:**\n"
                    "• Smart merge engine with fallback\n"
                    "• Advanced progress tracking\n"
                    "• GoFile.io integration\n"
                    "• Enhanced error handling\n\n"
                    "Use `/start` to explore all features!",
                    quote=True
                )
            else:
                await m.reply_text(
                    "❌ **Invalid Password!**\n"
                    f"Contact @{Config.OWNER_USERNAME} for the correct password.\n\n"
                    "**Note:** Passwords are case-sensitive.",
                    quote=True
                )
        except IndexError:
            await m.reply_text(
                "**📝 Usage:** `/login <password>`\n\n"
                "**Example:** `/login mypassword123`\n\n"
                "Get the password from the bot owner.\n"
                f"**Contact:** @{Config.OWNER_USERNAME}",
                quote=True,
                parse_mode=enums.parse_mode.ParseMode.MARKDOWN
            )
    
    user.set()
    del user

@mergeApp.on_message(filters.command(["help"]) & filters.private)
async def help_handler(c: Client, m: Message):
    """Enhanced help with comprehensive guide"""
    help_text = (
        "📋 **Enhanced MERGE-BOT - Complete Guide**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**🎯 BASIC WORKFLOW:**\n"
        "1️⃣ Send videos, audios, or direct links\n"
        "2️⃣ Configure settings using `/settings`\n"
        "3️⃣ Send custom thumbnail (optional)\n"
        "4️⃣ Use `/merge` to start processing\n"
        "5️⃣ Choose upload method (Telegram/GoFile)\n\n"
        "**📹 MERGE MODES:**\n"
        "• **Video-Video:** Merge up to 10 videos\n"
        "• **Video-Audio:** Add audio tracks\n"
        "• **Video-Subtitle:** Add subtitle files\n"
        "• **Extract:** Get audio/subtitle streams\n\n"
        "**🔧 ADVANCED FEATURES:**\n"
        "• Smart format detection and conversion\n"
        "• Custom thumbnails and metadata\n"
        "• Progress tracking with ETA\n"
        "• Multiple upload destinations\n"
        "• User preferences and settings\n\n"
        "**📤 UPLOAD OPTIONS:**\n"
        "• **Telegram:** Direct upload to chat\n"
        "• **GoFile:** External link sharing\n"
        "• **Google Drive:** Cloud storage (premium)\n\n"
        "**⚠️ FILE LIMITS:**\n"
        "• Free users: 2GB per file\n"
        "• Premium users: 4GB per file\n"
        "• Supported: MP4, MKV, AVI, MOV, etc.\n\n"
        f"**Need help?** Contact @{Config.OWNER_USERNAME}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📹 Video Guide", callback_data="help_video"),
            InlineKeyboardButton("🎵 Audio Guide", callback_data="help_audio")
        ],
        [
            InlineKeyboardButton("📄 Subtitle Guide", callback_data="help_subtitle"),
            InlineKeyboardButton("🔍 Extract Guide", callback_data="help_extract")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data="start_main")
        ]
    ])
    
    await m.reply_text(help_text, quote=True, reply_markup=keyboard)

@mergeApp.on_message(filters.command(["stats"]) & filters.private)
async def stats_handler(c: Client, m: Message):
    """Enhanced stats with detailed system info"""
    if m.from_user.id != int(Config.OWNER):
        await m.reply_text(
            "🔒 **Owner Only Command!**\n"
            "This command is restricted to the bot owner.",
            quote=True
        )
        return
    
    # System statistics
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage(".")
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    
    # Bot statistics
    total_users = len(queueDB) if queueDB else 0
    active_queues = len([q for q in queueDB.values() if q.get('videos')])
    
    stats_text = (
        f"**📊 ENHANCED BOT STATISTICS v6.0**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**⏱️ System Info:**\n"
        f"• **Uptime:** `{currentTime}`\n"
        f"• **CPU Usage:** `{cpuUsage}%`\n"
        f"• **RAM Usage:** `{memory}%`\n"
        f"• **Disk Usage:** `{disk}%` ({used} / {total})\n"
        f"• **Free Space:** `{free}`\n\n"
        f"**🌐 Network:**\n"
        f"• **Uploaded:** `{sent}`\n"
        f"• **Downloaded:** `{recv}`\n\n"
        f"**👥 User Stats:**\n"
        f"• **Total Users:** `{total_users}`\n"
        f"• **Active Queues:** `{active_queues}`\n\n"
        f"**🤖 Bot Features:**\n"
        f"• Enhanced async downloader\n"
        f"• Robust merge engine with fallback\n"
        f"• Smart progress tracking\n"
        f"• GoFile.io integration\n"
        f"• Advanced error handling\n"
        f"• Multi-deployment support\n\n"
        f"**Version:** Enhanced MERGE-BOT v6.0\n"
        f"**Architecture:** Hybrid (UI + Core)"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="stats_refresh"),
            InlineKeyboardButton("📋 Detailed Logs", callback_data="stats_logs")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="start_main")]
    ])
    
    await m.reply_text(stats_text, quote=True, reply_markup=keyboard)

@mergeApp.on_message(filters.command(["merge"]) & filters.private)
async def merge_handler(c: Client, m: Message):
    """Enhanced merge command with improved workflow"""
    user_id = m.from_user.id
    user = UserSettings(user_id, m.from_user.first_name)
    
    # Authentication check
    if user_id != int(Config.OWNER) and not user.allowed:
        await m.reply_text("🔒 **Access Denied!** Use `/login <password>` first.", quote=True)
        return
    
    # Check if user has files in queue
    if user_id not in queueDB or not queueDB[user_id].get("videos"):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Help Guide", callback_data="help_main")]
        ])
        await m.reply_text(
            "📂 **Queue is Empty!**\n\n"
            "**To merge videos:**\n"
            "1. Send video files or direct download links\n"
            "2. Use `/merge` when you have 2+ items\n\n"
            "**Supported formats:** MP4, MKV, AVI, MOV, WEBM, etc.",
            quote=True,
            reply_markup=keyboard
        )
        return
    
    queue_size = len(queueDB[user_id]["videos"])
    if queue_size < 2:
        await m.reply_text(
            f"📹 **Need More Videos!**\n\n"
            f"**Current queue:** {queue_size} item(s)\n"
            f"**Required:** At least 2 items\n\n"
            f"Send more videos or links, then use `/merge` again.",
            quote=True
        )
        return
    
    # Start enhanced merge process
    status_msg = await m.reply_text(
        f"🚀 **Enhanced Merge Process Starting...**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Queue Size:** {queue_size} items\n"
        f"⚙️ **Mode:** {Config.MODES[user.merge_mode - 1].title()}\n"
        f"🎯 **User:** {user.name}\n"
        f"🔄 **Status:** Initializing enhanced workflow...",
        quote=True
    )
    
    try:
        # Initialize enhanced components
        downloader = EnhancedDownloader(user_id)
        merger = EnhancedMerger(user_id)
        
        # Download all files
        video_paths = []
        queue = queueDB[user_id]["videos"]
        
        for i, item in enumerate(queue):
            await status_msg.edit_text(
                f"📥 **Enhanced Download Phase**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔄 **Progress:** {i+1}/{len(queue)}\n"
                f"📁 **Processing:** Item {i+1}\n"
                f"⏳ **Status:** Starting download..."
            )
            
            # Download based on item type
            if isinstance(item, str):  # Direct URL
                file_path = await downloader.download_from_url(item, status_msg)
            else:  # Telegram message ID
                message = await c.get_messages(chat_id=user_id, message_ids=item)
                file_path = await downloader.download_from_telegram(message, status_msg)
            
            if not file_path:
                await status_msg.edit_text(
                    f"❌ **Download Failed!**\n"
                    f"Failed to download item {i+1}/{len(queue)}\n\n"
                    f"**Action:** Cancelling merge operation\n"
                    f"**Suggestion:** Check your files and try again"
                )
                await downloader.cleanup()
                return
            
            video_paths.append(file_path)
        
        # Enhanced merge phase
        merged_path = await merger.merge_videos(video_paths, status_msg)
        
        if not merged_path:
            await downloader.cleanup()
            return
        
        # Success - show upload options
        file_size = get_readable_file_size(os.path.getsize(merged_path))
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Upload to Telegram", callback_data=f"upload_tg_{user_id}")],
            [InlineKeyboardButton("🔗 Upload to GoFile", callback_data=f"upload_gofile_{user_id}")],
            [InlineKeyboardButton("☁️ Upload to Drive", callback_data=f"upload_drive_{user_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_merge_{user_id}")]
        ])
        
        await status_msg.edit_text(
            f"✅ **Merge Completed Successfully!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 **File:** `{os.path.basename(merged_path)}`\n"
            f"📊 **Size:** `{file_size}`\n"
            f"⚡ **Engine:** Enhanced hybrid merger\n"
            f"🎯 **Quality:** Original preserved\n\n"
            f"**🚀 Choose upload destination:**",
            reply_markup=keyboard
        )
        
        # Store merge result for upload
        if user_id not in queueDB:
            queueDB[user_id] = {}
        queueDB[user_id]["merged_file"] = merged_path
        
    except Exception as e:
        LOGGER.error(f"Enhanced merge process error: {e}")
        await status_msg.edit_text(
            f"❌ **Merge Process Failed!**\n\n"
            f"**Error:** `{str(e)}`\n"
            f"**Action:** Process terminated\n\n"
            f"Please try again or contact support if the issue persists."
        )

# ===== FILE AND MESSAGE HANDLERS =====

@mergeApp.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def enhanced_file_handler(c: Client, m: Message):
    """Enhanced file handler with smart processing"""
    user_id = m.from_user.id
    user = UserSettings(user_id, m.from_user.first_name)
    
    # Authentication check
    if user_id != int(Config.OWNER) and not user.allowed:
        await m.reply_text(
            "🔒 **Authentication Required!**\n\n"
            "Use `/login <password>` to access the bot.\n"
            f"Contact @{Config.OWNER_USERNAME} for the password.",
            quote=True
        )
        return
    
    # Initialize user data
    if user_id not in queueDB:
        queueDB[user_id] = {"videos": [], "subtitles": [], "audios": []}
    
    # Process file
    media = m.video or m.document or m.audio
    if not media or not media.file_name:
        await m.reply_text("❌ **Invalid File!** No filename detected.", quote=True)
        return
    
    filename = media.file_name
    file_ext = filename.split('.')[-1].lower()
    file_size = get_readable_file_size(media.file_size)
    
    # Enhanced file type detection
    if file_ext in VIDEO_EXTENSIONS:
        queueDB[user_id]["videos"].append(m.id)
        file_type = "📹 Video"
        queue_type = "videos"
        icon = "🎬"
    elif file_ext in AUDIO_EXTENSIONS:
        queueDB[user_id]["audios"].append(m.id)
        file_type = "🎵 Audio"
        queue_type = "audios"
        icon = "🎶"
    elif file_ext in SUBTITLE_EXTENSIONS:
        queueDB[user_id]["subtitles"].append(m.id)
        file_type = "📄 Subtitle"
        queue_type = "subtitles"
        icon = "📝"
    else:
        await m.reply_text(
            f"⚠️ **Unsupported File Format!**\n\n"
            f"**File:** `{filename}`\n"
            f"**Extension:** `{file_ext}`\n\n"
            f"**Supported Video:** {', '.join(VIDEO_EXTENSIONS[:5])}...\n"
            f"**Supported Audio:** {', '.join(AUDIO_EXTENSIONS[:5])}...\n"
            f"**Supported Subs:** {', '.join(SUBTITLE_EXTENSIONS[:3])}...",
            quote=True
        )
        return
    
    queue_count = len(queueDB[user_id][queue_type])
    total_items = sum(len(queueDB[user_id][t]) for t in ["videos", "audios", "subtitles"])
    
    # Dynamic keyboard based on queue status
    keyboard_buttons = []
    if queue_count >= 2 and queue_type == "videos":
        keyboard_buttons.append([InlineKeyboardButton("🚀 Merge Now", callback_data="merge_now")])
    
    keyboard_buttons.extend([
        [
            InlineKeyboardButton("📊 View Queue", callback_data=f"queue_{user_id}"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings_main")
        ],
        [
            InlineKeyboardButton("🗑️ Clear Queue", callback_data=f"clear_queue_{user_id}"),
            InlineKeyboardButton("❓ Help", callback_data="help_main")
        ]
    ])
    
    keyboard = InlineKeyboardMarkup(keyboard_buttons) if keyboard_buttons else None
    
    # Enhanced success message
    merge_ready = queue_count >= 2 and queue_type == "videos"
    status_emoji = "🚀" if merge_ready else "➕"
    status_text = "Ready to merge!" if merge_ready else "Add more files to merge"
    
    await m.reply_text(
        f"✅ **{file_type} Added Successfully!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 **File:** `{filename}`\n"
        f"📊 **Size:** `{file_size}`\n"
        f"🏷️ **Format:** `{file_ext.upper()}`\n"
        f"{icon} **Queue:** {queue_count} {queue_type}\n"
        f"📋 **Total Items:** {total_items}\n\n"
        f"{status_emoji} **Status:** {status_text}",
        quote=True,
        reply_markup=keyboard
    )

@mergeApp.on_message(filters.text & ~filters.command(["start", "help", "login", "merge", "settings", "cancel"]) & filters.private)
async def url_handler(c: Client, m: Message):
    """Handle direct download URLs"""
    user_id = m.from_user.id
    user = UserSettings(user_id, m.from_user.first_name)
    
    if user_id != int(Config.OWNER) and not user.allowed:
        return
    
    url = m.text.strip()
    
    # Simple URL validation
    if not (url.startswith('http://') or url.startswith('https://')):
        return
    
    if user_id not in queueDB:
        queueDB[user_id] = {"videos": [], "subtitles": [], "audios": []}
    
    # Add URL to queue (store as string to differentiate from message IDs)
    queueDB[user_id]["videos"].append(url)
    queue_count = len(queueDB[user_id]["videos"])
    
    keyboard = None
    if queue_count >= 2:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Merge Now", callback_data="merge_now")]
        ])
    
    await m.reply_text(
        f"✅ **URL Added to Queue!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 **URL:** `{url[:50]}{'...' if len(url) > 50 else ''}`\n"
        f"🔢 **Queue:** {queue_count} item(s)\n\n"
        f"{'🚀 Ready to merge!' if queue_count >= 2 else '➕ Add more items to merge'}",
        quote=True,
        reply_markup=keyboard
    )

if __name__ == "__main__":
    print("🚀 Starting Enhanced MERGE-BOT v6.0...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ Rich UI from yashoswalyo/MERGE-BOT")
    print("✅ Modern core from SunilSharmaNP/Sunil-CM")
    print("✅ Enhanced features and performance")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    try:
        # Initialize premium features
        if hasattr(Config, 'USER_SESSION_STRING') and Config.USER_SESSION_STRING:
            LOGGER.info("Premium features available")
            Config.IS_PREMIUM = True
        else:
            LOGGER.info("Running in free mode")
            Config.IS_PREMIUM = False
        
        # Start the enhanced bot
        LOGGER.info("Starting Enhanced MERGE-BOT...")
        mergeApp.run()
        
    except KeyboardInterrupt:
        LOGGER.info("Bot stopped by user")
        print("👋 Enhanced MERGE-BOT stopped by user")
    except Exception as e:
        LOGGER.error(f"Fatal error during startup: {e}")
        print(f"❌ Fatal error: {e}")
    finally:
        print("🔄 Cleaning up...")
        # Cleanup temporary files
        for temp_dir in ["temp", "downloads"]:
            if os.path.exists(temp_dir):
                try:
                    for item in os.listdir(temp_dir):
                        item_path = os.path.join(temp_dir, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                except:
                    pass
        print("✅ Enhanced MERGE-BOT shutdown complete")
