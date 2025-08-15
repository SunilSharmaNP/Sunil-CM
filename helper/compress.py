# helper/compress.py

import logging
import asyncio
import os
import time
import re
import math
import json

from utils import TimeFormatter  # हम यह फंक्शन utils.py में डालेंगे

LOGGER = logging.getLogger(__name__)

# इन वेरिएबल्स को आपके utils.py से लिया जा सकता है
FINISHED_PROGRESS_STR = "█"
UN_FINISHED_PROGRESS_STR = "░"

async def convert_video(video_file, output_directory, message, status_message):
    """वीडियो को कंप्रेस करने वाला मुख्य फंक्शन।"""
    out_put_file_name = os.path.join(output_directory, f"compressed_{int(time.time())}.mkv")
    progress_file = os.path.join(output_directory, "progress.txt")
    
    # वीडियो की अवधि (duration) निकालें
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
    except (FileNotFoundError, ValueError):
        await status_message.edit_text("❌ **Error:** `ffprobe` not found or invalid video duration.")
        return None

    # --- महत्वपूर्ण: एन्कोडर चुनें ---
    # विकल्प 1: NVIDIA GPU के लिए (बहुत तेज़)
    encoder = "h264_nvenc"
    preset = "fast"
    
    # विकल्प 2: केवल CPU के लिए (अगर GPU नहीं है)
    # encoder = "libx264"
    # preset = "ultrafast"
    # ------------------------------------

    with open(progress_file, 'w') as f:
        pass  # Progress file को खाली करें

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-progress", progress_file, "-i", video_file,
        "-c:v", encoder, "-preset", preset,
        "-crf", "24",  # क्वालिटी के लिए CRF का उपयोग करें
        "-c:a", "copy", "-y", out_put_file_name
    ]

    COMPRESSION_START_TIME = time.time()
    process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    
    while process.returncode is None:
        await asyncio.sleep(4) # FloodWait से बचने के लिए अंतराल बढ़ाएँ
        if not os.path.exists(progress_file):
            continue
        
        with open(progress_file, 'r') as file:
            text = file.read()
            time_in_us = re.findall(r"out_time_ms=(\d+)", text)
            speed = re.findall(r"speed=(\d+\.?\d*)x", text)
            progress_status = re.findall(r"progress=(\w+)", text)

            if progress_status and progress_status[-1] == "end":
                break

            if not all([time_in_us, speed]):
                continue

            elapsed_time = int(time_in_us[-1]) / 1000000
            current_speed = float(speed[-1])
            
            percentage = math.floor(elapsed_time * 100 / total_time)
            if percentage > 100: percentage = 100

            eta = "-"
            if current_speed > 0:
                time_left = (total_time - elapsed_time) / current_speed
                eta = TimeFormatter(time_left * 1000)

            progress_bar = "".join([FINISHED_PROGRESS_STR for _ in range(math.floor(percentage / 10))])
            progress_bar += "".join([UN_FINISHED_PROGRESS_STR for _ in range(10 - math.floor(percentage / 10))])

            stats = (f'🔄 **Compressing Video...**\n'
                     f'➢ `{progress_bar}` `{percentage}%`\n'
                     f'➢ **Speed:** `{current_speed:.2f}x`\n'
                     f'➢ **ETA:** `{eta}`')
            try:
                await status_message.edit_text(stats)
            except Exception:
                pass # FloodWait या MessageNotModified को अनदेखा करें

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        LOGGER.error(f"FFmpeg Error: {stderr.decode().strip()}")
        await status_message.edit_text(f"❌ **Compression Failed!**\n`{stderr.decode().strip()}`")
        return None
    
    if os.path.exists(out_put_file_name):
        return out_put_file_name
    return None
