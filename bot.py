# bot.py (Modified for interactive thumbnail and filename)
import os
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import config
from downloader import download_from_url, download_from_tg
from merger import merge_videos
from uploader import GofileUploader, upload_to_telegram
from utils import cleanup_files, is_valid_url

# In-memory dictionary to store user-specific data
# NEW: state, custom_thumbnail, aur custom_filename ke liye keys add ki gayi hain
user_data = {}

app = Client(
    "ss-merger-bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# --- State Management ke liye Custom Filters ---
async def is_waiting_for_thumbnail(_, __, message: Message):
    if not message.from_user: return False
    return user_data.get(message.from_user.id, {}).get("state") == "waiting_for_thumbnail"

async def is_waiting_for_filename(_, __, message: Message):
    if not message.from_user: return False
    return user_data.get(message.from_user.id, {}).get("state") == "waiting_for_filename"


# --- MODIFIED: clear_user_data ab custom thumbnail ko bhi saaf karega ---
def clear_user_data(user_id: int):
    """Clears all data and files associated with a user_id."""
    if user_id in user_data:
        user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
        cleanup_files(user_download_dir)
        
        # Agar custom thumbnail download hua tha, to use bhi delete karein
        custom_thumb = user_data[user_id].get("custom_thumbnail")
        if custom_thumb and os.path.exists(custom_thumb):
            os.remove(custom_thumb)
            
        user_data.pop(user_id, None)

# --- /start aur /cancel Handlers (wahi rahenge) ---
@app.on_message(filters.command(["start", "help"]))
async def start_handler(_, message: Message):
    if not message.from_user: return
    clear_user_data(message.from_user.id)
    await message.reply_text(
        "👋 **Hello! I am the Advanced Video Merger Bot.**\n\n"
        "**How to use:**\n"
        "1. Send me videos directly OR send direct download links (one per message).\n"
        "2. When you are ready, send the `/merge` command.\n\n"
        "Use `/cancel` at any time to clear your queue and start over.",
        quote=True
    )

@app.on_message(filters.command("cancel"))
async def cancel_handler(_, message: Message):
    if not message.from_user: return
    clear_user_data(message.from_user.id)
    await message.reply_text("✅ **Operation cancelled.**\nYour queue has been cleared.", quote=True)


# --- file_handler ab state check karega ---
# NEW: /notg_thumbnail ko command list mein add kiya gaya hai
USED_COMMANDS = ["start", "help", "cancel", "merge", "notg_thumbnail"]
@app.on_message(filters.video | (filters.text & ~filters.command(USED_COMMANDS)) & filters.private)
async def file_handler(_, message: Message):
    if not message.from_user: return
    user_id = message.from_user.id
    
    # Agar bot kisi cheez ka intezaar kar raha hai, toh naye files na le
    if user_data.get(user_id, {}).get("state"):
        await message.reply_text("I am waiting for you to send a thumbnail or filename. Please follow the instructions or use /cancel to start over.")
        return
    
    if user_id not in user_data:
        # Puraane 'status_message' aur 'merged_file' ko hata diya gaya hai,
        # kyunki woh ab merge ke time par set hote hain.
        user_data[user_id] = {"queue": []}
    
    item = message if message.video else message.text
    item_type = "Video" if message.video else "Link"
    user_data[user_id].setdefault("queue", []).append(item)
    
    await message.reply_text(
        f"✅ **{item_type} added to queue!**\n\n"
        f"➢ **Total items in queue:** `{len(user_data[user_id]['queue'])}`\n"
        f"Send more, or use `/merge` to combine them.",
        quote=True
    )

# --- MODIFIED: merge_handler ab thumbnail maangega ---
@app.on_message(filters.command("merge") & filters.private)
async def merge_handler(client, message: Message):
    if not message.from_user: return
    user_id = message.from_user.id

    if user_id not in user_data or not user_data[user_id].get("queue"):
        await message.reply_text("Your queue is empty. Send me some videos or links first.", quote=True)
        return
    if len(user_data[user_id]["queue"]) < 2:
        await message.reply_text("You need at least two items in your queue to merge.", quote=True)
        return
        
    status_msg = await message.reply_text("🚀 **Starting process...**", quote=True)
    user_data[user_id]["status_message"] = status_msg

    video_paths = []
    queue = user_data[user_id]["queue"]
    for i, item in enumerate(queue):
        await status_msg.edit_text(f"Downloading item {i+1} of {len(queue)}...")
        file_path = await download_from_url(item, user_id, status_msg) if isinstance(item, str) else await download_from_tg(item, user_id, status_msg)
        if not file_path:
            await status_msg.edit_text("A download failed. Cancelling operation.")
            clear_user_data(user_id)
            return
        video_paths.append(file_path)
            
    merged_path = await merge_videos(video_paths, user_id, status_msg)
    if not merged_path:
        clear_user_data(user_id)
        return

    # --- Naya Interactive Flow Yahan se Shuru ---
    user_data[user_id]["merged_file"] = merged_path
    user_data[user_id]["state"] = "waiting_for_thumbnail" # User ki state set karein
    
    await status_msg.edit_text(
        "✅ **Merge Successful!**\n\n"
        "Now, please send me the **thumbnail** you want to use for the video.\n\n"
        "To use a default thumbnail, send /notg_thumbnail."
    )

# --- NAYA HANDLER: Jab user thumbnail ke liye photo bhejta hai ---
@app.on_message(filters.photo & filters.private & filters.create(is_waiting_for_thumbnail))
async def thumbnail_handler(_, message: Message):
    user_id = message.from_user.id
    status_msg = user_data[user_id]["status_message"]
    
    await status_msg.edit_text("🖼️ Processing thumbnail...")
    thumb_path = await message.download(file_name=os.path.join(config.DOWNLOAD_DIR, str(user_id), "custom_thumb.jpg"))
    
    user_data[user_id]["custom_thumbnail"] = thumb_path
    user_data[user_id]["state"] = "waiting_for_filename" # Agli state par jaayein
    
    await status_msg.edit_text(
        "✅ **Thumbnail saved!**\n\n"
        "Now, send me the **filename** (without extension) you want for the merged video."
    )

# --- NAYA HANDLER: Jab user default thumbnail chahta hai ---
@app.on_message(filters.command("notg_thumbnail") & filters.private & filters.create(is_waiting_for_thumbnail))
async def no_thumbnail_handler(_, message: Message):
    user_id = message.from_user.id
    user_data[user_id]["custom_thumbnail"] = None # None set karein
    user_data[user_id]["state"] = "waiting_for_filename" # Agli state par jaayein
    
    await user_data[user_id]["status_message"].edit_text(
        "👍 **Okay, I will generate a default thumbnail.**\n\n"
        "Now, send me the **filename** (without extension) you want for the merged video."
    )

# --- NAYA HANDLER: Jab user filename bhejta hai ---
@app.on_message(filters.text & filters.private & filters.create(is_waiting_for_filename))
async def filename_handler(_, message: Message):
    user_id = message.from_user.id
    status_msg = user_data[user_id]["status_message"]
    
    filename = os.path.basename(message.text) # Filename ko sanitize karein
    user_data[user_id]["custom_filename"] = filename
    user_data[user_id]["state"] = None # State ko clear karein
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Upload to Telegram", callback_data="upload_tg")],
        [InlineKeyboardButton("🔗 Upload to GoFile.io", callback_data="upload_gofile")]
    ])
    
    await status_msg.edit_text(
        f"✅ **Filename set to:** `{filename}.mkv`\n\n"
        "Final step! Choose where you want to upload the file:",
        reply_markup=keyboard
    )

