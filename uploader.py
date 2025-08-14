# uploader.py (Modified to prevent FloodWait and FFmpeg errors)
import os
import time
import asyncio
from aiohttp import ClientSession, FormData
from random import choice
from config import config
from utils import get_human_readable_size, get_progress_bar, get_video_properties # We will use a new robust function

# --- Throttling Logic (to prevent FloodWait) ---
last_edit_time = {}
EDIT_THROTTLE_SECONDS = 4.0

async def smart_progress_editor(status_message, text: str):
    """
    A custom editor that throttles message edits to prevent FloodWait errors.
    """
    message_key = f"{status_message.chat.id}_{status_message.id}"
    now = time.time()
    last_time = last_edit_time.get(message_key, 0)

    if (now - last_time) > EDIT_THROTTLE_SECONDS:
        try:
            await status_message.edit_text(text)
            last_edit_time[message_key] = now
        except Exception:
            pass

# --- Safer Thumbnail Generation ---
async def create_safe_thumbnail(video_path: str) -> str | None:
    """
    Creates a thumbnail safely by seeking to the middle of the video.
    Returns the path to the thumbnail or None if it fails.
    """
    thumbnail_path = f"{os.path.splitext(video_path)[0]}.jpg"
    
    # Get video duration using our robust utility function
    metadata = await get_video_properties(video_path)
    if not metadata or not metadata.get("duration"):
        print(f"Could not get duration for '{video_path}'. Skipping thumbnail.")
        return None
        
    # Seek to the middle of the video, which is always a safe timestamp
    thumbnail_time = metadata["duration"] / 2

    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-i', video_path, 
        '-ss', str(thumbnail_time), 
        '-vframes', '1', 
        '-c:v', 'mjpeg', '-f', 'image2', 
        '-y', thumbnail_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print(f"Error creating thumbnail for '{video_path}': {stderr.decode().strip()}")
        return None
    
    return thumbnail_path if os.path.exists(thumbnail_path) else None

# --- GoFile Uploader (Unchanged, it was already good) ---
class GofileUploader:
    def __init__(self, token=None):
        self.api_url = "https://api.gofile.io/"
        self.token = token or config.GOFILE_TOKEN

    async def __get_server(self):
        async with ClientSession() as session:
            async with session.get(f"{self.api_url}servers") as resp:
                resp.raise_for_status()
                result = await resp.json()
                if result.get("status") == "ok":
                    servers = result["data"]["servers"]
                    return choice(servers)["name"]
                raise Exception("Failed to fetch GoFile upload server.")

    async def upload_file(self, file_path: str):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        server = await self.__get_server()
        upload_url = f"https://{server}.gofile.io/uploadFile"

        data = FormData()
        if self.token:
            data.add_field("token", self.token)
        
        with open(file_path, "rb") as f:
            data.add_field("file", f, filename=os.path.basename(file_path))
            async with ClientSession() as session:
                async with session.post(upload_url, data=data) as resp:
                    resp.raise_for_status()
                    resp_json = await resp.json()
                    if resp_json.get("status") == "ok":
                        return resp_json["data"]["downloadPage"]
                    else:
                        raise Exception(f"GoFile upload failed: {resp_json.get('status')}")


# --- Telegram Uploader (Modified) ---
async def upload_to_telegram(client, chat_id: int, file_path: str, status_message):
    try:
        file_size = os.path.getsize(file_path)
        
        await smart_progress_editor(status_message, "Analyzing video and creating thumbnail...")
        
        # Get reliable metadata and thumbnail path
        metadata = await get_video_properties(file_path)
        thumbnail_path = await create_safe_thumbnail(file_path)

        duration = metadata.get('duration', 0)
        width = metadata.get('width', 0)
        height = metadata.get('height', 0)
        
        caption = f"**✅ Merge Successful!**\n\n**File:** `{os.path.basename(file_path)}`\n**Size:** `{get_human_readable_size(file_size)}`"

        # Define the throttled progress callback for uploading
        async def progress(current, total):
            progress_percent = current / total
            progress_text = (
                f"📤 **Uploading to Telegram...**\n"
                f"➢ {get_progress_bar(progress_percent)} `{progress_percent:.1%}`"
            )
            await smart_progress_editor(status_message, progress_text)

        await client.send_video(
            chat_id=chat_id, video=file_path, caption=caption,
            duration=duration, width=width, height=height,
            thumb=thumbnail_path, progress=progress
        )
        
        await status_message.delete()
        return True
    except Exception as e:
        try:
            await status_message.edit_text(f"❌ **Upload Failed!**\nError: `{e}`")
        except Exception:
            pass # Suppress error if we are already flood-waited
        return False
    finally:
        # Clean up thumbnail file if it was created
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
