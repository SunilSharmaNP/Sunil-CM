# utils.py

import time
import math
import asyncio
import json
import os
import re
import shutil

def get_human_readable_size(size_in_bytes: int) -> str:
    if size_in_bytes is None: return "0B"
    power = 1024; n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size_in_bytes > power and n < len(power_labels) - 1:
        size_in_bytes /= power; n += 1
    return f"{size_in_bytes:.2f} {power_labels[n]}B"

def get_progress_bar(progress: float, length: int = 12) -> str:
    filled_len = int(length * progress)
    return '█' * filled_len + '░' * (length - filled_len)

def get_time_formatted(seconds: float) -> str:
    if seconds is None: return "N/A"
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0: return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0: return f"{minutes}m {seconds}s"
    return f"{seconds}s"

def generate_progress_string(
    title: str,
    status: str,
    progress: float,
    processed_bytes: int,
    total_bytes: int,
    speed: float,
    eta: int,
    start_time: float,
    user_mention: str,
    user_id: int
) -> str:
    elapsed_time = get_time_formatted(time.time() - start_time)
    
    if status.startswith("Merging"):
        processed_str = get_time_formatted(processed_bytes)
        total_str = get_time_formatted(total_bytes)
        speed_str = ""
    else:
        processed_str = get_human_readable_size(processed_bytes)
        total_str = get_human_readable_size(total_bytes)
        speed_str = f"{get_human_readable_size(speed)}/s"

    return (
        f"**🎥 𝐓ɪᴛᴛʟᴇ :** `{title}`\n\n"
        f"┏━━༻« ★彡 𝐒𝐒 𝐁ᴏᴛs 彡★ »༺━━┓\n"
        f"┠ [{get_progress_bar(progress)}] {progress:.1%}\n"
        f"┠⚡**𝐏ʀᴏᴄᴇssᴇᴅ :** {processed_str} of {total_str}\n"
        f"┠ 🪄 **𝐒ᴛᴀᴛᴜs :** {status}\n"
        f"┠⏳ **𝐄ᴛᴀ :** {get_time_formatted(eta)}\n"
        f"┠☘️ **𝐒ᴘᴇᴇᴅ :** {speed_str}\n"
        f"┠ 🕓 **𝐄ʟᴀᴘsᴇᴅ :** {elapsed_time}\n"
        f"┠ 🪩 **𝐄ɴɢɪɴᴇ :** SS Merger v1.0\n"
        f"┠ 🌐 **𝐌ᴏᴅᴇ :** #MergeBot\n"
        f"┠ 👤 **𝐔sᴇʀ :** {user_mention}\n"
        f"┠ 🆔 **𝐈𝐃 :** `{user_id}`\n"
        f"┗━━༻« ★彡 𝐒𝐒 𝐁ᴏᴛs 彡★ »༺━━┛"
    )

async def get_video_properties(video_path: str) -> dict | None:
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return None
    command = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", video_path]
    process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        print(f"Error getting video properties for '{video_path}': {stderr.decode().strip()}")
        return None
    try:
        data = json.loads(stdout)
        video_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
        if not video_stream:
            print(f"No video stream found in '{video_path}'"); return None
        duration_str = video_stream.get("duration", data.get("format", {}).get("duration", "0"))
        return {"duration": int(float(duration_str)), "width": int(video_stream.get("width", 0)), "height": int(video_stream.get("height", 0))}
    except (json.JSONDecodeError, KeyError, StopIteration, ValueError) as e:
        print(f"Failed to parse ffprobe output for '{video_path}': {e}"); return None

def cleanup_files(*files_or_dirs):
    for item in files_or_dirs:
        try:
            if os.path.isdir(item): shutil.rmtree(item)
            elif os.path.isfile(item): os.remove(item)
        except OSError as e:
            print(f"Error cleaning up {item}: {e}")

def is_valid_url(url: str) -> bool:
    return re.match(r'^https?:\/\/.+$', url) is not None

def TimeFormatter(milliseconds: float) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2] if tmp else "0s"
