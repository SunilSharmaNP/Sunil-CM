import os
import subprocess

def merge_videos(video_files, output_file="merged_output.mp4"):
    with open("temp_filelist.txt", "w") as f:
        for file in video_files:
            f.write(f"file '{os.path.abspath(file)}'\n")

    result = subprocess.run(
        ["ffmpeg", "-f", "concat", "-safe", "0", "-i", "temp_filelist.txt", "-c", "copy", output_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode == 0:
        return output_file
    else:
        return None
