# Enhanced MERGE-BOT - Package Initialization
# Combines constants and utilities from both repositories with enhancements

import os
import sys
import logging
from collections import defaultdict
from logging.handlers import RotatingFileHandler

# ===== VERSION INFORMATION =====
__version__ = "6.0.0"
__title__ = "Enhanced MERGE-BOT"
__description__ = "Advanced Telegram video merger combining rich UI with modern core"
__author__ = "Enhanced by combining yashoswalyo/MERGE-BOT + SunilSharmaNP/Sunil-CM"

# ===== GLOBAL CONSTANTS (Enhanced from old repo) =====

# User session management
MERGE_MODE = {}        # Maintain each user's merge mode
UPLOAD_AS_DOC = {}     # Maintain each user's upload type preference  
UPLOAD_TO_DRIVE = {}   # Maintain each user's drive upload choice
queueDB = {}           # User file queues
formatDB = {}          # User format preferences
replyDB = {}           # User reply message tracking
gDict = defaultdict(lambda: [])  # Global dictionary for misc data

# ===== ENHANCED FILE TYPE SUPPORT =====
# Expanded file type support from both repositories

VIDEO_EXTENSIONS = [
    "mkv", "mp4", "webm", "ts", "avi", "mov", "m4v", "3gp", "flv", "wmv",
    "mpg", "mpeg", "ogv", "asf", "rm", "rmvb", "vob", "mts", "m2ts"
]

AUDIO_EXTENSIONS = [
    "aac", "ac3", "eac3", "m4a", "mka", "mp3", "wav", "flac", "ogg", 
    "wma", "opus", "dts", "amr", "ra", "au"
]

SUBTITLE_EXTENSIONS = [
    "srt", "ass", "ssa", "vtt", "sub", "idx", "mka", "mks", "sbv",
    "ttml", "dfxp", "smi", "rt", "scc"
]

# ===== PROGRESS BAR CONFIGURATION =====
# Enhanced progress display settings
FINISHED_PROGRESS_STR = os.environ.get("FINISHED_PROGRESS_STR", "█")
UN_FINISHED_PROGRESS_STR = os.environ.get("UN_FINISHED_PROGRESS_STR", "░")
EDIT_SLEEP_TIME_OUT = 10

# ===== ENHANCED LOGGING SYSTEM =====
# Improved logging with rotation and better formatting

def setup_logging():
    """Setup enhanced logging system with rotation and proper formatting"""
    
    # Ensure logs directory exists
    if not os.path.exists("logs"):
        os.makedirs("logs", exist_ok=True)
    
    # Clear existing log file at startup
    log_file = "logs/mergebotlog.txt"
    try:
        with open(log_file, "w") as w:
            w.truncate(0)
    except:
        pass
    
    # Configure logging with enhanced format
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(filename)s:%(lineno)d] - %(message)s"
    )
    
    date_format = "%d-%b-%y %H:%M:%S"
    
    # Setup handlers
    handlers = [
        # File handler with rotation
        RotatingFileHandler(
            log_file, 
            maxBytes=50000000,  # 50MB
            backupCount=10,
            encoding='utf-8'
        ),
        # Console handler for real-time monitoring
        logging.StreamHandler(sys.stdout)
    ]
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True  # Override existing configuration
    )
    
    # Set levels for external libraries
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("ffmpeg").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Initialize logging
LOGGER = setup_logging()

# ===== MESSAGE TEMPLATES =====
# Enhanced message templates

BROADCAST_MSG = """
**📢 BROADCAST MESSAGE**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Total Recipients:** {}
**Successfully Sent:** {}
**Status:** Processing...
"""

WELCOME_MSG_TEMPLATE = """
🤖 **Enhanced MERGE-BOT v{version}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👋 **Welcome {user_name}!**

🌟 **New Enhanced Features:**
• 🚀 Smart download system with flood protection
• ⚡ Robust merge engine with fallback modes  
• 🔗 GoFile.io integration for easy sharing
• 📊 Advanced progress tracking
• 🛡️ Enhanced error handling

🎯 **Available Modes:**
• 📹 Video Merge - Combine multiple videos
• 🎵 Audio Merge - Add audio tracks to video
• 📄 Subtitle Merge - Add subtitles to video  
• 🔍 Stream Extract - Extract audio/subs

📋 **Quick Start:**
1. Send videos/links or upload files
2. Configure settings with `/settings`
3. Use `/merge` to start processing
4. Choose upload destination

**Owner:** @{owner_username}
**Support:** @{owner_username}
"""

# ===== ENHANCED BUTTON MAKER =====
# Simple button maker class for compatibility
class MakeButtons:
    """Simple button maker for inline keyboards"""
    
    def build_keyboard(self, buttons):
        """Build inline keyboard from button list"""
        from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        for row in buttons:
            if isinstance(row, list):
                keyboard.append([InlineKeyboardButton(btn[0], callback_data=btn[1]) for btn in row])
            else:
                keyboard.append([InlineKeyboardButton(row, callback_data=row[1])])
        return InlineKeyboardMarkup(keyboard)

# Initialize button maker
bMaker = MakeButtons()

# ===== PERFORMANCE MONITORING =====

