# downloader.py
import aiohttp
import os
from config import DOWNLOAD_DIR


async def download_file(url: str, filename: str) -> str or None:
    """
    Downloads a file from a direct URL and saves it to DOWNLOAD_DIR.
    
    Args:
        url (str): The direct link to download from.
        filename (str): The filename to save as (inside DOWNLOAD_DIR).
        
    Returns:
        str: Path to downloaded file if successful, else None.
    """
    dest_path = os.path.join(DOWNLOAD_DIR, filename)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(dest_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024 * 1024)  # 1 MB chunks
                            if not chunk:
                                break
                            f.write(chunk)
                    return dest_path
                else:
                    print(f"[Downloader] Failed with status {resp.status} for {url}")
    except Exception as e:
        print(f"[Downloader] Error while downloading {url} -> {str(e)}")
    
    return None


async def download_tg_file(message, filename: str) -> str or None:
    """
    Downloads a file sent via Telegram directly to DOWNLOAD_DIR.

    Args:
        message: The Pyrogram message object containing the media.
        filename (str): Desired filename to save.

    Returns:
        str: Path to downloaded file if successful, else None.
    """
    dest_path = os.path.join(DOWNLOAD_DIR, filename)
    try:
        await message.download(file_name=dest_path)
        return dest_path
    except Exception as e:
        print(f"[Downloader] Error downloading Telegram file: {str(e)}")
        return None
