from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN
from downloader import download_file
from merger import merge_videos
from uploader import GofileUploader
from config import GOFILE_TOKEN
from uploader import upload_to_gofile
import asyncio
import os
import uuid

bot = Client("video_merger_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("merge"))
async def merge_cmd(client, message):
    # (video download, merge वाला existing पार्ट यथावत...)

    await message.reply("🙌 GoFile.io पर अपलोड कर रहा हूँ...")

    try:
        uploader = GofileUploader(token=GOFILE_TOKEN)
        gofile_link = await uploader.upload_file(merged_filename)

        await message.reply(f"✅ फ़ाइल सफलतापूर्वक अपलोड हुई:\n{gofile_link}")
    except Exception as e:
        await message.reply(f"❌ Upload failed: {str(e)}") {str(e)}")