class PerformanceMonitor:
    """Monitor bot performance and resource usage"""
    
    def __init__(self):
        self.start_time = None
        self.operations = defaultdict(int)
        self.errors = defaultdict(int)
    
    def start_operation(self, operation_name):
        """Start monitoring an operation"""
        import time
        self.start_time = time.time()
        self.operations[operation_name] += 1
        LOGGER.debug(f"Started operation: {operation_name}")
    
    def end_operation(self, operation_name, success=True):
        """End monitoring an operation"""
        import time
        if self.start_time:
            duration = time.time() - self.start_time
            status = "success" if success else "failed"
            LOGGER.info(f"Operation {operation_name} {status} in {duration:.2f}s")
            
            if not success:
                self.errors[operation_name] += 1
    
    def get_stats(self):
        """Get performance statistics"""
        return {
            'operations': dict(self.operations),
            'errors': dict(self.errors)
        }

# Initialize performance monitor
performance_monitor = PerformanceMonitor()

# ===== CACHE SYSTEM =====

class SimpleCache:
    """Simple in-memory cache with expiration"""
    
    def __init__(self, default_ttl=3600):
        self.cache = {}
        self.default_ttl = default_ttl
    
    def set(self, key, value, ttl=None):
        """Set a cached value"""
        import time
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = {'value': value, 'expiry': expiry}
    
    def get(self, key, default=None):
        """Get a cached value"""
        import time
        if key not in self.cache:
            return default
        
        entry = self.cache[key]
        if time.time() > entry['expiry']:
            del self.cache[key]
            return default
        
        return entry['value']
    
    def clear_expired(self):
        """Clear expired cache entries"""
        import time
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items() 
            if current_time > entry['expiry']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            LOGGER.debug(f"Cleared {len(expired_keys)} expired cache entries")

# Initialize cache
cache = SimpleCache()

# ===== STARTUP BANNER =====

def print_startup_banner():
    """Print enhanced startup banner"""
    banner = f"""
╔═══════════════════════════════════════════════════════════════╗
║                    ENHANCED MERGE-BOT v{__version__}                    ║
║               Advanced Telegram Video Merger                 ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  🎯 Features:                                                ║
║   • Rich Interactive UI (from yashoswalyo/MERGE-BOT)        ║
║   • Modern Async Core (from SunilSharmaNP/Sunil-CM)        ║
║   • Smart Download System with Flood Protection             ║
║   • Robust Merge Engine with Fallback Modes                ║
║   • GoFile.io Integration for Easy Sharing                  ║
║   • Enhanced Progress Tracking & Error Handling             ║
║                                                               ║
║  📊 Support:                                                 ║
║   • Up to 10 videos per merge                               ║
║   • 4GB file size limit (premium)                           ║
║   • Multiple audio/subtitle tracks                          ║
║   • Stream extraction capabilities                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)

# ===== CLEANUP FUNCTIONS =====

def cleanup_temp_files():
    """Clean up temporary files and directories"""
    temp_dirs = ["temp", "cache"]
    cleaned_files = 0
    
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            try:
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            __import__('shutil').rmtree(item_path)
                        else:
                            os.remove(item_path)
                        cleaned_files += 1
                    except:
                        pass
            except:
                pass
    
    if cleaned_files > 0:
        LOGGER.info(f"Cleaned up {cleaned_files} temporary files")

def cleanup_user_data(user_id):
    """Clean up all data for a specific user"""
    # Remove from global dictionaries
    for db in [queueDB, formatDB, replyDB, MERGE_MODE, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE]:
        db.pop(user_id, None)
    
    # Remove user download directory
    user_dir = f"downloads/{user_id}"
    if os.path.exists(user_dir):
        try:
            __import__('shutil').rmtree(user_dir)
            LOGGER.info(f"Cleaned up user directory: {user_dir}")
        except Exception as e:
            LOGGER.error(f"Failed to cleanup user directory {user_dir}: {e}")

# ===== INITIALIZATION =====

def initialize_enhanced_bot():
    """Initialize enhanced bot components"""
    try:
        print_startup_banner()
        
        # Setup logging
        LOGGER.info("Enhanced MERGE-BOT initialization started")
        
        # Create necessary directories
        for directory in ["downloads", "logs", "temp", "cache", "backups"]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        # Initialize performance monitoring
        performance_monitor.start_operation("bot_startup")
        
        # Clean up any existing temporary files
        cleanup_temp_files()
        
        LOGGER.info(f"Enhanced MERGE-BOT v{__version__} initialized successfully")
        return True
        
    except Exception as e:
        LOGGER.error(f"Failed to initialize Enhanced MERGE-BOT: {e}")
        return False

# ===== MODULE EXPORTS =====

# Export all important components
__all__ = [
    # Version info
    '__version__', '__title__', '__description__', '__author__',
    
    # Core components
    'LOGGER', 'bMaker', 'cache', 'performance_monitor',
    
    # Global dictionaries
    'queueDB', 'formatDB', 'replyDB', 'gDict',
    'MERGE_MODE', 'UPLOAD_AS_DOC', 'UPLOAD_TO_DRIVE',
    
    # Constants
    'VIDEO_EXTENSIONS', 'AUDIO_EXTENSIONS', 'SUBTITLE_EXTENSIONS',
    'FINISHED_PROGRESS_STR', 'UN_FINISHED_PROGRESS_STR',
    
    # Message templates
    'BROADCAST_MSG', 'WELCOME_MSG_TEMPLATE',
    
    # Utility classes
    'PerformanceMonitor', 'SimpleCache', 'MakeButtons',
    
    # Functions
    'cleanup_temp_files', 'cleanup_user_data', 'initialize_enhanced_bot',
    'print_startup_banner', 'setup_logging'
]

# Auto-initialize when imported
if __name__ != "__main__":
    initialize_enhanced_bot()
