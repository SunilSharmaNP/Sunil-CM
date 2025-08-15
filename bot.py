# bot.py (New Interactive Flow)

import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup
from config import config
from downloader import download_from_url, download_from_tg
from merger import merge_videos
from uploader import GofileUploader, upload_to_telegram
from utils import cleanup_files, is_valid_url
from helper.compress import convert_video

user_data = {}

app = Client(
    "ss-merger-bot",
    api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN
)

def clear_user_data(user_id: int):
    if user_id in user_data:
        user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
        cleanup_files(user_download_dir)
        custom_thumb = user_data[user_id].get("custom_thumbnail")
        if custom_thumb and os.path.exists(custom_thumb):
            os.remove(custom_thumb)
        user_data.pop(user_id, None)

# --- START & CANCEL ---
@app.on_message(filters.command(["start", "help"]))
async def start_handler(_, message: Message):
    if not message.from_user: return
    clear_user_data(message.from_user.id)
    await message.reply_text(
        "👋 **Welcome! I am your Advanced Merger & Compressor Bot.**\n\n"
        "**How to use:**\n"
        "➢ Use `/merge` to start a new merge session.\n"
        "➢ Use `/compress` to start a new compress session.\n"
        "➢ Use `/cancel` at any time to stop the current operation.",
        quote=True
    )

@app.on_message(filters.command("cancel"))
async def cancel_handler(_, message: Message):
    if not message.from_user: return
    clear_user_data(message.from_user.id)
    await message.reply_text("✅ **Operation cancelled.**", quote=True, reply_markup={"remove_keyboard": True})

# --- MODE SETUP COMMANDS ---
@app.on_message(filters.command("merge"))
async def merge_command_handler(_, message: Message):
    if not message.from_user: return
    user_id = message.from_user.id
    clear_user_data(user_id)
    user_data[user_id] = {"state": "merge_mode", "queue": []}
    await message.reply_text(
        "**Okay, I'm ready for merging.**\n\n"
        "Send me your videos or direct links one by one. When you're done, press the 'Done' button below.",
        reply_markup=ReplyKeyboardMarkup([["Done Merging"]], resize_keyboard=True)
    )

@app.on_message(filters.command("compress"))
async def compress_command_handler(_, message: Message):
    if not message.from_user: return
    user_id = message.from_user.id
    clear_user_data(user_id)
    user_data[user_id] = {"state": "compress_mode"}
    await message.reply_text(
        "**Okay, I'm ready to compress.**\n\n"
        "Please send me the single video file or direct link you want to compress."
    )

# --- MAIN MESSAGE HANDLER (Handles files/links based on user's state) ---
@app.on_message(
    (filters.video | (filters.text & ~filters.command(["start", "help", "cancel", "merge", "compress"]))) &
    filters.private
)
async def main_message_handler(client, message: Message):
    if not message.from_user: return
    user_id = message.from_user.id
    user_state = user_data.get(user_id, {}).get("state")

    # --- MERGE MODE LOGIC ---
    if user_state == "merge_mode":
        item = message if message.video else message.text
        if isinstance(item, str):
            if not is_valid_url(item):
                await message.reply_text("⚠️ This link seems invalid. Please send a direct download link.")
                return
            if message.text.lower() == "done merging":
                if len(user_data[user_id]["queue"]) < 2:
                    await message.reply_text("You need at least two items to merge.", quote=True)
                    return
                await message.reply_text("Got it! Starting the merge process...", reply_markup={"remove_keyboard": True})
                await start_merge_process(client, message)
                return

        user_data[user_id]["queue"].append(item)
        queue_len = len(user_data[user_id]["queue"])
        
        reply_markup = ReplyKeyboardMarkup([["Done Merging"]], resize_keyboard=True)
        if queue_len >= 2:
            reply_markup = ReplyKeyboardMarkup([["Merge Now"], ["Done Merging"]], resize_keyboard=True)

        await message.reply_text(f"✅ **Item #{queue_len} added to queue!**", reply_markup=reply_markup)
    
    # --- COMPRESS MODE LOGIC ---
    elif user_state == "compress_mode":
        item = message if message.video else message.text
        if isinstance(item, str) and not is_valid_url(item):
            await message.reply_text("⚠️ This link seems invalid. Please send a direct download link.")
            return
        
        user_data[user_id]["state"] = "processing" # Lock state
        await start_compress_process(client, message, item)

    # --- TEXT COMMANDS IN MERGE MODE ---
    elif message.text and (message.text.lower() == "done merging" or message.text.lower() == "merge now"):
        if user_state == "merge_mode":
            if len(user_data[user_id]["queue"]) < 2:
                await message.reply_text("You need at least two items to merge.", quote=True)
                return
            await message.reply_text("Got it! Starting the merge process...", reply_markup={"remove_keyboard": True})
            await start_merge_process(client, message)
        else:
            await message.reply_text("Please start a new session with /merge first.")

