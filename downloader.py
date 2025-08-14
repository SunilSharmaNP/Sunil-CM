# downloader.py (Modified to prevent FloodWait errors)
import aiohttp
import os
import time
from config import config
from utils import get_human_readable_size, get_progress_bar # Assuming these functions exist in your utils.py

# --- Throttling Logic ---
# Global dictionary to store the last time a message was updated.
# This helps us avoid editing the message too frequently.
# The key will be a unique identifier for the message being edited.
last_edit_time = {}

# We will only allow message edits once every 4 seconds.
EDIT_THROTTLE_SECONDS = 4.0

async def smart_progress_editor(status_message, text: str):
    """
    A custom editor that checks if enough time has passed before editing a message.
    This is the core of the FloodWait prevention.
    """
    # Create a unique key for the message
    message_key = f"{status_message.chat.id}_{status_message.id}"
    now = time.time()

    # Get the last time we edited this message, defaulting to 0 if it's the first time
    last_time = last_edit_time.get(message_key, 0)

    # If more than EDIT_THROTTLE_SECONDS have passed, we can edit the message
    if (now - last_time) > EDIT_THROTTLE_SECONDS:
        try:
            await status_message.edit_text(text)
            # IMPORTANT: Update the last edit time for this message
            last_edit_time[message_key] = now
        except Exception:
            # If we still get an error (e.g., message not modified), we just ignore it
            # and try again on the next scheduled update.
            pass

async def download_from_url(url: str, user_id: int, status_message) -> str or None:
    """Downloads a file from a direct URL with smart progress reporting."""
    file_name = url.split('/')[-1] or f"video_{int(time.time())}.mp4"
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    dest_path = os.path.join(user_download_dir, file_name)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    total_size = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    with open(dest_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(1024 * 1024):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = downloaded / total_size
                                # 1. Build the progress message text
                                progress_text = (
                                    f"📥 **Downloading from URL...**\n"
                                    f"➢ `{file_name}`\n"
                                    f"➢ {get_progress_bar(progress)} `{progress:.1%}`\n"
                                    f"➢ **Size:** `{get_human_readable_size(downloaded)}` / `{get_human_readable_size(total_size)}`"
                                )
                                # 2. Call our new smart editor instead of editing directly
                                await smart_progress_editor(status_message, progress_text)
                    
                    # Send a final update to show the download is done
                    await status_message.edit_text(f"✅ **Downloaded:** `{file_name}`\n\nPreparing to merge...")
                    return dest_path
                else:
                    await status_message.edit_text(f"❌ **Download Failed!**\nStatus: {resp.status} for URL: `{url}`")
                    return None
    except Exception as e:
        # If the bot is already flood-waited, even sending an error can fail.
        # So we wrap this in a try/except block too.
        try:
            await status_message.edit_text(f"❌ **Download Failed!**\nError: `{str(e)}`")
        except Exception:
            pass
        return None

async def download_from_tg(message, user_id: int, status_message) -> str or None:
    """Downloads a file from Telegram with smart progress reporting."""
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    
    # We define the progress callback here, which will be called by Pyrogram
    async def progress_func(current, total):
        progress = current / total
        file_name = message.video.file_name if message.video and message.video.file_name else "telegram_video.mp4"
        
        # 1. Build the progress message text
        progress_text = (
            f"📥 **Downloading from Telegram...**\n"
            f"➢ `{file_name}`\n"
            f"➢ {get_progress_bar(progress)} `{progress:.1%}`\n"
            f"➢ **Size:** `{get_human_readable_size(current)}` / `{get_human_readable_size(total)}`"
        )
        # 2. Call our new smart editor
        await smart_progress_editor(status_message, progress_text)

    try:
        file_path = await message.download(
            file_name=os.path.join(user_download_dir, ''),
            progress=progress_func
        )
        file_name = os.path.basename(file_path)
        await status_message.edit_text(f"✅ **Downloaded:** `{file_name}`\n\nPreparing to merge...")
        return file_path
    except Exception as e:
        try:
            await status_message.edit_text(f"❌ **Download Failed!**\nError: `{str(e)}`")
        except Exception:
            pass
        return None
