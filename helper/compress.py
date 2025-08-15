# helper/compress.py

import logging
import asyncio
import os
import time
import re
import math
from utils import generate_progress_string

LOGGER = logging.getLogger(__name__)

async def convert_video(video_file, output_directory, status_message, user_mention, user_id, quality: str):
    """वीडियो को चयनित गुणवत्ता के आधार पर कंप्रेस करता है।"""
    out_put_file_name = os.path.join(output_directory, f"compressed_{quality}_{int(time.time())}.mkv")
    progress_file = os.path.join(output_directory, "progress.txt")
    
    try:
        process = await asyncio.create_subprocess_exec(
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', video_file,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            LOGGER.error(f"FFprobe failed: {stderr.decode().strip()}")
            return None
        total_time = float(stdout.decode().strip())
    except Exception:
        await status_message.edit_text("❌ **Error:** Could not get video duration.")
        return None

    # --- गुणवत्ता के आधार पर FFmpeg पैरामीटर सेट करें ---
    quality_presets = {
        # H.264 Presets (व्यापक संगतता)
        "1080p": {"codec": "libx264", "crf": "22", "scale": "scale=-2:1080", "preset": "veryfast"},
        "720p":  {"codec": "libx264", "crf": "23", "scale": "scale=-2:720", "preset": "veryfast"},
        "480p":  {"codec": "libx264", "crf": "24", "scale": "scale=-2:480", "preset": "veryfast"},
        # H.265/HEVC Presets (बेहतर कंप्रेशन, छोटी फाइलें)
        "720p_hevc": {"codec": "libx265", "crf": "26", "tag": "hvc1", "scale": "scale=-2:720", "preset": "medium"},
        "480p_hevc": {"codec": "libx265", "crf": "28", "tag": "hvc1", "scale": "scale=-2:480", "preset": "medium"},
    }
    
    params = quality_presets.get(quality)
    if not params:
        await status_message.edit_text("❌ Invalid quality selected.")
        return None

    with open(progress_file, 'w') as f: pass

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-progress", progress_file, "-i", video_file,
        "-c:v", params["codec"],
        "-preset", params["preset"],
        "-crf", params["crf"],
        "-vf", params["scale"],
        "-c:a", "copy",  # ऑडियो को बिना री-एनकोड किए कॉपी करें
        "-y", out_put_file_name
    ]
    # HEVC के लिए वीडियो टैग जोड़ें (स्ट्रीमिंग संगतता के लिए)
    if "tag" in params:
        command.extend(["-tag:v", params["tag"]])

    start_time = time.time()
    process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    
    last_edit_time = 0
    while process.returncode is None:
        await asyncio.sleep(2)
        if time.time() - last_edit_time < 5: continue
        
        if not os.path.exists(progress_file): continue
        
        with open(progress_file, 'r') as file:
            text = file.read()
            time_in_us = re.findall(r"out_time_ms=(\d+)", text)
            speed = re.findall(r"speed=(\d+\.?\d*)x", text)
            progress_status = re.findall(r"progress=(\w+)", text)

            if progress_status and progress_status[-1] == "end": break
            if not all([time_in_us, speed]): continue

            elapsed_time = int(time_in_us[-1]) / 1000000
            current_speed = float(speed[-1])
            
            percentage = min(elapsed_time * 100 / total_time, 100) if total_time > 0 else 0
            eta = (total_time - elapsed_time) / current_speed if current_speed > 0 else 0
            
            progress_text = generate_progress_string(
                title=os.path.basename(out_put_file_name), status=f"Compressing ({quality})",
                progress=percentage / 100, processed_bytes=int(elapsed_time),
                total_bytes=int(total_time), speed=0, # बाइट्स में नहीं है
                eta=eta, start_time=start_time, user_mention=user_mention, user_id=user_id
            )
            try:
                await status_message.edit_text(progress_text)
                last_edit_time = time.time()
            except Exception: pass

    _, stderr = await process.communicate()
    if process.returncode != 0:
        error_message = stderr.decode().strip()
        LOGGER.error(f"FFmpeg Error: {error_message}")
        await status_message.edit_text(f"❌ **Compression Failed!**\n`{error_message}`")
        return None
    
    return out_put_file_name if os.path.exists(out_put_file_name) else None
