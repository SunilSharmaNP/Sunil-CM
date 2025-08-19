# Enhanced Message Templates
# Consistent messaging for Enhanced MERGE-BOT

from typing import Dict, Any, Optional
from config import Config

# ===== WELCOME MESSAGES =====

WELCOME_MESSAGE = """👋 **Welcome {user_name}!**

🤖 **Enhanced MERGE-BOT v6.0**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 **What's New:**
• 🚀 **Smart Download System** with flood protection
• ⚡ **Robust Merge Engine** with fallback modes  
• 🔗 **GoFile.io Integration** for easy sharing
• 📊 **Enhanced Progress Tracking** with ETA
• 🛡️ **Advanced Error Handling** and recovery

🎯 **Available Modes:**
• 📹 **Video Merge** - Combine multiple videos
• 🎵 **Audio Merge** - Add audio tracks to video
• 📄 **Subtitle Merge** - Add subtitles to video
• 🔍 **Stream Extract** - Extract audio/subtitle streams

📋 **Quick Start:**
1. Send videos/links or upload files
2. Configure settings with buttons below
3. Use **Merge Now** to start processing
4. Choose your preferred upload destination

**Owner:** @{owner_username}"""

HELP_MESSAGE = """📋 **Enhanced MERGE-BOT - Complete Guide**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🎯 Basic Workflow:**
1️⃣ Send videos, audios, or direct download links
2️⃣ Configure your preferences in Settings
3️⃣ Send custom thumbnail (optional)
4️⃣ Use **Merge Now** to start processing
5️⃣ Choose upload method (Telegram/GoFile/Drive)

**📹 Merge Modes:**
• **Video-Video:** Merge up to 10 videos into one
• **Video-Audio:** Add multiple audio tracks
• **Video-Subtitle:** Add subtitle files with language support
• **Extract Streams:** Get separate audio/subtitle files

**🔧 Advanced Features:**
• Smart format detection and automatic conversion
• Custom thumbnails with auto-generation fallback
• Real-time progress tracking with speed and ETA
• Multiple upload destinations for convenience
• User preferences saved automatically

**📤 Upload Options:**
• **Telegram:** Direct upload to chat (2GB/4GB limit)
• **GoFile:** External link sharing (unlimited size)
• **Google Drive:** Cloud storage (premium feature)

**⚠️ File Limits:**
• Free users: 2GB per file
• Premium users: 4GB per file  
• Supported formats: MP4, MKV, AVI, MOV, WEBM, etc.

**📱 Pro Tips:**
• Send files in the order you want them merged
• Use custom thumbnails for better presentation
• Enable compression for smaller file sizes
• Check queue status before merging

Need specific help? Use the buttons below! 👇"""

# ===== STATUS MESSAGES =====

DOWNLOAD_STARTING = """📥 **Starting Enhanced Download...**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 **Status:** Initializing smart download system
⚙️ **Features:** Flood protection, retry logic, progress tracking
📊 **Queue Position:** {position} of {total}"""

DOWNLOAD_PROGRESS = """📥 **Downloading {file_type}...**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
➢ `{filename}`
➢ {progress_bar} `{progress:.1%}`
➢ **Size:** `{current_size}` / `{total_size}`
➢ **Speed:** `{speed}/s`
➢ **ETA:** `{eta}`
➢ **Source:** {source_type}"""

MERGE_STARTING = """🔧 **Enhanced Merge Process Initiated**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **Files:** {file_count} items in queue
⚙️ **Mode:** {merge_mode}  
🎯 **Quality:** Original preservation enabled
🚀 **Engine:** Hybrid merger (Fast + Robust fallback)
⏳ **Estimated Time:** {estimated_time}"""

MERGE_PROGRESS = """🔧 **{merge_type} Merge in Progress...**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 **Mode:** {mode_detail}
⏱️ **Elapsed:** `{elapsed_time}`
📊 **Current Size:** `{current_size}`
🎯 **Quality Setting:** {quality_info}
💾 **Output:** `{output_filename}`"""

MERGE_SUCCESS = """✅ **Merge Completed Successfully!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 **Output File:** `{filename}`
📊 **Final Size:** `{file_size}`
⏱️ **Total Time:** `{total_time}`
⚡ **Merge Type:** {merge_type}
🎯 **Quality:** {quality_preserved}

🚀 **Ready for Upload!**
Choose your preferred destination below:"""

UPLOAD_PROGRESS = """📤 **Uploading to {destination}...**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
➢ `{filename}`
➢ {progress_bar} `{progress:.1%}`
➢ **Size:** `{current_size}` / `{total_size}`
➢ **Speed:** `{speed}/s`
➢ **ETA:** `{eta}`
➢ **Destination:** {upload_type}"""

UPLOAD_SUCCESS = """✅ **Upload Completed Successfully!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 **File:** `{filename}`
📊 **Size:** `{file_size}`
⏱️ **Upload Time:** `{upload_time}`
🌐 **Destination:** {destination}
{link_info}

Thank you for using Enhanced MERGE-BOT! 🎉"""

