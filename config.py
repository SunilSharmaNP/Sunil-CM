# config.py
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv('config.env')

class Config:
    """
    Configuration class for the bot.
    Reads all the necessary environment variables.
    Raises an error if any critical variable is missing.
    """
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    GOFILE_TOKEN = os.environ.get("GOFILE_TOKEN")
    
    # Path for downloads, unique for each user
    DOWNLOAD_DIR = "downloads"

# --- Sanity Checks ---
if not Config.API_ID:
    raise ValueError("API_ID not found. Please add it to your config.env file.")
if not Config.API_HASH:
    raise ValueError("API_HASH not found. Please add it to your config.env file.")
if not Config.BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found. Please add it to your config.env file.")
if not Config.GOFILE_TOKEN:
    raise ValueError("GOFILE_TOKEN not found. Please add it to your config.env file.")

# Ensure the main download directory exists
if not os.path.isdir(Config.DOWNLOAD_DIR):
    os.makedirs(Config.DOWNLOAD_DIR)

# Create a singleton instance
config = Config()
