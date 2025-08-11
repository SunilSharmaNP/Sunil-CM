import os
import subprocess
import uuid
from config import DOWNLOAD_DIR, MERGED_FILE_NAME

def merge_videos(video_files, output_file=None):
    """
    Merges multiple videos into one.
    Uses stream copy if compatible, else re-encodes to ensure playback compatibility.

    Args:
        video_files (list): Paths to the video files to merge.
        output_file (str): Optional custom output filename.

    Returns:
        str or None: Path to merged file if successful, else None.
    """
    if not video_files or len(video_files) < 2:
        return None

    # Output path
    if not output_file:
        output_file = os.path.join(DOWNLOAD_DIR, MERGED_FILE_NAME)
    else:
        output_file = os.path.join(DOWNLOAD_DIR, output_file)

    # Create concat list for ffmpeg
    list_file = os.path.join(DOWNLOAD_DIR, f"temp_filelist_{uuid.uuid4().hex[:8]}.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for file in video_files:
            f.write(f"file '{os.path.abspath(file)}'
")

    # --- First try: Fast merge without re-encoding ---
    cmd_copy = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output_file
    ]
    result = subprocess.run(cmd_copy, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0 and os.path.exists(output_file):
        os.remove(list_file)
        return output_file

    # --- Fallback: Re-encode to ensure compatibility ---
    cmd_reencode = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "23", "-c:a", "aac", "-b:a", "192k", output_file
    ]
    result2 = subprocess.run(cmd_reencode, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Cleanup temp list
    os.remove(list_file)

    if result2.returncode == 0 and os.path.exists(output_file):
        return output_file
    else:
        # Optional: Save error log to check later
        with open(os.path.join(DOWNLOAD_DIR, "ffmpeg_error.log"), "wb") as log:
            log.write(result2.stderr)
        return None
