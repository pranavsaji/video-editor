import gradio as gr
import os
import tempfile
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))
from tools.speed_video import change_video_speed
from tools.crop_video import crop_video, get_video_dimensions
from tools.trim_video import trim_video, get_duration
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


# ── Crop & Trim ───────────────────────────────────────────────────────────────

def load_ct_info(video_path):
    """Auto-populate sliders when video is uploaded."""
    if video_path is None:
        return (gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), "Upload a video first.", video_path)
    try:
        w, h = get_video_dimensions(video_path)
        dur = get_duration(video_path)
        mins, secs = divmod(dur, 60)
        return (
            gr.update(maximum=w - 2, value=0, step=2),
            gr.update(maximum=h - 2, value=0, step=2),
            gr.update(maximum=w, value=w, step=2),
            gr.update(maximum=h, value=h, step=2),
            gr.update(maximum=round(dur, 1), value=0, step=0.1),
            gr.update(maximum=round(dur, 1), value=round(dur, 1), step=0.1),
            f"Size: {w}×{h} px  |  Duration: {int(mins)}m {secs:.1f}s",
            video_path,   # show uploaded video in preview player for scrubbing
        )
    except Exception as e:
        return (gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), f"Error reading video: {e}", None)


def preview_trim(video_path, start, end):
    """Generate a quick preview clip (capped at 30 s) so user can verify the cut."""
    if video_path is None:
        return None, "Upload a video first."
    if start >= end:
        return None, "Start time must be less than end time."
    try:
        preview_end = min(float(end), float(start) + 30)
        out = _out_path("_preview", ".mp4")
        trim_video(video_path, float(start), preview_end, out)
        shown = preview_end - float(start)
        return out, f"Showing {start:.1f}s → {preview_end:.1f}s  ({shown:.1f}s preview)"
    except Exception as e:
        return None, f"Error: {e}"


def process_crop_trim(video_path, x, y, w, h, start, end, do_crop, do_trim):
    if video_path is None:
        return None, None, "Please upload a video."
    if not do_crop and not do_trim:
        return None, None, "Enable at least one operation — Crop or Trim."
    try:
        current = video_path
        ext = os.path.splitext(video_path)[1] or ".mp4"

        if do_trim:
            out = _out_path("_trimmed", ext)
            trim_video(current, float(start), float(end), out)
            current = out

        if do_crop:
            out = _out_path("_cropped", ext)
            crop_video(current, int(x), int(y), int(w), int(h), out)
            current = out

        out_mb = os.path.getsize(current) / 1e6
        ops = []
        if do_trim:
            ops.append(f"trimmed {start:.1f}s–{end:.1f}s")
        if do_crop:
            ops.append(f"cropped {int(w)}×{int(h)} @ ({int(x)},{int(y)})")
        return current, current, "Done — " + ", ".join(ops) + f"  |  {out_mb:.1f} MB"
    except Exception as e:
        return None, None, f"Error: {e}"


# ── Merge ─────────────────────────────────────────────────────────────────────

