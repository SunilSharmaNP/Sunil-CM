# Enhanced Configuration Module
# Combines configuration approaches from both repositories with additional features

import os
from dotenv import load_dotenv

# Load environment variables from config.env file
load_dotenv('config.env', override=True)

class Config(object):
    """
    Enhanced Configuration class combining both repo approaches
    Includes all features from yashoswalyo/MERGE-BOT plus new additions from SunilSharmaNP/Sunil-CM
    """
    
    # ===== TELEGRAM API CREDENTIALS =====
    # Required for bot operation - supports both naming conventions
    API_ID = os.environ.get("API_ID") or os.environ.get("TELEGRAM_API")
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    # Legacy compatibility
    TELEGRAM_API = API_ID  
    
    # ===== USER MANAGEMENT =====
    # Bot owner and access control
    OWNER = os.environ.get("OWNER")
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME")
    PASSWORD = os.environ.get("PASSWORD")
    
    # ===== DATABASE CONFIGURATION =====
    # MongoDB for user data and settings (from old repo)
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    # ===== LOGGING AND CHANNELS =====
    # Log channel for storing merged videos (format: "-100" + channel_id)
    LOGCHANNEL = os.environ.get("LOGCHANNEL")
    
    # ===== PREMIUM FEATURES =====
    # Premium account session for 4GB uploads (from old repo)
    USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", None)
    
    # Google Drive integration via rclone (from old repo)
    GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "root")
    
    # ===== NEW FEATURES (from SunilSharmaNP repo) =====
    # GoFile.io integration for external file sharing
    GOFILE_TOKEN = os.environ.get("GOFILE_TOKEN")
    
    # Download directory configuration
    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads")
    
    # ===== RUNTIME FLAGS =====
    # Set dynamically during bot startup
    IS_PREMIUM = False  # Determined by USER_SESSION_STRING availability
    
    # ===== MERGE MODES =====
    # Available merge modes (enhanced from old repo)
    MODES = [
        "video-video",      # Merge multiple videos into single file
        "video-audio",      # Add multiple audio tracks to video
        "video-subtitle",   # Add subtitle files to video
        "extract-streams"   # Extract audio/subtitle streams separately
    ]
    
    # ===== FILE TYPE SUPPORT =====
    # Enhanced file extension support
    VIDEO_EXTENSIONS = [
        "mkv", "mp4", "webm", "ts", "avi", "mov", "m4v", 
        "3gp", "flv", "wmv", "mpg", "mpeg", "ogv"
    ]
    
    AUDIO_EXTENSIONS = [
        "aac", "ac3", "eac3", "m4a", "mka", "mp3", "wav", 
        "flac", "ogg", "wma", "opus", "dts"
    ]
    
    SUBTITLE_EXTENSIONS = [
        "srt", "ass", "ssa", "vtt", "sub", "idx", "mka", "mks", "sbv"
    ]
    
    # ===== UPLOAD LIMITS =====
    # File size limits in bytes
    MAX_FILE_SIZE_FREE = 2 * 1024 * 1024 * 1024      # 2GB for free users
    MAX_FILE_SIZE_PREMIUM = 4 * 1024 * 1024 * 1024    # 4GB for premium users
    MAX_QUEUE_SIZE = 10  # Maximum files in queue
    
    # ===== PERFORMANCE SETTINGS =====
    # Enhanced performance configuration
    EDIT_THROTTLE_SECONDS = 4.0         # Prevent FloodWait errors
    DOWNLOAD_CHUNK_SIZE = 1024 * 1024   # 1MB download chunks
    MAX_CONCURRENT_DOWNLOADS = 3        # Concurrent download limit
    UPLOAD_TIMEOUT = 300                # Upload timeout in seconds
    DOWNLOAD_TIMEOUT = 300              # Download timeout in seconds
    
    # ===== FFMPEG CONFIGURATION =====
    # Enhanced FFmpeg settings
    FFMPEG_PRESET = os.environ.get("FFMPEG_PRESET", "fast")    # fast, medium, slow, veryfast
    VIDEO_CRF = int(os.environ.get("VIDEO_CRF", "23"))         # Constant Rate Factor (18-28)
    AUDIO_BITRATE = os.environ.get("AUDIO_BITRATE", "192k")    # Audio bitrate
    VIDEO_CODEC = os.environ.get("VIDEO_CODEC", "libx264")     # Video codec
    AUDIO_CODEC = os.environ.get("AUDIO_CODEC", "aac")         # Audio codec
    
    # ===== UI AND PROGRESS SETTINGS =====
    # Progress bar and UI configuration
    PROGRESS_BAR_LENGTH = int(os.environ.get("PROGRESS_BAR_LENGTH", "20"))
    FINISHED_PROGRESS_STR = os.environ.get("FINISHED_PROGRESS_STR", "█")
    UN_FINISHED_PROGRESS_STR = os.environ.get("UN_FINISHED_PROGRESS_STR", "░")
    
    # ===== ADVANCED FEATURES =====
    # Feature flags for enhanced capabilities
    ENABLE_COMPRESSION = os.environ.get("ENABLE_COMPRESSION", "true").lower() == "true"
    AUTO_DELETE_FILES = os.environ.get("AUTO_DELETE_FILES", "true").lower() == "true"
    ENABLE_STATS_LOGGING = os.environ.get("ENABLE_STATS_LOGGING", "true").lower() == "true"
    ENABLE_WEBHOOK = os.environ.get("ENABLE_WEBHOOK", "false").lower() == "true"
    DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
    
    # ===== WEBHOOK CONFIGURATION =====
    # For webhook-based deployments (optional)
    WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST")
    WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "8080"))
    WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE")
    WEBHOOK_URL_PATH = os.environ.get("WEBHOOK_URL_PATH", "/webhook")

