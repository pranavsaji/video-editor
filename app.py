import gradio as gr
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(__file__))
from tools.speed_video import change_video_speed
from tools.crop_video import crop_video, get_video_dimensions
from tools.merge_videos import merge_videos

os.makedirs(".tmp", exist_ok=True)


def _out_path(suffix: str, ext: str = ".mp4") -> str:
    f = tempfile.NamedTemporaryFile(suffix=f"{suffix}{ext}", delete=False, dir=".tmp")
    f.close()
    return f.name


# ── Speed ─────────────────────────────────────────────────────────────────────

def process_speed(video_path, speed):
    if video_path is None:
        return None, None, "Please upload a video."
    try:
        ext = os.path.splitext(video_path)[1] or ".mp4"
        out = _out_path(f"_speed{speed}x", ext)
        change_video_speed(video_path, speed, out)
        in_mb = os.path.getsize(video_path) / 1e6
        out_mb = os.path.getsize(out) / 1e6
        return out, out, f"Done! {speed}x  |  {in_mb:.1f} MB → {out_mb:.1f} MB"
    except Exception as e:
        return None, None, f"Error: {e}"


# ── Crop ──────────────────────────────────────────────────────────────────────

def load_video_info(video_path):
    if video_path is None:
        return gr.update(), gr.update(), gr.update(), gr.update(), "Upload a video first."
    try:
        w, h = get_video_dimensions(video_path)
        return (
            gr.update(maximum=w, value=0),
            gr.update(maximum=h, value=0),
            gr.update(maximum=w, value=w),
            gr.update(maximum=h, value=h),
            f"Video dimensions: {w} × {h} px",
        )
    except Exception as e:
        return gr.update(), gr.update(), gr.update(), gr.update(), f"Error: {e}"


def process_crop(video_path, x, y, width, height):
    if video_path is None:
        return None, None, "Please upload a video."
    try:
        ext = os.path.splitext(video_path)[1] or ".mp4"
        out = _out_path("_cropped", ext)
        crop_video(video_path, int(x), int(y), int(width), int(height), out)
        out_mb = os.path.getsize(out) / 1e6
        return out, out, f"Done! Cropped to {int(width)}×{int(height)} at ({int(x)},{int(y)})  |  {out_mb:.1f} MB"
    except Exception as e:
        return None, None, f"Error: {e}"


# ── Merge ─────────────────────────────────────────────────────────────────────

def process_merge(*args):
    # args = [v1, v2, v3, v4, v5]
    paths = [p for p in args if p is not None]
    if len(paths) < 2:
        return None, None, "Upload at least 2 videos to merge."
    try:
        out = _out_path("_merged", ".mp4")
        merge_videos(paths, out)
        out_mb = os.path.getsize(out) / 1e6
        return out, out, f"Done! Merged {len(paths)} videos  |  {out_mb:.1f} MB"
    except Exception as e:
        return None, None, f"Error: {e}"


# ── UI ────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="Video Editor") as demo:
    gr.Markdown("# Video Editor")

    with gr.Tabs():

        # ── Tab 1: Speed ──────────────────────────────────────────────────────
        with gr.TabItem("Speed"):
            gr.Markdown("Change playback speed while preserving quality.")
            with gr.Row():
                with gr.Column():
                    s_video_in = gr.Video(label="Upload Video")
                    s_slider = gr.Slider(0.1, 10.0, value=2.0, step=0.05,
                                         label="Speed Multiplier",
                                         info="0.1x = slow  |  1.0x = original  |  10.0x = fast")
                    s_number = gr.Number(value=2.0, label="Exact Speed (0.05 – 100)", precision=2)
                    s_slider.change(lambda v: v, s_slider, s_number)
                    s_number.change(lambda v: min(max(v, 0.1), 10.0), s_number, s_slider)
                    s_btn = gr.Button("Change Speed", variant="primary")
                with gr.Column():
                    s_video_out = gr.Video(label="Output Preview")
                    s_download = gr.File(label="Download")
                    s_status = gr.Textbox(label="Status", interactive=False)
            s_btn.click(process_speed, [s_video_in, s_number], [s_video_out, s_download, s_status])

        # ── Tab 2: Crop ───────────────────────────────────────────────────────
        with gr.TabItem("Crop"):
            gr.Markdown("Crop a region from the video. Upload the video first to auto-detect its dimensions.")
            with gr.Row():
                with gr.Column():
                    c_video_in = gr.Video(label="Upload Video")
                    c_info = gr.Textbox(label="Video Info", interactive=False)
                    with gr.Row():
                        c_x = gr.Number(label="X (left offset)", value=0, minimum=0, precision=0)
                        c_y = gr.Number(label="Y (top offset)", value=0, minimum=0, precision=0)
                    with gr.Row():
                        c_w = gr.Number(label="Width", value=1280, minimum=2, precision=0)
                        c_h = gr.Number(label="Height", value=720, minimum=2, precision=0)
                    c_btn = gr.Button("Crop Video", variant="primary")
                with gr.Column():
                    c_video_out = gr.Video(label="Output Preview")
                    c_download = gr.File(label="Download")
                    c_status = gr.Textbox(label="Status", interactive=False)
            c_video_in.change(load_video_info, c_video_in, [c_x, c_y, c_w, c_h, c_info])
            c_btn.click(process_crop, [c_video_in, c_x, c_y, c_w, c_h], [c_video_out, c_download, c_status])

        # ── Tab 3: Merge ──────────────────────────────────────────────────────
        with gr.TabItem("Merge"):
            gr.Markdown("Merge up to 5 videos in order. Videos are re-encoded for compatibility.")
            with gr.Row():
                with gr.Column():
                    m_v1 = gr.Video(label="Video 1")
                    m_v2 = gr.Video(label="Video 2")
                    m_v3 = gr.Video(label="Video 3 (optional)")
                    m_v4 = gr.Video(label="Video 4 (optional)")
                    m_v5 = gr.Video(label="Video 5 (optional)")
                    m_btn = gr.Button("Merge Videos", variant="primary")
                with gr.Column():
                    m_video_out = gr.Video(label="Output Preview")
                    m_download = gr.File(label="Download")
                    m_status = gr.Textbox(label="Status", interactive=False)
            m_btn.click(process_merge, [m_v1, m_v2, m_v3, m_v4, m_v5],
                        [m_video_out, m_download, m_status])

if __name__ == "__main__":
    demo.launch(share=False, theme=gr.themes.Soft())
