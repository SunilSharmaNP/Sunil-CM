# merger.py
import subprocess
import os
import time
from typing import List
from config import config
from utils import get_video_metadata, get_progress_bar, get_time_left

async def merge_videos(video_files: List[str], user_id: int, status_message) -> str | None:
    """
    Tries to merge videos using the fast '-c copy' method first.
    If it fails, it falls back to the slower but more robust filter method.
    """
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    output_path = os.path.join(user_download_dir, f"merged_{int(time.time())}.mkv")
    inputs_file = os.path.join(user_download_dir, "inputs.txt")

    with open(inputs_file, 'w') as f:
        for file in video_files:
            f.write(f"file '{os.path.abspath(file)}'\n")

    await status_message.edit_text("🚀 **Starting Merge (Fast Mode)...**\nThis should be quick if videos are compatible.")
    
    # --- Stage 1: Fast Merge Attempt (-c copy) ---
    command = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', inputs_file,
        '-c', 'copy', '-y', output_path
    ]
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()

    if process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        await status_message.edit_text("✅ **Merge Complete!**")
        os.remove(inputs_file)
        return output_path
    else:
        await status_message.edit_text(
            "⚠️ Fast merge failed. Videos might have different formats.\n"
            "🔄 **Switching to Robust Mode...** This will re-encode videos and may take longer."
        )
        time.sleep(2)
        print(f"Fast merge failed. FFmpeg stderr: {stderr}")
        # --- Stage 2: Fallback to Robust Merge (re-encoding) ---
        return await _merge_videos_filter(video_files, user_id, status_message)


async def _merge_videos_filter(video_files: List[str], user_id: int, status_message) -> str | None:
    """Fallback merge function using the robust but slower 'concat' filter."""
    user_download_dir = os.path.join(config.DOWNLOAD_DIR, str(user_id))
    output_path = os.path.join(user_download_dir, f"merged_fallback_{int(time.time())}.mkv")
    
    total_duration = sum(get_video_metadata(f)['duration'] for f in video_files)
    if total_duration == 0:
        await status_message.edit_text("❌ **Merge Failed!** Could not get video durations for robust mode.")
        return None
        
    input_args = []
    filter_complex = []
    for i, file in enumerate(video_files):
        input_args.extend(['-i', file])
        filter_complex.append(f"[{i}:v:0][{i}:a:0]")
    
    filter_complex_str = "".join(filter_complex) + f"concat=n={len(video_files)}:v=1:a=1[v][a]"
    
    command = [
        'ffmpeg', *input_args, '-filter_complex', filter_complex_str,
        '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '23', '-c:a', 'aac', '-b:a', '192k', '-y',
        '-progress', 'pipe:1', output_path
    ]
    
    start_time = time.time()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
    for line in iter(process.stdout.readline, ''):
        if 'out_time_ms' in line:
            current_time_ms = int(line.strip().split('=')[1])
            progress_percent = max(0, min(1, (current_time_ms / 1000000) / total_duration))
            elapsed_time = time.time() - start_time
            
            try:
                await status_message.edit_text(
                    f"⚙️ **Merging Videos (Robust Mode)...**\n"
                    f"➢ {get_progress_bar(progress_percent)} `{progress_percent:.1%}`\n"
                    f"➢ **Time Left:** `{get_time_left(elapsed_time, progress_percent)}`"
                )
            except: pass
    
    process.wait()
    
    if process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        await status_message.edit_text("✅ **Merge Complete!**")
        return output_path
    else:
        error_output = process.stderr.read()
        print(f"Robust merge failed. FFmpeg stderr: {error_output}")
        await status_message.edit_text(f"❌ **Merge Failed!**\nRobust method also failed. Error: `{error_output[-500:]}`")
        return None