# ===== VALIDATION FUNCTIONS =====

def validate_config():
    """Validate required configuration variables with enhanced error reporting"""
    required_vars = [
        ("API_ID or TELEGRAM_API", Config.API_ID),
        ("API_HASH", Config.API_HASH),
        ("BOT_TOKEN", Config.BOT_TOKEN),
        ("OWNER", Config.OWNER),
        ("PASSWORD", Config.PASSWORD)
    ]
    
    missing_vars = []
    invalid_vars = []
    
    # Check for missing variables
    for var_name, var_value in required_vars:
        if not var_value:
            missing_vars.append(var_name)
    
    # Validate numeric values
    numeric_checks = [
        ("OWNER", Config.OWNER),
        ("API_ID", Config.API_ID),
    ]
    
    for var_name, var_value in numeric_checks:
        if var_value:
            try:
                int(var_value)
            except ValueError:
                invalid_vars.append(f"{var_name} (must be numeric)")
    
    # Generate error messages
    if missing_vars or invalid_vars:
        error_lines = ["❌ Configuration Validation Failed!"]
        error_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if missing_vars:
            error_lines.append(f"📋 Missing Required Variables: {', '.join(missing_vars)}")
        
        if invalid_vars:
            error_lines.append(f"⚠️ Invalid Values: {', '.join(invalid_vars)}")
        
        error_lines.extend([
            "",
            "📝 Required Configuration:",
            "   • API_ID or TELEGRAM_API (numeric)",
            "   • API_HASH (string)",
            "   • BOT_TOKEN (bot token from @BotFather)",
            "   • OWNER (numeric user ID)",
            "   • PASSWORD (string)",
            "",
            "🔗 Get API credentials: https://my.telegram.org",
            "🤖 Get bot token: @BotFather",
            "",
            "💡 Optional Features:",
            "   • DATABASE_URL (MongoDB for user management)",
            "   • GOFILE_TOKEN (GoFile.io integration)",
            "   • USER_SESSION_STRING (premium features)",
            "   • LOGCHANNEL (log channel ID)",
        ])
        
        print("\n".join(error_lines))
        raise ValueError("Configuration validation failed")
    
    print("✅ Configuration validation passed!")
    return True

def setup_directories():
    """Create necessary directories with proper permissions"""
    directories = [
        Config.DOWNLOAD_DIR,
        "logs",
        "temp",
        "cache",
        "backups"
    ]
    
    created_dirs = []
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, mode=0o755, exist_ok=True)
                created_dirs.append(directory)
            except PermissionError:
                print(f"⚠️ Permission denied creating directory: {directory}")
            except Exception as e:
                print(f"⚠️ Error creating directory {directory}: {e}")
    
    if created_dirs:
        print(f"📁 Created directories: {', '.join(created_dirs)}")
    
    return True

def print_config_summary():
    """Print a summary of the current configuration"""
    print("🔧 Enhanced MERGE-BOT Configuration Summary")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🤖 Bot Token: {'✅ Configured' if Config.BOT_TOKEN else '❌ Missing'}")
    print(f"🔑 API Credentials: {'✅ Valid' if Config.API_ID and Config.API_HASH else '❌ Invalid'}")
    print(f"👤 Owner: {'✅ Set' if Config.OWNER else '❌ Missing'}")
    print(f"🔒 Password: {'✅ Set' if Config.PASSWORD else '❌ Missing'}")
    print(f"🗄️ Database: {'✅ MongoDB' if Config.DATABASE_URL else '⚠️ In-memory only'}")
    print(f"📁 Downloads: {Config.DOWNLOAD_DIR}")
    print(f"🔗 GoFile: {'✅ Enabled' if Config.GOFILE_TOKEN else '⚠️ Disabled'}")
    print(f"💎 Premium: {'✅ Available' if Config.USER_SESSION_STRING else '⚠️ Not configured'}")
    print(f"📺 Log Channel: {'✅ Set' if Config.LOGCHANNEL else '⚠️ Not set'}")
    print(f"🚀 Performance: Enhanced async + smart throttling")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# ===== LEGACY COMPATIBILITY =====
# Maintain compatibility with old repository imports

# Direct variable exports for old code compatibility
TELEGRAM_API = Config.API_ID
API_HASH = Config.API_HASH
BOT_TOKEN = Config.BOT_TOKEN
OWNER = Config.OWNER
OWNER_USERNAME = Config.OWNER_USERNAME
PASSWORD = Config.PASSWORD
DATABASE_URL = Config.DATABASE_URL
LOGCHANNEL = Config.LOGCHANNEL
USER_SESSION_STRING = Config.USER_SESSION_STRING
GDRIVE_FOLDER_ID = Config.GDRIVE_FOLDER_ID

# New variables for enhanced features
GOFILE_TOKEN = Config.GOFILE_TOKEN
DOWNLOAD_DIR = Config.DOWNLOAD_DIR

# ===== INITIALIZATION =====
if __name__ != "__main__":
    # Auto-validate and setup when module is imported
    try:
        validate_config()
        setup_directories()
        print_config_summary()
    except Exception as e:
        print(f"❌ Configuration initialization failed: {e}")
        raise

# Create a singleton config instance
config = Config()

# ===== EXPORTS =====
__all__ = [
    'Config', 'config',
    'validate_config', 'setup_directories', 'print_config_summary',
    # Legacy exports for backward compatibility
    'TELEGRAM_API', 'API_HASH', 'BOT_TOKEN', 'OWNER', 'OWNER_USERNAME',
    'PASSWORD', 'DATABASE_URL', 'LOGCHANNEL', 'USER_SESSION_STRING',
    'GDRIVE_FOLDER_ID', 'GOFILE_TOKEN', 'DOWNLOAD_DIR'
]
