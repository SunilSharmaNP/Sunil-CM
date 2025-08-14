# downloader.py (Final version with new attractive progress template)
import aiohttp
import os
import time
from config import config
# Import the new template generator
from utils import generate_progress_string

# --- Throttling Logic (Unchanged) ---
last_edit_time = {}
EDIT_THROTTLE_SECONDS = 4.0

async def smart_progress_editor(status_message, text: str):
    """A custom editor that throttles message edits."""
    if not status_message or not hasattr(status_message, 'chat'): return
    message_key = f"{status_message.chat.id}_{status_message.id}"
    now = time.time()
    last_time = last_edit_time.get(message_key, 0)
    if (now - last_time) > EDIT_THROTTLE_SECONDS:
        try:
            await status_message.edit_text(text)
            last_edit_time[message_key] = now
        except Exception:
            pass

# --- NEW: Central progress hook for both URL and TG downloads ---
async def download_progress_hook(
    current: int,
    total: int,
    status_message,
    start_time: float,
    title: str,
    user_mention: str,
    user_id: int
):
    """Calculates speed, ETA and generates the attractive progress template."""
    progress = current / total
    # Calculate speed in bytes/second
    speed = current / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
    # Calculate estimated time of arrival in seconds
    eta = (total - current) / speed if speed > 0 else None
    
    # Generate the full template string using the utility function
    progress_text = generate_progress_string(
        title=title,
        status="Downloading",
        progress=progress,
        processed_bytes=current,
        total_bytes=total,
        speed=speed,
        eta=eta,
        start_time=start_time,
        user_mention=user_mention,
        user_id=user_id
    )
    # Update the message using the throttled editor
    await smart_progress_editor(status_message, progress_text)

# --- MODIFIED: download_from_url now uses the new hook ---
async def download_from_url(url: str, user_id: int, status_message, user_mention: str) -> str or None:
    """Downloads a file from a direct URL with the new progress template."""
    file_name = url.split('/')[-1] or f"video_{int(time.time())}.mp4"
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    dest_path = os.path.join(user_download_dir, file_name)
    start_time = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=60) as resp:
                if resp.status == 200:
                    total_size = int(resp.headers.get('content-length', 0))
                    with open(dest_path, 'wb') as f:
                        downloaded = 0
                        async for chunk in resp.content.iter_chunked(1024 * 1024):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                # Call the new central progress hook
                                await download_progress_hook(
                                    downloaded, total_size, status_message, start_time, 
                                    file_name, user_mention, user_id
                                )
                    return dest_path
                else:
                    await status_message.edit_text(f"❌ **Download Failed!**\nStatus: {resp.status}")
                    return None
    except Exception as e:
        await status_message.edit_text(f"❌ **Download Failed!**\nError: `{str(e)}`")
        return None

# --- MODIFIED: download_from_tg now uses the new hook ---
async def download_from_tg(message, user_id: int, status_message, user_mention: str) -> str or None:
    """Downloads a file from Telegram with the new progress template."""
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    start_time = time.time()
    file_name = message.video.file_name if message.video and message.video.file_name else "telegram_video.mp4"

    # The progress callback passed to pyrogram now just calls our hook
    async def progress_func(current, total):
        await download_progress_hook(current, total, status_message, start_time, file_name, user_mention, user_id)

    try:
        return await message.download(
            file_name=os.path.join(user_download_dir, ''),
            progress=progress_func
        )
    except Exception as e:
        await status_message.edit_text(f"❌ **Download Failed!**\nError: `{str(e)}`")
        return None
