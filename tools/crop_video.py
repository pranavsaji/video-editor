import subprocess
import json


def get_video_dimensions(input_path: str) -> tuple[int, int]:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        input_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe error:\n{result.stderr}")
    streams = json.loads(result.stdout).get("streams", [])
    for s in streams:
        if s.get("codec_type") == "video":
            return int(s["width"]), int(s["height"])
    raise RuntimeError("No video stream found")


def crop_video(
    input_path: str,
    x: int,
    y: int,
    width: int,
    height: int,
    output_path: str,
) -> str:
    """
    Crop video to the rectangle defined by (x, y, width, height).
    Width and height must be even numbers (H.264 requirement).
    """
    # H.264 requires even dimensions
    width = width if width % 2 == 0 else width - 1
    height = height if height % 2 == 0 else height - 1

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"crop={width}:{height}:{x}:{y}",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        "-c:a", "copy",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr}")

    return output_path
