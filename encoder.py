# encoder.py (वीडियो एन्कोडिंग और वॉटरमार्किंग के लिए नई फ़ाइल)
import os
import time
import asyncio
from config import config
from utils import generate_progress_string, get_video_properties, cleanup_files
from downloader import download_from_tg, download_from_url

# --- FFmpeg एन्कोडिंग लॉजिक ---

async def process_video_encoding(
    target_message, 
    user_id: int, 
    status_message, 
    user_mention: str, 
    preset: str
) -> str | None:
    """
    वीडियो को डाउनलोड करता है, दिए गए प्रीसेट के अनुसार एन्कोड/वॉटरमार्क करता है, 
    और आउटपुट फ़ाइल का पाथ लौटाता है।
    """
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)

    # --- चरण 1: वीडियो डाउनलोड करें ---
    downloaded_file_path = None
    if hasattr(target_message, 'video') and target_message.video:
        downloaded_file_path = await download_from_tg(target_message, user_id, status_message, user_mention)
    elif hasattr(target_message, 'text') and target_message.text:
        downloaded_file_path = await download_from_url(target_message.text, user_id, status_message, user_mention)

    if not downloaded_file_path:
        await status_message.edit_text("❌ **Download Failed!**\nCould not download the video.")
        return None

    # --- चरण 2: एन्कोडिंग के लिए FFmpeg कमांड चलाएँ ---
    try:
        encoded_file_path = await _run_ffmpeg_encode_process(
            input_path=downloaded_file_path,
            user_id=user_id,
            status_message=status_message,
            user_mention=user_mention,
            preset=preset
        )
        return encoded_file_path
    finally:
        # मूल डाउनलोड की गई फ़ाइल को साफ़ करें
        cleanup_files(downloaded_file_path)


async def _run_ffmpeg_encode_process(
    input_path: str, 
    user_id: int, 
    status_message, 
    user_mention: str, 
    preset: str
) -> str | None:
    """FFmpeg कमांड बनाता है, चलाता है, और प्रोग्रेस दिखाता है।"""
    
    properties = await get_video_properties(input_path)
    if not properties or not properties.get("duration"):
        await status_message.edit_text("❌ **Encoding Failed!**\nCould not read video metadata.")
        return None
    total_duration = int(properties["duration"])
    if total_duration <= 0:
        await status_message.edit_text("❌ **Encoding Failed!**\nVideo duration is zero or invalid.")
        return None

    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    output_path = os.path.join(user_download_dir, f"encoded_{preset}_{int(time.time())}.mkv")
    
    # --- प्रीसेट के आधार पर FFmpeg कमांड बनाएँ ---
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', input_path]
    
    # एन्कोडिंग पैरामीटर्स
    video_filters = []
    if preset == '1080p_h264':
        video_filters.append("scale='min(1920,iw)':min'(1080,ih)':force_original_aspect_ratio=decrease")
        command.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '22'])
    elif preset == '1080p_h265':
        video_filters.append("scale='min(1920,iw)':min'(1080,ih)':force_original_aspect_ratio=decrease")
        command.extend(['-c:v', 'libx265', '-preset', 'fast', '-crf', '26'])
    elif preset == '720p_h264':
        video_filters.append("scale='min(1280,iw)':min'(720,ih)':force_original_aspect_ratio=decrease")
        command.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '23'])
    elif preset == '720p_h265':
        video_filters.append("scale='min(1280,iw)':min'(720,ih)':force_original_aspect_ratio=decrease")
        command.extend(['-c:v', 'libx265', '-preset', 'fast', '-crf', '28'])
    elif preset == '480p_h264':
        video_filters.append("scale='min(854,iw)':min'(480,ih)':force_original_aspect_ratio=decrease")
        command.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '24'])
    elif preset == '480p_h265':
        video_filters.append("scale='min(854,iw)':min'(480,ih)':force_original_aspect_ratio=decrease")
        command.extend(['-c:v', 'libx265', '-preset', 'fast', '-crf', '30'])
    elif preset == 'watermark':
        if not os.path.exists('watermark.png'):
            await status_message.edit_text("❌ **Watermark Failed!**\n`watermark.png` not found in the bot's directory.")
            return None
        video_filters.append("overlay=W-w-10:H-h-10") # वॉटरमार्क नीचे-दाएं कोने में
        command.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '23']) # डिफ़ॉल्ट एन्कोडर
    
    if video_filters:
        command.extend(['-vf', ",".join(video_filters)])

    command.extend(['-c:a', 'aac', '-b:a', '128k', '-y', '-progress', 'pipe:1', output_path])

    # --- FFmpeg प्रोसेस चलाएँ और प्रोग्रेस दिखाएँ ---
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    start_time = time.time()
    last_update_time = 0
    
    while process.returncode is None:
        line_bytes = await process.stdout.readline()
        if not line_bytes:
            await asyncio.sleep(0.1)
            continue
        
        line = line_bytes.decode('utf-8', errors='ignore').strip()
        
        if 'out_time_ms=' in line:
            current_time = time.time()
            if current_time - last_update_time < 3: continue
            
            processed_us = int(line.split('=')[1])
            processed_seconds = processed_us // 1000000
            
            if processed_seconds > 0 and total_duration > 0:
                progress = processed_seconds / total_duration
                elapsed_time = current_time - start_time
                speed_factor = processed_seconds / elapsed_time if elapsed_time > 0 else 0
                eta = (total_duration - processed_seconds) / speed_factor if speed_factor > 0 else 0
                
                try:
                    progress_text = generate_progress_string(
                        title=f"Encoding ({preset})...", status="Encoding",
                        progress=progress, processed_bytes=processed_seconds,
                        total_bytes=total_duration, speed=0, eta=int(eta),
                        start_time=start_time, user_mention=user_mention, user_id=user_id
                    )
                    await status_message.edit_text(progress_text)
                    last_update_time = current_time
                except Exception as e:
                    print(f"Progress update error: {e}")
                    break 

    await process.wait()

    if process.returncode != 0:
        stderr_output = (await process.stderr.read()).decode('utf-8', errors='ignore').strip()
        await status_message.edit_text(f"❌ **Encoding Failed!**\n\n**Error:**\n`{stderr_output[-500:]}`")
        cleanup_files(output_path)
        return None
    
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        await status_message.edit_text("❌ **Encoding Failed!**\nOutput file not found or is empty.")
        return None
        
    return output_path
