# downloader.py
import aiohttp
import os
import time
from config import config
from utils import get_human_readable_size, get_progress_bar, get_time_left

async def download_from_url(url: str, user_id: int, status_message) -> str or None:
    """Downloads a file from a direct URL and saves it."""
    file_name = url.split('/')[-1] or f"video_{int(time.time())}.mp4"
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    dest_path = os.path.join(user_download_dir, file_name)

    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    total_size = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    with open(dest_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(1024 * 1024):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = downloaded / total_size
                                elapsed_time = time.time() - start_time
                                await status_message.edit_text(
                                    f"📥 **Downloading from URL...**\n"
                                    f"➢ `{file_name}`\n"
                                    f"➢ {get_progress_bar(progress)} `{progress:.1%}`\n"
                                    f"➢ **Size:** `{get_human_readable_size(downloaded)}` / `{get_human_readable_size(total_size)}`"
                                )
                    return dest_path
                else:
                    await status_message.edit_text(f"❌ **Download Failed!**\nStatus: {resp.status} for URL: `{url}`")
                    return None
    except Exception as e:
        await status_message.edit_text(f"❌ **Download Failed!**\nError: `{str(e)}`")
        return None

async def download_from_tg(message, user_id: int, status_message) -> str or None:
    """Downloads a file sent via Telegram."""
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    
    start_time = time.time()

    async def progress_func(current, total):
        progress = current / total
        elapsed_time = time.time() - start_time
        try:
            await status_message.edit_text(
                f"📥 **Downloading from Telegram...**\n"
                f"➢ {get_progress_bar(progress)} `{progress:.1%}`\n"
                f"➢ **Size:** `{get_human_readable_size(current)}` / `{get_human_readable_size(total)}`"
            )
        except:
            pass

    try:
        file_path = await message.download(
            file_name=os.path.join(user_download_dir, ''),
            progress=progress_func
        )
        return file_path
    except Exception as e:
        await status_message.edit_text(f"❌ **Download Failed!**\nError: `{str(e)}`")
        return None