def _sortable_html(paths: list[str]) -> str:
    if not paths:
        return ""
    items = "".join(
        f"""<li class="vitem" draggable="true" data-path="{p}"
              style="display:flex;align-items:center;gap:10px;padding:11px 14px;
                     margin:5px 0;background:#1f2937;border-radius:8px;
                     border:2px solid #374151;list-style:none;cursor:grab;
                     transition:border-color .15s;">
              <span style="font-size:20px;color:#6b7280;cursor:grab;">⠿</span>
              <span style="flex:1;font-size:13px;color:#e5e7eb;overflow:hidden;
                           text-overflow:ellipsis;white-space:nowrap;">{os.path.basename(p)}</span>
              <span class="badge" style="font-size:11px;color:#9ca3af;background:#111827;
                           padding:2px 8px;border-radius:4px;flex-shrink:0;">#{i+1}</span>
            </li>"""
        for i, p in enumerate(paths)
    )
    return f"""
<p style="color:#9ca3af;font-size:12px;margin:8px 0 6px;">
  🖱 Drag rows to reorder — videos merge top → bottom.
</p>
<ul id="vlist" style="padding:0;margin:0;">{items}</ul>
<script>
(function() {{
  var dragging = null;

  function renumber(list) {{
    list.querySelectorAll('.badge').forEach(function(b, i) {{
      b.textContent = '#' + (i + 1);
    }});
  }}

  function pushOrder(list) {{
    var paths = Array.from(list.querySelectorAll('.vitem'))
                     .map(function(li) {{ return li.dataset.path; }});
    /* try several selectors to find the hidden textarea */
    var box = document.querySelector('#m-order textarea')
           || document.querySelector('[data-testid="m-order"] textarea')
           || document.querySelector('textarea[data-m-order]');
    if (box) {{
      box.value = JSON.stringify(paths);
      ['input','change'].forEach(function(ev) {{
        box.dispatchEvent(new Event(ev, {{bubbles: true}}));
      }});
    }}
  }}

  function init() {{
    var list = document.getElementById('vlist');
    if (!list || list._ready) return;
    list._ready = true;

    list.querySelectorAll('.vitem').forEach(function(item) {{
      item.addEventListener('dragstart', function(e) {{
        dragging = item;
        setTimeout(function() {{ item.style.opacity = '0.4'; }}, 0);
        e.dataTransfer.effectAllowed = 'move';
      }});

      item.addEventListener('dragend', function() {{
        item.style.opacity = '1';
        list.querySelectorAll('.vitem').forEach(function(li) {{
          li.style.borderColor = '#374151';
        }});
        dragging = null;
        renumber(list);
        pushOrder(list);
      }});

      item.addEventListener('dragover', function(e) {{
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        if (!dragging || dragging === item) return;
        var rect = item.getBoundingClientRect();
        var after = e.clientY > rect.top + rect.height / 2;
        list.querySelectorAll('.vitem').forEach(function(li) {{
          li.style.borderColor = '#374151';
        }});
        item.style.borderColor = after ? '#6366f1' : '#818cf8';
        var ref = after ? item.nextSibling : item;
        if (list.insertBefore(dragging, ref) !== dragging) {{}}
        list.insertBefore(dragging, ref);
      }});

      item.addEventListener('dragleave', function() {{
        item.style.borderColor = '#374151';
      }});

      item.addEventListener('drop', function(e) {{
        e.preventDefault();
      }});
    }});
  }}

  /* retry until the list element exists in DOM */
  var attempts = 0;
  var t = setInterval(function() {{
    init();
    if (++attempts > 20) clearInterval(t);
    if (document.getElementById('vlist') && document.getElementById('vlist')._ready)
      clearInterval(t);
  }}, 300);
}})();
</script>"""


def on_files_upload(files):
    if not files:
        return [], ""
    paths = [f.name if hasattr(f, "name") else f for f in files]
    return paths, _sortable_html(paths)


def process_merge(file_state, order_json):
    if not file_state or len(file_state) < 2:
        return None, None, "Upload at least 2 videos."
    try:
        ordered = file_state
        if order_json:
            try:
                candidate = json.loads(order_json)
                candidate = [p for p in candidate if os.path.exists(p)]
                if len(candidate) >= 2:
                    ordered = candidate
            except Exception:
                pass
        out = _out_path("_merged", ".mp4")
        merge_videos(ordered, out)
        out_mb = os.path.getsize(out) / 1e6
        return out, out, f"Merged {len(ordered)} videos  |  {out_mb:.1f} MB"
    except Exception as e:
        return None, None, f"Error: {e}"