# ===== SETTINGS MESSAGES =====

SETTINGS_MAIN = """⚙️ **Enhanced MERGE-BOT Settings**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Current Configuration:**
🎬 **Merge Mode:** {merge_mode}
📤 **Upload Mode:** {upload_mode}
🖼️ **Custom Thumbnail:** {thumbnail_status}
🗜️ **Compression:** {compression_status}
🌍 **Language:** {language}
🧹 **Auto Cleanup:** {autoclean_status}

**User Information:**
👤 **Name:** {user_name}
🆔 **ID:** `{user_id}`
📅 **Member Since:** {join_date}
⭐ **Status:** {user_status}

Use the buttons below to customize your experience:"""

MERGE_MODE_SELECTION = """🎬 **Select Merge Mode**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose how you want to process your files:

**📹 Video Merge**
• Combine multiple videos into single file
• Preserves quality with smart encoding
• Supports up to 10 videos per merge

**🎵 Audio Merge**
• Add audio tracks to existing video
• Multiple language support
• Maintains video quality

**📄 Subtitle Merge**
• Add subtitle files to video
• Auto-detects subtitle language
• Soft-mux for compatibility

**🔍 Extract Streams**
• Extract audio/subtitle streams
• Separate files for each stream
• Preserves original quality

Current mode: **{current_mode}**"""

UPLOAD_MODE_SELECTION = """📤 **Upload Destination Settings**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose your preferred upload destination:

**📱 Telegram**
• Direct upload to chat
• Free: 2GB limit | Premium: 4GB limit
• Instant access, no external links

**🔗 GoFile.io**
• External file sharing service
• No file size limits
• Shareable download links

**☁️ Google Drive**
• Cloud storage integration
• Requires premium account
• Permanent storage solution

**📋 As Document**
• Upload files as documents
• Better for non-video files
• Preserves original filename

Current settings: **{current_settings}**"""

# ===== ERROR MESSAGES =====

ERROR_TEMPLATES = {
    "file_too_large": """❌ **File Too Large!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 **File:** `{filename}`
📊 **Size:** `{file_size}`
⚠️ **Limit:** `{size_limit}`

**Solutions:**
• Use premium account for 4GB support
• Enable compression to reduce size  
• Upload to GoFile.io (no size limit)
• Split video into smaller parts""",

    "download_failed": """❌ **Download Failed!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 **Source:** {source}
⚠️ **Error:** `{error_message}`

**Common Issues:**
• Invalid or expired download link
• Network connectivity problems
• Server temporarily unavailable
• File requires authentication

**Try:**
• Check the link in your browser
• Wait a few minutes and retry
• Use a different download source""",

    "merge_failed": """❌ **Merge Process Failed!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ **Error:** `{error_message}`
🔧 **Stage:** {failed_stage}

**Possible Causes:**
• Incompatible video formats
• Corrupted input files
• Insufficient disk space
• System resource limitations

**Solutions:**
• Check all input files are valid
• Free up disk space
• Try with different video files
• Contact support if issue persists""",

    "upload_failed": """❌ **Upload Failed!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 **Destination:** {destination}
⚠️ **Error:** `{error_message}`

**Common Issues:**
• Network connectivity problems
• Service temporarily unavailable
• Authentication/token expired
• File size exceeds limits

**Try:**
• Switch to different upload method
• Check your internet connection
• Wait and retry in a few minutes
• Use GoFile for large files""",

    "access_denied": """🔒 **Access Denied!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ You need to authenticate to use this bot.

**How to Login:**
1. Use `/login <password>` command
2. Get the password from bot owner
3. Once logged in, you can use all features

**Need Access?**
Contact the bot owner: @{owner_username}

**Note:** This helps maintain quality service for all users."""
}

# ===== ADMIN MESSAGES =====

ADMIN_STATS = """📊 **Enhanced Bot Statistics**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**System Information:**
⏱️ **Uptime:** `{uptime}`
🖥️ **CPU Usage:** `{cpu_usage}%`
⚙️ **RAM Usage:** `{memory_usage}%`
💾 **Disk Usage:** `{disk_usage}%` ({disk_used} / {disk_total})
📊 **Free Space:** `{free_space}`

**Network Statistics:**
📤 **Uploaded:** `{bytes_sent}`
📥 **Downloaded:** `{bytes_received}`

**Bot Statistics:**
👥 **Total Users:** `{total_users}`
🔄 **Active Sessions:** `{active_sessions}`
📁 **Files Processed:** `{files_processed}`
⚡ **Average Speed:** `{avg_speed}/s`

**Performance:**
• Enhanced async architecture ✅
• Smart progress tracking ✅  
• Robust error handling ✅
• Multi-destination upload ✅
• GoFile.io integration ✅

**Version:** Enhanced MERGE-BOT v{version}"""

