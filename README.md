# Video Editor

A local browser-based video editing tool. Built with Python, Gradio, and FFmpeg.

Three tabs: **Speed**, **Crop & Trim**, and **Merge** — every tab has a preview player and a download button.

---

## Features

### ⚡ Speed
- Change playback speed from **0.05× to 100×**
- Slider (0.1×–10×) plus a free-text number input for exact values
- Audio is retimed using chained `atempo` filters; video frames via `setpts`

### ✂️ Crop & Trim
Both operations can be applied together in a single encode pass.

**Spatial Crop**
- Enable with a checkbox
- X, Y, Width, Height sliders — auto-populated from the video's dimensions on upload
- Width/Height snap to even numbers (H.264 requirement)

**Time Trim**
- Enable with a checkbox
- Start and End sliders — auto-populated from the video's duration on upload
- **Preview Trim** button: generates a ≤30 s preview clip instantly so you can verify the cut before the full encode
- Scrub the preview player to find exact timestamps before setting the sliders

### 🔗 Merge
- Upload **any number of videos** at once via multi-file picker
- **Drag and drop** rows in the list to set the merge order
- Order badges (#1, #2 …) update live as you drag
- Videos are re-encoded to ensure consistent codec and resolution

### Quality
All outputs use:
- **CRF 18 libx264** — visually lossless H.264 video
- **AAC 192 kbps** audio
- `fast` preset — good speed/compression balance

---

## Requirements

- macOS (tested on macOS 14+) or Linux
- Python 3.12+
- FFmpeg

---

## Setup

```bash
git clone git@github.com:pranavsaji/video-editor.git
cd video-editor

# Install FFmpeg if needed
brew install ffmpeg          # macOS
# sudo apt install ffmpeg   # Ubuntu/Debian

# Create venv and install Gradio
python3.12 -m venv .venv
.venv/bin/pip install gradio
```

## Run

```bash
.venv/bin/python app.py
```

Open **http://127.0.0.1:7860** in your browser.

---

## Project Structure

```
video-editor/
├── app.py                   # Gradio UI — all tabs, event wiring
├── tools/
│   ├── speed_video.py       # Speed change via setpts + chained atempo
│   ├── crop_video.py        # Spatial crop + dimension detection (ffprobe)
│   ├── trim_video.py        # Time trim + duration detection (ffprobe)
│   └── merge_videos.py      # Concat demuxer merge
├── .gitignore
└── README.md
```

`.tmp/` is created at runtime for output files — gitignored and safe to delete.

---

## How Each Tool Works

| Tool | FFmpeg technique |
|------|-----------------|
| `speed_video.py` | `setpts=1/N*PTS` for video; chained `atempo` stages for audio (each stage capped at 0.5–2.0) |
| `crop_video.py` | `ffprobe` reads stream metadata → `crop=W:H:X:Y` filter |
| `trim_video.py` | `-ss START` before `-i` for fast seek; `-t DURATION` for frame-accurate end point |
| `merge_videos.py` | Temp concat list file → `-f concat -safe 0` |

---

## Performance (M-series Mac, 1080p)

| Operation | Estimate |
|-----------|----------|
| Speed change — 1 h video | 5–15 min |
| Crop or Trim — 1 h video | 5–15 min |
| Trim preview (≤30 s clip) | < 30 s |
| Merge — per hour of footage | 5–15 min |

A 22-minute 1080p video at 1.1× speed takes roughly **2–4 minutes**.

---

## License

MIT
