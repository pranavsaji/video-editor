# Video Editor

A local video editing tool with a clean browser UI. Built with Python, Gradio, and FFmpeg.

Supports three operations — **speed adjustment**, **cropping**, and **merging** — all with high-quality H.264 output and a download button on every tab.

---

## Features

### Speed
- Change playback speed from **0.05× to 100×**
- Slider for quick selection (0.1×–10×) plus a number input for exact values
- Audio is retimed using chained `atempo` filters (FFmpeg only supports 0.5–2.0 per stage, so extreme speeds chain multiple stages automatically)
- Video frames are retimed with `setpts`

### Crop
- Upload a video and its **width × height is auto-detected**
- Set X offset, Y offset, output width, and output height numerically
- Dimensions are automatically adjusted to be even numbers (H.264 requirement)
- Audio is copied without re-encoding for speed

### Merge
- Upload **2 to 5 videos** and concatenate them in order
- Videos are re-encoded to ensure consistent codec and resolution across clips
- Uses FFmpeg's concat demuxer

### Quality
All outputs use:
- **CRF 18 libx264** — visually lossless H.264 video
- **AAC 192k** audio
- `fast` preset — good balance of speed and compression

---

## Requirements

- macOS (tested on macOS 14+), Linux should work too
- Python 3.12+
- FFmpeg (installed via Homebrew or system package manager)

---

## Setup

**1. Clone the repo**
```bash
git clone git@github.com:pranavsaji/video-editor.git
cd video-editor
```

**2. Install FFmpeg** (if not already installed)
```bash
brew install ffmpeg        # macOS
# sudo apt install ffmpeg  # Ubuntu/Debian
```

**3. Create a virtual environment and install dependencies**
```bash
python3.12 -m venv .venv
.venv/bin/pip install gradio
```

---

## Usage

```bash
.venv/bin/python app.py
```

Then open **http://127.0.0.1:7860** in your browser.

---

## Project Structure

```
video-editor/
├── app.py                  # Gradio UI — all three tabs wired together
├── tools/
│   ├── speed_video.py      # FFmpeg speed adjustment logic
│   ├── crop_video.py       # FFmpeg crop logic + dimension detection
│   └── merge_videos.py     # FFmpeg concat demuxer logic
├── .gitignore
└── README.md
```

**`.tmp/`** is created at runtime to hold output files. It is gitignored and safe to delete at any time.

---

## How Each Tool Works

### `tools/speed_video.py`
Uses two FFmpeg filters in combination:
- `setpts=1/speed*PTS` — scales the presentation timestamp of every video frame
- `atempo` chain — adjusts audio tempo. Since FFmpeg limits each `atempo` stage to [0.5, 2.0], extreme speeds are handled by chaining multiple stages (e.g. 8× = `atempo=2.0,atempo=2.0,atempo=2.0`)

### `tools/crop_video.py`
- `ffprobe` reads the input video's stream metadata to extract width and height
- `crop=W:H:X:Y` FFmpeg filter crops the frame. Width and height are snapped to even numbers before the encode

### `tools/merge_videos.py`
- Writes a temporary FFmpeg concat list file pointing to each input video
- Passes it to FFmpeg via `-f concat -safe 0`, which reads and concatenates the files in order
- Re-encodes everything so codecs and resolution are consistent in the output

---

## Performance Notes

| Operation | Speed estimate (M-series Mac) |
|-----------|-------------------------------|
| Speed change (1h video) | ~5–15 min |
| Crop | ~3–10 min (same as a full re-encode) |
| Merge (N × 1h clips) | ~5–15 min per clip |

Encode time scales with video duration and resolution. A 22-minute 1080p video at 1.1× takes roughly **2–4 minutes**.

---

## License

MIT