# --- PROCESS STARTERS ---
async def start_merge_process(client, message):
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    status_msg = await message.reply_text("🚀 **Initializing Merge...**", quote=True)
    user_data[user_id]["status_message"] = status_msg

    video_paths = []
    queue = user_data[user_id]["queue"]
    for i, item in enumerate(queue):
        file_path = await download_from_url(item, user_id, status_msg, user_mention) if isinstance(item, str) else await download_from_tg(item, user_id, status_msg, user_mention)
        if not file_path:
            await status_msg.edit_text("A download failed. Cancelling operation.")
            clear_user_data(user_id)
            return
        video_paths.append(file_path)
            
    merged_path = await merge_videos(video_paths, user_id, status_msg, user_mention)
    if not merged_path:
        clear_user_data(user_id)
        return

    user_data[user_id]["final_file"] = merged_path
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload to Telegram", callback_data="upload_tg")], [InlineKeyboardButton("🔗 Upload to GoFile.io", callback_data="upload_gofile")]])
    await status_msg.edit_text("✅ **Merge Successful!**\n\nChoose where to upload the file:", reply_markup=keyboard)

async def start_compress_process(client, message, item_to_process):
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    status_msg = await message.reply_text("🚀 **Initializing Compression...**", quote=True)
    user_data[user_id]["status_message"] = status_msg

    file_path = await download_from_url(item_to_process, user_id, status_msg, user_mention) if isinstance(item_to_process, str) else await download_from_tg(message, user_id, status_msg, user_mention)
    if not file_path:
        clear_user_data(user_id)
        return

    compressed_path = await convert_video(file_path, os.path.dirname(file_path), status_msg, user_mention, user_id)
    if not compressed_path:
        clear_user_data(user_id)
        return
        
    user_data[user_id]["final_file"] = compressed_path
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload to Telegram", callback_data="upload_tg")], [InlineKeyboardButton("🔗 Upload to GoFile.io", callback_data="upload_gofile")]])
    await status_msg.edit_text("✅ **Compression Successful!**\n\nChoose where to upload the file:", reply_markup=keyboard)

# --- UPLOAD FLOW HANDLERS (Unchanged Logic, just bug fixes) ---
@app.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_data:
        await query.answer("Sorry, your session has expired.", show_alert=True)
        return

    data = query.data
    status_msg = user_data[user_id]["status_message"]
    final_file = user_data[user_id].get("final_file")

    if not final_file:
        await query.answer("Error: The processed file was not found.", show_alert=True)
        return
        
    await query.message.edit_reply_markup(None)
    
    if data == "upload_tg":
        user_data[user_id]["state"] = "waiting_for_thumbnail"
        await status_msg.edit_text("Please send the **thumbnail** you want to use, or send /notg_thumbnail for a default one.")
    
    elif data == "upload_gofile":
        await status_msg.edit_text("🚀 Uploading to GoFile.io...")
        try:
            link = await GofileUploader().upload_file(final_file)
            await status_msg.edit_text(f"✅ **GoFile Upload Complete!**\n\n🔗 **Link:** {link}")
        except Exception as e:
            await status_msg.edit_text(f"❌ **GoFile Upload Failed!**\nError: `{e}`")
        clear_user_data(user_id)

# --- THUMBNAIL & FILENAME HANDLERS (Unchanged) ---
async def is_waiting_for_thumbnail(_, __, message: Message):
    if not message.from_user: return False
    return user_data.get(message.from_user.id, {}).get("state") == "waiting_for_thumbnail"

@app.on_message(filters.photo & filters.private & filters.create(is_waiting_for_thumbnail))
async def thumbnail_handler(_, message: Message):
    user_id = message.from_user.id
    status_msg = user_data[user_id]["status_message"]
    await status_msg.edit_text("🖼️ Processing thumbnail...")
    thumb_path = await message.download(file_name=os.path.join(config.DOWNLOAD_DIR, str(user_id), "custom_thumb.jpg"))
    user_data[user_id]["custom_thumbnail"] = thumb_path
    user_data[user_id]["state"] = "waiting_for_filename"
    await status_msg.edit_text("✅ **Thumbnail saved!**\n\nNow, send the **filename** for the merged video (without extension).")

@app.on_message(filters.command("notg_thumbnail") & filters.private & filters.create(is_waiting_for_thumbnail))
async def no_thumbnail_handler(_, message: Message):
    user_id = message.from_user.id
    user_data[user_id]["custom_thumbnail"] = None
    user_data[user_id]["state"] = "waiting_for_filename"
    await user_data[user_id]["status_message"].edit_text("👍 **Okay, I will use a default thumbnail.**\n\nNow, send the **filename** for the merged video (without extension).")

async def is_waiting_for_filename(_, __, message: Message):
    if not message.from_user: return False
    return user_data.get(message.from_user.id, {}).get("state") == "waiting_for_filename"

@app.on_message(filters.text & filters.private & filters.create(is_waiting_for_filename))
async def filename_handler(client, message: Message):
    user_id = message.from_user.id
    status_msg = user_data[user_id]["status_message"]
    filename = os.path.basename(message.text)
    user_data[user_id]["custom_filename"] = filename
    user_data[user_id]["state"] = None
    
    await status_msg.edit_text(f"✅ **Filename set to:** `{filename}.mkv`\n\n🚀 Starting upload...")
    
    file_path = user_data[user_id]["final_file"]
    thumb_path = user_data[user_id].get("custom_thumbnail")
    
    await upload_to_telegram(client, message.chat.id, file_path, status_msg, thumb_path, filename, user_mention=message.from_user.mention)
    clear_user_data(user_id)

if __name__ == "__main__":
    print("Bot is starting with new interactive flow...")
    app.run()
