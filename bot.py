# bot.py (मौजूदा कोड + नया एन्कोडिंग फीचर)
import os
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import config
from downloader import download_from_url, download_from_tg
from merger import merge_videos
from uploader import GofileUploader, upload_to_telegram
from utils import cleanup_files, is_valid_url
# --- नया इम्पोर्ट ---
from encoder import process_video_encoding

user_data = {}

app = Client(
    "ss-merger-bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

async def is_waiting_for_thumbnail(_, __, message: Message):
    if not message.from_user: return False
    return user_data.get(message.from_user.id, {}).get("state") == "waiting_for_thumbnail"

async def is_waiting_for_filename(_, __, message: Message):
    if not message.from_user: return False
    return user_data.get(message.from_user.id, {}).get("state") == "waiting_for_filename"

def clear_user_data(user_id: int):
    if user_id in user_data:
        user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
        cleanup_files(user_download_dir)
        custom_thumb = user_data[user_id].get("custom_thumbnail")
        if custom_thumb and os.path.exists(custom_thumb):
            os.remove(custom_thumb)
        user_data.pop(user_id, None)

@app.on_message(filters.command(["start", "help"]))
async def start_handler(_, message: Message):
    if not message.from_user: return
    clear_user_data(message.from_user.id)
    await message.reply_text(
        "👋 **Hello! I am the Advanced Video Merger & Encoder Bot.**\n\n"
        "**How to use:**\n"
        "➢ **To Merge:** Send videos/links, then use `/merge`.\n"
        "➢ **To Encode:** Reply to a video/link with `/encode`.\n\n"
        "Use `/cancel` at any time to clear your current operation.",
        quote=True
    )

@app.on_message(filters.command("cancel"))
async def cancel_handler(_, message: Message):
    if not message.from_user: return
    clear_user_data(message.from_user.id)
    await message.reply_text("✅ **Operation cancelled.**\nYour queue has been cleared.", quote=True)

# --- थंबनेल और फ़ाइलनेम हैंडलर्स (कोई बदलाव नहीं) ---
@app.on_message(filters.photo & filters.private & filters.create(is_waiting_for_thumbnail))
async def thumbnail_handler(_, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    status_msg = user_data[user_id]["status_message"]
    await status_msg.edit_text("🖼️ Processing thumbnail...")
    thumb_path = await message.download(file_name=os.path.join(config.DOWNLOAD_DIR, str(user_id), "custom_thumb.jpg"))
    user_data[user_id]["custom_thumbnail"] = thumb_path
    user_data[user_id]["state"] = "waiting_for_filename"
    await status_msg.edit_text(
        "✅ **Thumbnail saved!**\n\n"
        "Now, send me the **filename** (without extension) you want for the final video."
    )

@app.on_message(filters.command("notg_thumbnail") & filters.private & filters.create(is_waiting_for_thumbnail))
async def no_thumbnail_handler(_, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    user_data[user_id]["custom_thumbnail"] = None
    user_data[user_id]["state"] = "waiting_for_filename"
    await user_data[user_id]["status_message"].edit_text(
        "👍 **Okay, I will generate a default thumbnail.**\n\n"
        "Now, send me the **filename** (without extension) you want for the final video."
    )

@app.on_message(filters.text & filters.private & filters.create(is_waiting_for_filename))
async def filename_handler(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    user_mention = message.from_user.mention
    status_msg = user_data[user_id]["status_message"]
    filename = os.path.basename(message.text)
    user_data[user_id]["custom_filename"] = filename
    user_data[user_id]["state"] = None
    
    await status_msg.edit_text(f"✅ **Filename set to:** `{filename}.mkv`\n\n🚀 Starting final upload to Telegram...")
    
    # यह मर्ज और एन्कोड दोनों के लिए काम करेगा
    file_path = user_data[user_id]["merged_file"]
    thumb_path = user_data[user_id].get("custom_thumbnail")
    
    await upload_to_telegram(
        client=client, chat_id=message.chat.id, file_path=file_path,
        status_message=status_msg, custom_thumbnail=thumb_path, custom_filename=filename,
        user_mention=user_mention, user_id=user_id
    )
    clear_user_data(user_id)

# --- मर्ज के लिए फाइल हैंडलर (कोई बदलाव नहीं) ---
USED_COMMANDS = ["start", "help", "cancel", "merge", "encode", "notg_thumbnail"] # 'encode' जोड़ा गया
@app.on_message(filters.video | (filters.text & ~filters.command(USED_COMMANDS)) & filters.private)
async def file_handler(_, message: Message):
    if not message.from_user: return
    user_id = message.from_user.id
    if user_data.get(user_id, {}).get("state"):
        await message.reply_text("I am waiting for you to complete the current process. Please follow the instructions or use /cancel to start over.")
        return
    
    if user_id not in user_data:
        user_data[user_id] = {"queue": []}
    
    item = message if message.video else message.text
    item_type = "Video" if message.video else "Link"

    if item_type == "Link" and not is_valid_url(item):
        await message.reply_text("⚠️ This doesn't look like a valid direct download link.", quote=True)
        return

    user_data[user_id].setdefault("queue", []).append(item)
    await message.reply_text(f"✅ **{item_type} added to merge queue!**\n➢ **Queue:** `{len(user_data[user_id]['queue'])}` items.")

# --- मर्ज हैंडलर (कोई बदलाव नहीं) ---
@app.on_message(filters.command("merge") & filters.private)
async def merge_handler(client, message: Message):
    if not message.from_user: return
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    if user_id not in user_data or not user_data[user_id].get("queue"):
        await message.reply_text("Your merge queue is empty.", quote=True)
        return
    if len(user_data[user_id]["queue"]) < 2:
        await message.reply_text("You need at least two items in the queue to merge.", quote=True)
        return
    status_msg = await message.reply_text("🚀 **Starting Merge Process...**", quote=True)
    user_data[user_id]["status_message"] = status_msg
    video_paths = []
    queue = user_data[user_id]["queue"]
    for i, item in enumerate(queue):
        file_path = (await download_from_url(item, user_id, status_msg, user_mention)
                     if isinstance(item, str)
                     else await download_from_tg(item, user_id, status_msg, user_mention))
        if not file_path:
            clear_user_data(user_id)
            return
        video_paths.append(file_path)
    merged_path = await merge_videos(video_paths, user_id, status_msg, user_mention)
    if not merged_path:
        clear_user_data(user_id)
        return
    user_data[user_id]["merged_file"] = merged_path
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Upload to Telegram", callback_data="upload_tg")],
        [InlineKeyboardButton("🔗 Upload to GoFile.io", callback_data="upload_gofile")]
    ])
    await status_msg.edit_text("✅ **Merge Successful!**\n\nChoose where you want to upload the file:", reply_markup=keyboard)

# =================================================================
# === NAYA ENCODING FEATURE KA CODE ===
# =================================================================

ENCODE_PRESETS = {
    "encode_1080p_h264": "1080p_h264", "encode_1080p_h265": "1080p_h265",
    "encode_720p_h264": "720p_h264",   "encode_720p_h265": "720p_h265",
    "encode_480p_h264": "480p_h264",   "encode_480p_h265": "480p_h265",
    "encode_watermark": "watermark"
}

@app.on_message(filters.command("encode") & filters.private)
async def encode_command_handler(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a video or a direct download link with the `/encode` command.", quote=True)
        return

    target_message = message.reply_to_message
    is_video = hasattr(target_message, 'video') and target_message.video
    is_link = hasattr(target_message, 'text') and target_message.text and is_valid_url(target_message.text)

    if not (is_video or is_link):
        await message.reply_text("This command only works when replying to a video or a valid direct download link.", quote=True)
        return

    user_id = message.from_user.id
    clear_user_data(user_id) # पिछला कोई काम चल रहा हो तो उसे साफ़ करें
    user_data[user_id] = {"encode_target_msg_id": target_message.id}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1080p H.264", callback_data="encode_1080p_h264"), InlineKeyboardButton("1080p H.265", callback_data="encode_1080p_h265")],
        [InlineKeyboardButton("720p H.264", callback_data="encode_720p_h264"), InlineKeyboardButton("720p H.265", callback_data="encode_720p_h265")],
        [InlineKeyboardButton("480p H.264", callback_data="encode_480p_h264"), InlineKeyboardButton("480p H.265", callback_data="encode_480p_h265")],
        [InlineKeyboardButton("💧 Add Watermark", callback_data="encode_watermark")],
        [InlineKeyboardButton("✖️ Close", callback_data="encode_close")]
    ])
    await message.reply_text("Please choose an encoding option:", reply_markup=keyboard, quote=True)

# --- संशोधित CALLBACK HANDLER ---
# यह हैंडलर अब मर्ज और एन्कोड दोनों को संभालेगा
@app.on_callback_query()
async def universal_callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    # --- ENCODING FLOW ---
    if data.startswith("encode_"):
        await handle_encode_callback(client, query)
    
    # --- UPLOAD ENCODED FILE FLOW ---
    elif data.startswith("upload_") and data.endswith("_encoded"):
        await handle_encoded_upload_callback(client, query)

    # --- MERGE FLOW ---
    elif data in ["upload_tg", "upload_gofile"]:
        await handle_merge_upload_callback(client, query)

async def handle_encode_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if data == "encode_close":
        if user_id in user_data: user_data.pop(user_id, None)
        await query.message.delete()
        return

    if user_id not in user_data or "encode_target_msg_id" not in user_data[user_id]:
        await query.answer("Sorry, this is an old request. Please start over.", show_alert=True)
        await query.message.delete()
        return

    try:
        target_message = await client.get_messages(chat_id=query.message.chat.id, message_ids=user_data[user_id]["encode_target_msg_id"])
    except Exception:
        await query.answer("Could not find the original video. It might have been deleted.", show_alert=True)
        return
    
    await query.message.edit_text("🚀 **Starting Encoding Process...**")
    user_data[user_id]["status_message"] = query.message
    
    preset = ENCODE_PRESETS.get(data)
    if not preset: return await query.message.edit_text("❌ Invalid option.")
    
    encoded_path = await process_video_encoding(
        target_message=target_message, user_id=user_id, status_message=query.message,
        user_mention=query.from_user.mention, preset=preset
    )

    if not encoded_path:
        clear_user_data(user_id)
        return

    user_data[user_id]["encoded_file"] = encoded_path
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Upload to Telegram", callback_data="upload_tg_encoded")],
        [InlineKeyboardButton("🔗 Upload to GoFile.io", callback_data="upload_gofile_encoded")]
    ])
    await query.message.edit_text("✅ **Encoding Successful!**\n\nChoose where you want to upload the file:", reply_markup=keyboard)

