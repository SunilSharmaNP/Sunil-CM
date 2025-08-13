# utils.py
import time
import math
import subprocess
import os
import re
import shutil

def get_human_readable_size(size_in_bytes: int) -> str:
    """Formats size in bytes to a human-readable string (KB, MB, GB)."""
    if size_in_bytes is None:
        return "0B"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size_in_bytes > power and n < len(power_labels) -1:
        size_in_bytes /= power
        n += 1
    return f"{size_in_bytes:.2f} {power_labels[n]}B"

def get_progress_bar(progress: float, length: int = 20) -> str:
    """Creates a textual progress bar."""
    filled_len = int(length * progress)
    return '█' * filled_len + '░' * (length - filled_len)

def get_time_left(elapsed_time: float, progress: float) -> str:
    """Estimates the time remaining for the process."""
    if progress == 0:
        return "N/A"
    seconds = (elapsed_time / progress) - elapsed_time
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"

def get_video_metadata(file_path: str) -> dict:
    """
    Uses ffprobe to get video metadata.
    Returns a dictionary with 'duration', 'width', and 'height'.
    """
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "stream=width,height,duration", "-of",
        "default=noprint_wrappers=1:nokey=1", file_path
    ]
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        # Handle cases where multiple streams exist (e.g., video and audio)
        # width, height, duration
        output = process.stdout.strip().split('\n')
        # find the line with duration, it's usually the most reliable
        duration = 0
        for item in output:
            try:
                if float(item) > duration: duration = float(item)
            except ValueError:
                continue
        return {
            "width": int(output[0]),
            "height": int(output[1]),
            "duration": duration
        }
    except Exception as e:
        print(f"Error getting metadata for {file_path}: {e}")
    return {"width": 0, "height": 0, "duration": 0.0}


def create_thumbnail(video_path: str, thumbnail_path: str, duration: float) -> str | None:
    """
    Creates a thumbnail from the middle of the video.
    Returns the path to the thumbnail or None on failure.
    """
    try:
        thumbnail_time = duration / 2
        command = [
            "ffmpeg", "-i", video_path, "-ss", str(thumbnail_time),
            "-vframes", "1", "-c:v", "mjpeg", "-f", "image2", "-y",
            thumbnail_path
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        if os.path.exists(thumbnail_path):
            return thumbnail_path
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
    return None

def cleanup_files(*files_or_dirs):
    """Safely removes files and directories."""
    for item in files_or_dirs:
        try:
            if os.path.isdir(item):
                shutil.rmtree(item)
            elif os.path.isfile(item):
                os.remove(item)
        except OSError as e:
            print(f"Error cleaning up {item}: {e}")

def is_valid_url(url: str) -> bool:
    """A simple check to see if a string looks like a URL."""
    return re.match(r'https?://[^\s/$.?#].[^\s]*$', url) is not None
