# downloader.py

import aiohttp
import os
import time
from config import config
# 1. utils से नया 'generate_progress_string' इम्पोर्ट किया गया
from utils import generate_progress_string

# --- थ्रॉटलिंग लॉजिक (यह अपरिवर्तित है) ---
last_edit_time = {}
EDIT_THROTTLE_SECONDS = 4.0

async def smart_progress_editor(status_message, text: str):
    """एक कस्टम एडिटर जो संदेश को संपादित करने से पहले जांचता है कि पर्याप्त समय बीत चुका है या नहीं।"""
    if not status_message: return
    message_key = f"{status_message.chat.id}_{status_message.id}"
    now = time.time()
    last_time = last_edit_time.get(message_key, 0)

    if (now - last_time) > EDIT_THROTTLE_SECONDS:
        try:
            await status_message.edit_text(text)
            last_edit_time[message_key] = now
        except Exception:
            pass

# 2. फंक्शन सिग्नेचर में user_mention जोड़ा गया
async def download_from_url(url: str, user_id: int, status_message, user_mention: str) -> str or None:
    """एक सीधे URL से फाइल डाउनलोड करता है और आकर्षक प्रोग्रेस रिपोर्टिंग करता है।"""
    file_name = url.split('/')[-1].split('?')[0] or f"video_{int(time.time())}.mp4"
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    dest_path = os.path.join(user_download_dir, file_name)
    start_time = time.time() # प्रोग्रेस की गणना के लिए जोड़ा गया

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
                                now = time.time()
                                progress = downloaded / total_size
                                speed = downloaded / (now - start_time) if (now - start_time) > 0 else 0
                                eta = (total_size - downloaded) / speed if speed > 0 else 0
                                
                                # 3. पुराने प्रोग्रेस टेक्स्ट को 'generate_progress_string' से बदला गया
                                progress_text = generate_progress_string(
                                    title=file_name, status="Downloading", progress=progress,
                                    processed_bytes=downloaded, total_bytes=total_size,
                                    speed=speed, eta=eta, start_time=start_time,
                                    user_mention=user_mention, user_id=user_id
                                )
                                await smart_progress_editor(status_message, progress_text)
                    
                    # 4. अंतिम संदेश को सरल बनाया गया
                    await status_message.edit_text(f"✅ **Downloaded:** `{file_name}`")
                    return dest_path
                else:
                    await status_message.edit_text(f"❌ **Download Failed!**\nStatus Code: {resp.status}")
                    return None
    except Exception as e:
        await status_message.edit_text(f"❌ **Download Error!**\n`{str(e)}`")
        return None

# 2. फंक्शन सिग्नेचर में user_mention जोड़ा गया
async def download_from_tg(message, user_id: int, status_message, user_mention: str) -> str or None:
    """टेलीग्राम से फाइल डाउनलोड करता है और आकर्षक प्रोग्रेस रिपोर्टिंग करता है।"""
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    start_time = time.time() # प्रोग्रेस की गणना के लिए जोड़ा गया
    
    async def progress_func(current, total):
        now = time.time()
        progress = current / total
        speed = current / (now - start_time) if (now - start_time) > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0
        file_name = message.video.file_name if message.video and message.video.file_name else "telegram_video.mp4"

        # 3. पुराने प्रोग्रेस टेक्स्ट को 'generate_progress_string' से बदला गया
        progress_text = generate_progress_string(
            title=file_name, status="Downloading", progress=progress,
            processed_bytes=current, total_bytes=total,
            speed=speed, eta=eta, start_time=start_time,
            user_mention=user_mention, user_id=user_id
        )
        await smart_progress_editor(status_message, progress_text)

    try:
        file_path = await message.download(
            file_name=os.path.join(user_download_dir, ''),
            progress=progress_func
        )
        file_name = os.path.basename(file_path)
        # 4. अंतिम संदेश को सरल बनाया गया
        await status_message.edit_text(f"✅ **Downloaded:** `{file_name}`")
        return file_path
    except Exception as e:
        await status_message.edit_text(f"❌ **Download Failed!**\n`{str(e)}`")
        return None
