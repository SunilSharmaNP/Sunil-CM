# bot.py
import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import config
from downloader import download_from_url, download_from_tg
from merger import merge_videos
from uploader import GofileUploader, upload_to_telegram
from utils import cleanup_files, is_valid_url

# In-memory dictionary to store user-specific data
# Format: {user_id: {"queue": [msg_or_url, ...], "status_message": msg, "merged_file": path}}
user_data = {}

app = Client(
    "ss-merger-bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

def clear_user_data(user_id: int):
    """Clears all data and files associated with a user_id."""
    if user_id in user_data:
        user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
        cleanup_files(user_download_dir)
        user_data.pop(user_id, None)

@app.on_message(filters.command(["start", "help"]))
async def start_handler(_, message: Message):
    clear_user_data(message.from_user.id)
    await message.reply_text(
        "👋 **Hello! I am the Advanced Video Merger Bot.**\n\n"
        "**How to use:**\n"
        "1. Send me videos directly OR send direct download links (one per message).\n"
        "2. I will add them to your queue.\n"
        "3. When you are ready, send the `/merge` command.\n"
        "4. After merging, I'll ask you where to upload the file.\n\n"
        "Use `/cancel` at any time to clear your queue and start over.",
        quote=True
    )

@app.on_message(filters.command("cancel"))
async def cancel_handler(_, message: Message):
    clear_user_data(message.from_user.id)
    await message.reply_text("✅ **Operation cancelled.**\nYour queue has been cleared.", quote=True)

@app.on_message(filters.video | (filters.text & ~filters.command))
async def file_handler(_, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {"queue": [], "status_message": None, "merged_file": None}
    
    item = None
    item_type = ""
    
    if message.video:
        item = message
        item_type = "Video"
    elif message.text and is_valid_url(message.text):
        item = message.text
        item_type = "Link"
    else:
        await message.reply_text("⚠️ Please send a video file or a valid direct download link.", quote=True)
        return

    user_data[user_id]["queue"].append(item)
    
    await message.reply_text(
        f"✅ **{item_type} added to queue!**\n\n"
        f"➢ **Total items in queue:** `{len(user_data[user_id]['queue'])}`\n"
        f"Send more, or use `/merge` to combine them.",
        quote=True
    )

@app.on_message(filters.command("merge"))
async def merge_handler(client, message: Message):
    user_id = message.from_user.id

    if user_id not in user_data or not user_data[user_id]["queue"]:
        await message.reply_text("Your queue is empty. Send me some videos or links first.", quote=True)
        return

    if len(user_data[user_id]["queue"]) < 2:
        await message.reply_text("You need at least two items in your queue to merge.", quote=True)
        return
        
    status_msg = await message.reply_text("🚀 **Starting process...**", quote=True)
    user_data[user_id]["status_message"] = status_msg

    # --- Download Phase ---
    video_paths = []
    queue = user_data[user_id]["queue"]
    for i, item in enumerate(queue):
        await status_msg.edit_text(f"Downloading item {i+1} of {len(queue)}...")
        if isinstance(item, str): # It's a URL
            file_path = await download_from_url(item, user_id, status_msg)
        else: # It's a Message object
            file_path = await download_from_tg(item, user_id, status_msg)
        
        if file_path:
            video_paths.append(file_path)
        else:
            await status_msg.edit_text("A download failed. Cancelling operation.")
            clear_user_data(user_id)
            return
            
    # --- Merge Phase ---
    merged_path = await merge_videos(video_paths, user_id, status_msg)
    if not merged_path:
        clear_user_data(user_id)
        return

    user_data[user_id]["merged_file"] = merged_path
    
    # --- Upload Choice Phase ---
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Upload to Telegram", callback_data="upload_tg")],
        [InlineKeyboardButton("🔗 Upload to GoFile.io", callback_data="upload_gofile")]
    ])
    await status_msg.edit_text(
        "✅ **Merge Successful!**\n\n"
        "Choose where you want to upload the file:",
        reply_markup=keyboard
    )

@app.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    if user_id not in user_data or not user_data[user_id].get("merged_file"):
        await query.answer("Sorry, your session has expired or been cancelled.", show_alert=True)
        return

    status_msg = user_data[user_id]["status_message"]
    file_path = user_data[user_id]["merged_file"]

    await query.message.edit_reply_markup(None) # Remove buttons

    if data == "upload_tg":
        await status_msg.edit_text("Starting upload to Telegram...")
        success = await upload_to_telegram(client, query.message.chat.id, file_path, status_msg)
    
    elif data == "upload_gofile":
        await status_msg.edit_text("Starting upload to GoFile.io...")
        try:
            uploader = GofileUploader()
            link = await uploader.upload_file(file_path)
            await status_msg.edit_text(
                f"✅ **Upload to GoFile Complete!**\n\n"
                f"🔗 **Your Link:** {link}\n\n"
                f"Note: Links may expire based on GoFile's policy for free accounts."
            )
            success = True
        except Exception as e:
            await status_msg.edit_text(f"❌ **GoFile Upload Failed!**\nError: `{e}`")
            success = False
    
    # Final cleanup
    clear_user_data(user_id)


if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