# ── UI ────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="Video Editor") as demo:
    gr.Markdown("# Video Editor")

    with gr.Tabs():

        # ── Speed ─────────────────────────────────────────────────────────────
        with gr.TabItem("⚡ Speed"):
            gr.Markdown("Change playback speed while preserving quality.")
            with gr.Row():
                with gr.Column():
                    s_in = gr.Video(label="Upload Video")
                    s_slider = gr.Slider(0.1, 10.0, value=2.0, step=0.05, label="Speed Multiplier",
                                         info="0.1x = slow  |  1.0x = original  |  10.0x = fast")
                    s_num = gr.Number(value=2.0, label="Exact Speed (0.05 – 100)", precision=2)
                    s_slider.change(lambda v: v, s_slider, s_num)
                    s_num.change(lambda v: min(max(v, 0.1), 10.0), s_num, s_slider)
                    s_btn = gr.Button("Change Speed", variant="primary")
                with gr.Column():
                    s_out = gr.Video(label="Output Preview")
                    s_dl = gr.File(label="Download")
                    s_status = gr.Textbox(label="Status", interactive=False)
            s_btn.click(process_speed, [s_in, s_num], [s_out, s_dl, s_status])

        # ── Crop & Trim ───────────────────────────────────────────────────────
        with gr.TabItem("✂️ Crop & Trim"):
            gr.Markdown(
                "**Crop** removes unwanted edges. **Trim** cuts the timeline. "
                "Upload a video — sliders auto-fill. Scrub the preview player to find timestamps."
            )
            with gr.Row():
                with gr.Column(scale=1):
                    ct_in = gr.Video(label="Upload Video")
                    ct_info = gr.Textbox(label="Video Info", interactive=False, lines=1)
                    ct_preview = gr.Video(label="Preview (scrub to find timestamps)", interactive=False)

                    with gr.Accordion("✂️ Spatial Crop", open=True):
                        ct_do_crop = gr.Checkbox(label="Enable Crop", value=False)
                        with gr.Row():
                            ct_x = gr.Slider(0, 1920, value=0, step=2, label="X — left edge")
                            ct_y = gr.Slider(0, 1080, value=0, step=2, label="Y — top edge")
                        with gr.Row():
                            ct_w = gr.Slider(2, 1920, value=1920, step=2, label="Width")
                            ct_h = gr.Slider(2, 1080, value=1080, step=2, label="Height")

                    with gr.Accordion("⏱ Time Trim", open=True):
                        ct_do_trim = gr.Checkbox(label="Enable Trim", value=False)
                        ct_start = gr.Slider(0, 3600, value=0, step=0.1, label="Start (seconds)")
                        ct_end   = gr.Slider(0, 3600, value=60,  step=0.1, label="End (seconds)")
                        with gr.Row():
                            ct_prev_btn = gr.Button("Preview Trim", size="sm")
                            ct_prev_status = gr.Textbox(show_label=False, interactive=False,
                                                        placeholder="Preview status…", scale=3)

                    ct_btn = gr.Button("Apply", variant="primary", size="lg")

                with gr.Column(scale=1):
                    ct_out = gr.Video(label="Output Preview")
                    ct_dl  = gr.File(label="Download")
                    ct_status = gr.Textbox(label="Status", interactive=False)

            ct_in.change(
                load_ct_info, ct_in,
                [ct_x, ct_y, ct_w, ct_h, ct_start, ct_end, ct_info, ct_preview]
            )
            ct_prev_btn.click(preview_trim, [ct_in, ct_start, ct_end], [ct_preview, ct_prev_status])
            ct_btn.click(
                process_crop_trim,
                [ct_in, ct_x, ct_y, ct_w, ct_h, ct_start, ct_end, ct_do_crop, ct_do_trim],
                [ct_out, ct_dl, ct_status]
            )

        # ── Merge ─────────────────────────────────────────────────────────────
        with gr.TabItem("🔗 Merge"):
            gr.Markdown("Upload any number of videos, then **drag rows** to set the order before merging.")
            with gr.Row():
                with gr.Column(scale=1):
                    m_files = gr.File(label="Upload Videos", file_count="multiple")
                    m_state = gr.State([])
                    m_list  = gr.HTML("")
                    m_order = gr.Textbox(visible=False, elem_id="m-order", label="order")
                    m_btn   = gr.Button("Merge Videos", variant="primary", size="lg")
                with gr.Column(scale=1):
                    m_out    = gr.Video(label="Output Preview")
                    m_dl     = gr.File(label="Download")
                    m_status = gr.Textbox(label="Status", interactive=False)

            m_files.change(on_files_upload, m_files, [m_state, m_list])
            m_btn.click(process_merge, [m_state, m_order], [m_out, m_dl, m_status])


if __name__ == "__main__":
    demo.launch(share=False, theme=gr.themes.Soft())
