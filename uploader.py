# uploader.py
import os
import time
from aiofiles.os import path as aiopath
from aiohttp import ClientSession, FormData
from random import choice
from config import config
from utils import get_human_readable_size, get_progress_bar, get_time_left, get_video_metadata, create_thumbnail

# --- GoFile Uploader ---
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
        if not await aiopath.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        server = await self.__get_server()
        upload_url = f"https://{server}.gofile.io/uploadFile"

        data = FormData()
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


# --- Telegram Uploader ---
async def upload_to_telegram(client, chat_id: int, file_path: str, status_message):
    start_time = time.time()
    file_size = os.path.getsize(file_path)
    
    metadata = get_video_metadata(file_path)
    duration = int(metadata.get('duration', 0))
    width = metadata.get('width', 0)
    height = metadata.get('height', 0)
    
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(chat_id))
    thumbnail_path = create_thumbnail(file_path, os.path.join(user_download_dir, "thumbnail.jpg"), duration)

    caption = f"**Merged Video** | `{get_human_readable_size(file_size)}`"

    async def progress(current, total):
        progress_percent = current / total
        elapsed_time = time.time() - start_time
        try:
            await status_message.edit_text(
                f"📤 **Uploading to Telegram...**\n"
                f"➢ {get_progress_bar(progress_percent)} `{progress_percent:.1%}`"
            )
        except:
            pass

    try:
        await client.send_video(
            chat_id=chat_id, video=file_path, caption=caption,
            duration=duration, width=width, height=height,
            thumb=thumbnail_path, progress=progress
        )
        await status_message.delete()
        return True
    except Exception as e:
        await status_message.edit_text(f"❌ **Upload Failed!**\nError: `{e}`")
        return False
