# uploader.py (Modified to accept custom thumbnail and filename)
import os
import time
import asyncio
from aiohttp import ClientSession, FormData
from random import choice
from config import config
from utils import get_human_readable_size, get_progress_bar, get_video_properties

# --- Throttling Logic (Unchanged) ---
last_edit_time = {}
EDIT_THROTTLE_SECONDS = 4.0

async def smart_progress_editor(status_message, text: str):
    """A custom editor that throttles message edits to prevent FloodWait errors."""
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

# --- RENAMED: from create_safe_thumbnail to create_default_thumbnail ---
async def create_default_thumbnail(video_path: str) -> str | None:
    """Creates a default thumbnail if the user doesn't provide one."""
    thumbnail_path = f"{os.path.splitext(video_path)[0]}.jpg"
    metadata = await get_video_properties(video_path)
    if not metadata or not metadata.get("duration"):
        print(f"Could not get duration for '{video_path}'. Skipping default thumbnail.")
        return None
        
    thumbnail_time = metadata["duration"] / 2
    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', video_path, 
        '-ss', str(thumbnail_time), '-vframes', '1', 
        '-c:v', 'mjpeg', '-f', 'image2', '-y', thumbnail_path
    ]
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        print(f"Error creating default thumbnail for '{video_path}': {stderr.decode().strip()}")
        return None
    return thumbnail_path if os.path.exists(thumbnail_path) else None

# --- GoFile Uploader (Unchanged) ---
class GofileUploader:
    def __init__(self, token=None):
        self.api_url = "https://api.gofile.io/"
        self.token = token or config.GOFILE_TOKEN
    async def __get_server(self):
        async with ClientSession() as session:
            async with session.get(f"{self.api_url}servers") as resp:
                resp.raise_for_status(); result = await resp.json()
                if result.get("status") == "ok": return choice(result["data"]["servers"])["name"]
                raise Exception("Failed to fetch GoFile upload server.")
    async def upload_file(self, file_path: str):
        if not os.path.isfile(file_path): raise FileNotFoundError(f"File not found: {file_path}")
        server = await self.__get_server()
        upload_url = f"https://{server}.gofile.io/uploadFile"
        data = FormData()
        if self.token: data.add_field("token", self.token)
        with open(file_path, "rb") as f:
            data.add_field("file", f, filename=os.path.basename(file_path))
            async with ClientSession() as session:
                async with session.post(upload_url, data=data) as resp:
                    resp.raise_for_status(); resp_json = await resp.json()
                    if resp_json.get("status") == "ok": return resp_json["data"]["downloadPage"]
                    else: raise Exception(f"GoFile upload failed: {resp_json.get('status')}")

# --- MODIFIED: upload_to_telegram now accepts custom data ---
async def upload_to_telegram(client, chat_id: int, file_path: str, status_message, custom_thumbnail: str | None, custom_filename: str):
    """Uploads the merged file to Telegram using user-provided data."""
    is_default_thumb_created = False
    thumb_to_upload = custom_thumbnail
    
    try:
        # Agar user ne thumbnail nahi diya (custom_thumbnail is None), to default banayein
        if not thumb_to_upload:
            await smart_progress_editor(status_message, "Analyzing video to create default thumbnail...")
            thumb_to_upload = await create_default_thumbnail(file_path)
            if thumb_to_upload:
                is_default_thumb_created = True

        # Video properties ab bhi zaroori hain (duration, width, height ke liye)
        metadata = await get_video_properties(file_path)
        duration = metadata.get('duration', 0) if metadata else 0
        width = metadata.get('width', 0) if metadata else 0
        height = metadata.get('height', 0) if metadata else 0

        # User ka diya hua filename istemal karein
        final_filename = f"{custom_filename}.mkv"
        caption = f"**File:** `{final_filename}`\n**Size:** `{get_human_readable_size(os.path.getsize(file_path))}`"

        async def progress(current, total):
            progress_percent = current / total
            progress_text = (f"📤 **Uploading to Telegram...**\n➢ {get_progress_bar(progress_percent)} `{progress_percent:.1%}`")
            await smart_progress_editor(status_message, progress_text)

        await client.send_video(
            chat_id=chat_id,
            video=file_path,
            caption=caption,
            file_name=final_filename, # Custom filename yahan set karein
            duration=duration,
            width=width,
            height=height,
            thumb=thumb_to_upload,
            progress=progress
        )
        await status_message.delete()
        return True
    except Exception as e:
        await status_message.edit_text(f"❌ **Upload Failed!**\nError: `{e}`")
        return False
    finally:
        # Agar default thumbnail banaya gaya tha, to use upload ke baad delete kar dein
        if is_default_thumb_created and thumb_to_upload and os.path.exists(thumb_to_upload):
            os.remove(thumb_to_upload)
