# merger.py (Corrected for absolute paths and robust progress parsing)
import asyncio
import os
import time
from typing import List
from config import config
from utils import get_video_properties, get_progress_bar, get_time_left

# --- Throttling Logic for Progress Bar (Unchanged) ---
last_edit_time = {}
EDIT_THROTTLE_SECONDS = 4.0

async def smart_progress_editor(status_message, text: str):
    """A throttled editor to prevent FloodWait errors during progress updates."""
    # A check to ensure status_message is not None
    if not status_message or not hasattr(status_message, 'chat'):
        return
        
    message_key = f"{status_message.chat.id}_{status_message.id}"
    now = time.time()
    last_time = last_edit_time.get(message_key, 0)
    if (now - last_time) > EDIT_THROTTLE_SECONDS:
        try:
            await status_message.edit_text(text)
            last_edit_time[message_key] = now
        except Exception:
            pass

async def merge_videos(video_files: List[str], user_id: int, status_message) -> str | None:
    """
    Asynchronously tries a fast merge, then falls back to a robust merge.
    """
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    output_path = os.path.join(user_download_dir, f"merged_{int(time.time())}.mkv")
    inputs_file = os.path.join(user_download_dir, "inputs.txt")

    # --- FIX 1: Use absolute paths in the inputs file ---
    # This ensures FFmpeg can always find the files, resolving the "No such file" error.
    with open(inputs_file, 'w', encoding='utf-8') as f:
        for file in video_files:
            abs_path = os.path.abspath(file) # Convert to absolute path
            formatted_path = abs_path.replace("'", "'\\''")
            f.write(f"file '{formatted_path}'\n")

    await status_message.edit_text("🚀 **Starting Merge (Fast Mode)...**\nThis should be quick if videos are compatible.")
    
    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', 
        '-f', 'concat', '-safe', '0', '-i', inputs_file,
        '-c', 'copy', '-y', output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        await status_message.edit_text("✅ **Merge Complete! (Fast Mode)**")
        os.remove(inputs_file)
        return output_path
    else:
        error_log = stderr.decode().strip()
        print(f"Fast merge failed. FFmpeg stderr: {error_log}")
        await status_message.edit_text(
            "⚠️ Fast merge failed. Videos might have different formats.\n"
            "🔄 **Switching to Robust Mode...** This will re-encode videos and may take longer."
        )
        await asyncio.sleep(2)
        os.remove(inputs_file)
        return await _merge_videos_filter(video_files, user_id, status_message)


async def _merge_videos_filter(video_files: List[str], user_id: int, status_message) -> str | None:
    """Fallback async merge function using the robust but slower 'concat' filter."""
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    output_path = os.path.join(user_download_dir, f"merged_fallback_{int(time.time())}.mkv")
    
    tasks = [get_video_properties(f) for f in video_files]
    all_properties = await asyncio.gather(*tasks)
    
    valid_properties = [p for p in all_properties if p and p.get('duration') is not None]
    if len(valid_properties) != len(video_files):
        await status_message.edit_text("❌ **Merge Failed!** Could not read metadata from one or more videos.")
        return None
        
    total_duration = sum(p['duration'] for p in valid_properties)
    if total_duration == 0:
        await status_message.edit_text("❌ **Merge Failed!** Total video duration is zero.")
        return None
        
    input_args = []
    filter_complex = []
    for i, file in enumerate(video_files):
        input_args.extend(['-i', file])
        filter_complex.append(f"[{i}:v:0][{i}:a:0]")
    
    filter_complex_str = "".join(filter_complex) + f"concat=n={len(video_files)}:v=1:a=1[v][a]"
    
    command = [
        'ffmpeg', '-hide_banner', *input_args, '-filter_complex', filter_complex_str,
        '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '23', '-c:a', 'aac', '-b:a', '192k', '-y',
        '-progress', 'pipe:1', output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    
    start_time = time.time()
    
    while process.returncode is None:
        line_bytes = await process.stdout.readline()
        if not line_bytes:
            break
        line = line_bytes.decode('utf-8').strip()
        
        # --- FIX 2: Handle "N/A" from FFmpeg progress to prevent ValueError ---
        if 'out_time_ms' in line:
            parts = line.split('=')
            # Check if the value is a valid number before trying to convert it
            if len(parts) > 1 and parts[1].strip().isdigit():
                current_time_ms = int(parts[1])
                # Ensure total_duration is not zero to avoid division by zero
                if total_duration > 0:
                    progress_percent = max(0, min(1, (current_time_ms / 1000000) / total_duration))
                    elapsed_time = time.time() - start_time
                    
                    progress_text = (
                        f"⚙️ **Merging Videos (Robust Mode)...**\n"
                        f"➢ {get_progress_bar(progress_percent)} `{progress_percent:.1%}`\n"
                        f"➢ **Time Left:** `{get_time_left(elapsed_time, progress_percent)}`"
                    )
                    await smart_progress_editor(status_message, progress_text)
    
    await process.wait()
    
    if process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        await status_message.edit_text("✅ **Merge Complete! (Robust Mode)**")
        return output_path
    else:
        stderr = await process.stderr.read()
        error_output = stderr.decode().strip()
        print(f"Robust merge failed. FFmpeg stderr: {error_output}")
        await status_message.edit_text(f"❌ **Merge Failed!**\nRobust method also failed. See logs for details.")
        return None```