# --- MODIFIED: callback_handler ab save kiya hua data istemal karega ---
@app.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    if user_id not in user_data or not user_data[user_id].get("merged_file"):
        await query.answer("Sorry, your session has expired or been cancelled.", show_alert=True)
        return

    await query.message.edit_reply_markup(None)
    status_msg = user_data[user_id]["status_message"]
    
    if data == "upload_tg":
        await status_msg.edit_text("🚀 Preparing to upload to Telegram...")
        
        # User se save ki hui saari jaankari yahan nikalein
        file_path = user_data[user_id]["merged_file"]
        thumb_path = user_data[user_id].get("custom_thumbnail")
        file_name = user_data[user_id].get("custom_filename")

        # `uploader.py` ko saari jaankari pass karein
        await upload_to_telegram(
            client=client, 
            chat_id=query.message.chat.id, 
            file_path=file_path, 
            status_message=status_msg,
            custom_thumbnail=thumb_path,
            custom_filename=file_name
        )
    
    elif data == "upload_gofile":
        await status_msg.edit_text("🚀 Preparing to upload to GoFile.io...")
        try:
            uploader = GofileUploader()
            link = await uploader.upload_file(user_data[user_id]["merged_file"])
            await status_msg.edit_text(
                f"✅ **Upload to GoFile Complete!**\n\n"
                f"🔗 **Your Link:** {link}\n\n"
                f"Note: Links may expire based on GoFile's policy for free accounts."
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ **GoFile Upload Failed!**\nError: `{e}`")
    
    clear_user_data(user_id)


if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
