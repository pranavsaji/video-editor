import subprocess
import os
import tempfile
import math


def change_video_speed(input_path: str, speed: float, output_path: str) -> str:
    """
    Change video speed using FFmpeg while maintaining quality.
    Handles audio and video separately to support any speed factor.
    """
    if not (0.05 <= speed <= 100):
        raise ValueError("Speed must be between 0.05x and 100x")

    # FFmpeg atempo filter only supports 0.5–2.0 per stage, so chain filters for extreme speeds
    def build_atempo_chain(speed: float) -> str:
        filters = []
        remaining = speed
        # atempo range per filter is [0.5, 2.0]
        while remaining > 2.0:
            filters.append("atempo=2.0")
            remaining /= 2.0
        while remaining < 0.5:
            filters.append("atempo=0.5")
            remaining /= 0.5
        filters.append(f"atempo={remaining:.6f}")
        return ",".join(filters)

    video_pts = f"setpts={1/speed:.6f}*PTS"
    audio_filter = build_atempo_chain(speed)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", video_pts,
        "-af", audio_filter,
        # Preserve quality: use libx264 with CRF 18 (visually lossless) for video
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr}")

    return output_path