BROADCAST_TEMPLATE = """📢 **Broadcast Message**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**From:** Enhanced MERGE-BOT Admin
**Time:** {timestamp}

{message_content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Enhanced MERGE-BOT v6.0** - @{owner_username}"""

# ===== INFO MESSAGES =====

QUEUE_INFO = """📋 **Current Queue Status**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📹 Videos:** {video_count} files
{video_list}

**🎵 Audio Files:** {audio_count} files  
{audio_list}

**📄 Subtitles:** {subtitle_count} files
{subtitle_list}

**📊 Total Items:** {total_items}
**💾 Total Size:** `{total_size}`
**⏱️ Estimated Merge Time:** `{estimated_time}`

{merge_ready_status}"""

FILE_INFO = """📋 **File Information**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 **Filename:** `{filename}`
📊 **Size:** `{file_size}`
🎬 **Duration:** `{duration}`
📺 **Resolution:** `{resolution}`
🎵 **Audio:** `{audio_info}`
🔧 **Video Codec:** `{video_codec}`
🎼 **Audio Codec:** `{audio_codec}`
📈 **Bitrate:** `{bitrate}`
🏷️ **Format:** `{format}`

**Compatibility:**
• Fast Merge: {fast_compatible}
• Quality: {quality_rating}
• Mobile Friendly: {mobile_friendly}"""

ABOUT_MESSAGE = """ℹ️ **About Enhanced MERGE-BOT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🤖 Enhanced MERGE-BOT v6.0**
The ultimate Telegram video merger combining the best of both worlds!

**🎯 What Makes It Special:**
• Rich interactive UI from yashoswalyo/MERGE-BOT
• Modern async core from SunilSharmaNP/Sunil-CM  
• Enhanced with new features and optimizations

**✨ Key Features:**
• Smart download system with flood protection
• Robust merge engine with fallback modes
• GoFile.io integration for unlimited sharing
• Advanced progress tracking with ETA
• Multi-language subtitle support
• Custom thumbnail generation
• Multiple upload destinations
• Premium account support (4GB files)

**🛡️ Quality Assurance:**
• Preserves original video quality
• Smart format compatibility detection
• Automatic error recovery
• Comprehensive logging system

**👨‍💻 Development:**
• Hybrid architecture (UI + Core)
• Production-ready Docker support
• Multi-platform deployment
• Active maintenance and updates

**📞 Support:**
• Owner: @{owner_username}
• Documentation: Available in Help section
• Community: Professional support

**📊 Statistics:**
• Users served: {user_count}+
• Files processed: {file_count}+
• Uptime: 99.9%+
• Average rating: ⭐⭐⭐⭐⭐

Made with ❤️ by combining the best open source projects!"""

# ===== UTILITY FUNCTIONS =====

def format_message_template(template: str, **kwargs) -> str:
    """Format message template with provided kwargs"""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Template error: Missing key {e}"

def get_error_message(error_type: str, **kwargs) -> str:
    """Get formatted error message"""
    if error_type in ERROR_TEMPLATES:
        return format_message_template(ERROR_TEMPLATES[error_type], **kwargs)
    else:
        return f"❌ **Unknown Error:** {error_type}"

def create_progress_message(
    operation: str,
    filename: str,
    progress: float,
    current_size: str,
    total_size: str,
    speed: str,
    eta: str,
    **kwargs
) -> str:
    """Create standardized progress message"""
    progress_bar = "█" * int(20 * progress) + "░" * (20 - int(20 * progress))
    
    base_template = """⏳ **{operation} in Progress...**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
➢ `{filename}`
➢ {progress_bar} `{progress:.1%}`
➢ **Size:** `{current_size}` / `{total_size}`
➢ **Speed:** `{speed}/s`
➢ **ETA:** `{eta}`"""
    
    return base_template.format(
        operation=operation,
        filename=filename,
        progress_bar=progress_bar,
        progress=progress,
        current_size=current_size,
        total_size=total_size,
        speed=speed,
        eta=eta
    )

# Export all message templates and functions
__all__ = [
    'WELCOME_MESSAGE',
    'HELP_MESSAGE',
    'DOWNLOAD_STARTING',
    'DOWNLOAD_PROGRESS', 
    'MERGE_STARTING',
    'MERGE_PROGRESS',
    'MERGE_SUCCESS',
    'UPLOAD_PROGRESS',
    'UPLOAD_SUCCESS',
    'SETTINGS_MAIN',
    'MERGE_MODE_SELECTION',
    'UPLOAD_MODE_SELECTION',
    'ERROR_TEMPLATES',
    'ADMIN_STATS',
    'BROADCAST_TEMPLATE',
    'QUEUE_INFO',
    'FILE_INFO',
    'ABOUT_MESSAGE',
    'format_message_template',
    'get_error_message',
    'create_progress_message'
]
