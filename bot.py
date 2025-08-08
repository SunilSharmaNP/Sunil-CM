from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN, GOFILE_TOKEN
from downloader import download_file
from merger import merge_videos
from uploader import GofileUploader
import asyncio
import os
import uuid

bot = Client("video_merger_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("merge"))
async def merge_cmd(client, message):
    user_input = message.text.strip().split()
    links = user_input[1:]  # skip "/merge" command itself

    if not links or len(links) < 2:
        await message.reply("⚠️ कृपया कम से कम 2 वीडियो लिंक्स दें\nउदाहरण:\n`/merge link1 link2 link3`")
        return

    await message.reply("⬇️ वीडियो डाउनलोड किया जा रहा है...")

    downloaded_files = []
    for link in links:
        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        try:
            success = await download_file(link, filename)
            if success:
                downloaded_files.append(filename)
            else:
                await message.reply(f"❌ डाउनलोड फेल: {link}")
        except Exception as e:
            await message.reply(f"🔥 Error downloading {link}\n{str(e)}")

    if len(downloaded_files) < 2:
        await message.reply("❌ दो या अधिक वीडियो डाउनलोड नहीं हो पाए, मर्जिंग संभव नहीं।")
        return

    await message.reply("⚙️ मर्जिंग चालू है...")

    merged_filename = merge_videos(downloaded_files)
    if not merged_filename or not os.path.exists(merged_filename):
        await message.reply("❌ मर्ज फेल — शायद वीडियो फॉर्मेट अलग हैं या ffmpeg error है।")
        return

    await message.reply("🚀 GoFile.io पर अपलोड किया जा रहा है...")

    try:
        uploader = GofileUploader(token=GOFILE_TOKEN)
        gofile_link = await uploader.upload_file(merged_filename)

        await message.reply(f"✅ फ़ाइल सफलतापूर्वक अपलोड हुई:\n{gofile_link}")
    except Exception as e:
        await message.reply(f"❌ Upload failed: {str(e)}")

    # Cleanup
    for file in downloaded_files:
        if os.path.exists(file):
            os.remove(file)
    if os.path.exists(merged_filename):
        os.remove(merged_filename)

bot.run()
