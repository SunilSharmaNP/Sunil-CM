# config.py
import os

# ====== Telegram API Config ======
API_ID = int(os.environ.get("API_ID", 123456))  # Telegram API ID (get from https://my.telegram.org)
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")  # Telegram API Hash
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")  # Bot token from @BotFather

# Optional: For user-specific actions if you use Pyrogram session-based clients
SESSION_STRING = os.environ.get("SESSION_STRING", None)

# ====== GoFile API Token ======
# You can create a free account at https://gofile.io and get your token from settings
GOFILE_TOKEN = os.environ.get("GOFILE_TOKEN", "YOUR_GOFILE_API_TOKEN")

# ====== Bot Settings ======
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads")   # Where to temporarily store files
MERGED_FILE_NAME = os.environ.get("MERGED_FILE_NAME", "merged_video.mp4")

# Create download folder if it doesn't exist
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ====== Default Bot Messages (English) ======
START_MSG = (
    "👋 Hello! I can merge multiple videos (from direct links or Telegram uploads) "
    "into a single file with both video and audio.

"
    "📌 **How to use:**
"
    "1. Send me at least two direct links or video files.
"
    "2. When ready, send `/merge` to combine them.
"
    "3. I’ll upload the merged file to GoFile.io and give you the link."
)

HELP_MSG = (
    "📖 **Bot Commands:**

"
    "`/start` - Show welcome message
"
    "`/help` - Show this help message
"
    "`/merge link1 link2 ...` - Merge videos from given URLs
"
    "Or: Send video files directly and then `/merge`

"
    "⚠️ Make sure your videos have the same resolution/codec for fastest merging."
)