async def handle_encoded_upload_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if user_id not in user_data or "encoded_file" not in user_data[user_id]:
        return await query.answer("Sorry, your session has expired.", show_alert=True)
    
    await query.message.edit_reply_markup(None)
    user_data[user_id]["status_message"] = query.message
    
    file_to_upload = user_data[user_id]["encoded_file"]
    # uploader logic ke liye 'merged_file' key set karna zaroori hai
    user_data[user_id]["merged_file"] = file_to_upload

    if data == "upload_tg_encoded":
        user_data[user_id]["state"] = "waiting_for_thumbnail"
        await query.message.edit_text("Okay, preparing for Telegram upload.\n\nPlease send the thumbnail or /notg_thumbnail to use a default one.")
    elif data == "upload_gofile_encoded":
        await query.message.edit_text("🚀 Preparing to upload to GoFile.io...")
        try:
            uploader = GofileUploader()
            link = await uploader.upload_file(file_to_upload)
            await query.message.edit_text(f"✅ **Upload to GoFile Complete!**\n\n🔗 **Your Link:** {link}")
        except Exception as e:
            await query.message.edit_text(f"❌ **GoFile Upload Failed!**\nError: `{e}`")
        finally:
            clear_user_data(user_id)

async def handle_merge_upload_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if user_id not in user_data or not user_data[user_id].get("merged_file"):
        return await query.answer("Sorry, your session has expired or been cancelled.", show_alert=True)

    await query.message.edit_reply_markup(None)
    user_data[user_id]["status_message"] = query.message
    
    if data == "upload_tg":
        user_data[user_id]["state"] = "waiting_for_thumbnail"
        await query.message.edit_text("Okay, preparing for Telegram upload.\n\nPlease send the thumbnail or /notg_thumbnail to use a default one.")
    
    elif data == "upload_gofile":
        await query.message.edit_text("🚀 Preparing to upload to GoFile.io...")
        try:
            uploader = GofileUploader()
            link = await uploader.upload_file(user_data[user_id]["merged_file"])
            await query.message.edit_text(f"✅ **Upload to GoFile Complete!**\n\n🔗 **Your Link:** {link}")
        except Exception as e:
            await query.message.edit_text(f"❌ **GoFile Upload Failed!**\nError: `{e}`")
        finally:
            clear_user_data(user_id)

if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
