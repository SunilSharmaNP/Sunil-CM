from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN
from downloader import download_file
from merger import merge_videos
from uploader import upload_to_gofile
import asyncio
import os
import uuid

bot = Client("video_merger_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("merge"))
async def merge_cmd(client, message):
    user_input = message.text.split()
    links = user_input[1:]  # skip /merge

    if not links:
        await message.reply("कृपया कम से कम दो direct video links दें।\nउदाहरण:\n/merge link1 link2 link3")
        return

    await message.reply("डाउनलोड शुरू कर रहा हूँ...")

    downloaded_files = []
    for link in links:
        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        success = await download_file(link, filename)
        if success:
            downloaded_files.append(filename)
        else:
            await message.reply(f"डाउनलोड फेल: {link}")

    if len(downloaded_files) < 2:
        await message.reply("कम से कम दो वीडियो डाउनलोड होनी चाहिए merge के लिए।")
        return

    await message.reply("Merging videos with FFmpeg...")

    merged_filename = merge_videos(downloaded_files)
    if not merged_filename:
        await message.reply("Merge failed. शायद वीडियो formats अलग हों।")
        return

    await message.reply("GoFile.io पर अपलोड कर रहा हूँ...")

    gofile_link = upload_to_gofile(merged_filename)
    if gofile_link:
        await message.reply(f"✅ फाइल तैयार है: {gofile_link}")
    else:
        await message.reply("Upload failed on GoFile.io")

    # Cleanup
    for file in downloaded_files:
        os.remove(file)
    if os.path.exists(merged_filename):
        os.remove(merged_filename)

bot.run()
