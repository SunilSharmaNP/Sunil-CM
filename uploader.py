# merger.py (Final version with new attractive progress template and error fix)
import asyncio
import os
import time
from typing import List
from config import config
# Import the new template generator and other utils
from utils import get_video_properties, generate_progress_string

# --- Throttling Logic (Unchanged) ---
last_edit_time = {}
EDIT_THROTTLE_SECONDS = 4.0

async def smart_progress_editor(status_message, text: str):
    """A throttled editor to prevent FloodWait errors."""
    if not status_message or not hasattr(status_message, 'chat'): return
    message_key = f"{status_message.chat.id}_{status_message.id}"
    now = time.time()
    last_time = last_edit_time.get(message_key, 0)
    if (now - last_time) > EDIT_THROTTLE_SECONDS:
        try:
            await status_message.edit_text(text)
            last_edit_time[message_key] = now
        except Exception:
            pass

# --- MODIFIED: To accept and pass user_mention and fix the SyntaxError ---
async def merge_videos(video_files: List[str], user_id: int, status_message, user_mention: str) -> str | None:
    """Asynchronously tries a fast merge, then falls back to a robust merge."""
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    output_path = os.path.join(user_download_dir, f"merged_{int(time.time())}.mkv")
    inputs_file = os.path.join(user_download_dir, "inputs.txt")

    try:
        with open(inputs_file, 'w', encoding='utf-8') as f:
            for file in video_files:
                abs_path = os.path.abspath(file)
                # FIX: The following line caused the SyntaxError.
                # f.write(f"file '{abs_path.replace("'", "'\\''")}'\n")
                # The fix is to do the replacement outside of the f-string.
                escaped_path = abs_path.replace("'", r"'\''")
                f.write(f"file '{escaped_path}'\n")
    except Exception as e:
        await status_message.edit_text(f"❌ **Merge Failed!**\nError creating inputs file: `{e}`")
        if os.path.exists(inputs_file):
            os.remove(inputs_file)
        return None
    
    # Fast merge is almost instant, so no progress bar is needed here.
    await status_message.edit_text("🚀 **Starting Merge (Fast Mode)...**")
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', inputs_file, '-c', 'copy', '-y', output_path]
    process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
    _, stderr = await process.communicate()

    if process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        os.remove(inputs_file)
        return output_path
    else:
        # If fast merge fails, switch to robust mode, passing user_mention along
        await status_message.edit_text("⚠️ Fast merge failed. Switching to Robust Mode...")
        os.remove(inputs_file)
        if os.path.exists(output_path): # Clean up failed fast merge attempt
            os.remove(output_path)
        return await _merge_videos_filter(video_files, user_id, status_message, user_mention)

# --- MODIFIED: To use the new progress template ---
async def _merge_videos_filter(video_files: List[str], user_id: int, status_message, user_mention: str) -> str | None:
    """Fallback async merge function using the robust but slower 'concat' filter."""
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    output_path = os.path.join(user_download_dir, f"merged_fallback_{int(time.time())}.mkv")
    
    tasks = [get_video_properties(f) for f in video_files]
    all_properties = await asyncio.gather(*tasks)
    
    valid_properties = [p for p in all_properties if p and p.get('duration') is not None]
    if len(valid_properties) != len(video_files):
        await status_message.edit_text("❌ **Merge Failed!** Could not read metadata from all files."); return None
        
    total_duration = sum(p['duration'] for p in valid_properties)
    if total_duration == 0:
        await status_message.edit_text("❌ **Merge Failed!** Total video duration is zero."); return None
        
    input_args = []; filter_complex = []
    for i, file in enumerate(video_files):
        input_args.extend(['-i', file]); filter_complex.append(f"[{i}:v:0][{i}:a:0]")
    
    filter_complex_str = "".join(filter_complex) + f"concat=n={len(video_files)}:v=1:a=1[v][a]"
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', *input_args, '-filter_complex', filter_complex_str, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-y', '-progress', 'pipe:1', output_path]
    
    process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    start_time = time.time()
    
    while process.returncode is None:
        line_bytes = await process.stdout.readline()
        if not line_bytes:
            # If stdout pipe is closed, wait for the process to finish
            await asyncio.sleep(0.1)
            continue
            
        line = line_bytes.decode('utf-8').strip()
        
        if 'out_time_ms' in line:
            parts = line.split('=')
            if len(parts) > 1 and parts[1].strip().isdigit():
                current_time_ms = int(parts[1])
                current_time_s = max(0, current_time_ms / 1000000) # Ensure it's not negative
                progress = min(1.0, current_time_s / total_duration) if total_duration > 0 else 0
                
                elapsed = time.time() - start_time
                speed_factor = current_time_s / elapsed if elapsed > 0 else 0
                eta = (total_duration - current_time_s) / speed_factor if speed_factor > 0 else 0
                
                # Call the new template generator
                progress_text = generate_progress_string(
                    title=f"Merging {len(video_files)} files...",
                    status="Merging (Robust)",
                    progress=progress,
                    processed_bytes=int(current_time_s), # For merging, this is seconds processed
                    total_bytes=int(total_duration),     # For merging, this is total seconds
                    speed=0, # Speed not applicable for merging time-based progress
                    eta=int(eta),
                    start_time=start_time,
                    user_mention=user_mention,
                    user_id=user_id
                )
                await smart_progress_editor(status_message, progress_text)
    
    await process.wait()
    
    if process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return output_path
    else:
        error_output_bytes = await process.stderr.read()
        error_output = error_output_bytes.decode('utf-8', errors='ignore').strip()
        print(f"Robust merge failed. FFmpeg stderr: {error_output}")
        await status_message.edit_text(f"❌ **Merge Failed!**\nRobust method also failed.\n\n`{error_output[-500:]}`"); return None
