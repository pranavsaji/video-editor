import subprocess
import tempfile
import os


def merge_videos(input_paths: list[str], output_path: str) -> str:
    """
    Concatenate videos in order using FFmpeg concat demuxer.
    Re-encodes to ensure consistent codec/resolution across all clips.
    """
    if len(input_paths) < 2:
        raise ValueError("Need at least 2 videos to merge")

    # Write a temp concat list file
    list_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, dir=".tmp"
    )
    for path in input_paths:
        # ffmpeg concat list requires escaped single quotes
        safe = path.replace("'", "'\\''")
        list_file.write(f"file '{safe}'\n")
    list_file.close()

    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file.name,
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error:\n{result.stderr}")
    finally:
        os.unlink(list_file.name)

    return output_path
