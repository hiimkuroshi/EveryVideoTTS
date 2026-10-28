import re
import time
import gc
import sys
import gradio as gr
import soundfile as sf
from functools import lru_cache

def _format_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"

def _split_estimate_status(status: str) -> tuple[str, str]:
    if not isinstance(status, str):
        return status, ""

    estimate_marker = " | Ước tính còn lại: "
    if estimate_marker in status:
        status_text, estimate_text = status.split(" | ", 1)
        if status.endswith("...") and not status_text.endswith("..."):
            status_text += "..."
        return status_text, estimate_text.rstrip(". ")

    if ("batch mẫu:" in status or "trung bình batch:" in status) and "ước tính còn lại:" in status:
        start = status.find("(")
        end = status.rfind(")")
        if start != -1 and end != -1 and end > start:
            status_text = status[:start].strip()
            estimate_text = status[start + 1:end].replace(", ", "\n")
            return status_text, estimate_text

    return status, ""

_PROGRESS_DONE = re.compile(r"Đã xong\s+(\d+)\s*/\s*(\d+)")
_PROGRESS_BRACKET = re.compile(r"\[(\d+)\s*/\s*(\d+)\]")
_PROGRESS_UNIT = re.compile(r"\b(lô|batch|đoạn)\s+(\d+)\s*/\s*(\d+)", re.IGNORECASE)
_UNIT_LABELS = {"lô": "Lô", "batch": "Lô", "đoạn": "Đoạn"}


def extract_job_progress(status: str) -> dict | None:
    """Read "how far along" from any backend status line.

    Understands "Đã xong 2/5", "[3/12] …" (line i of n), and "lô/batch/đoạn i/n".
    Returns {"done", "total", "label"}; "done" counts finished units, so a line
    that says "đang xử lý đoạn 3/5" means 2 are done.
    """
    if not isinstance(status, str):
        return None
    m = _PROGRESS_DONE.search(status)
    if m:
        done, total = int(m.group(1)), int(m.group(2))
        nxt = min(done + 1, total)
        return {"done": done, "total": total, "label": f"Đoạn {nxt}/{total}"} if total else None
    m = _PROGRESS_BRACKET.search(status)
    if m:
        cur, total = int(m.group(1)), int(m.group(2))
        return {"done": cur - 1, "total": total, "label": f"Câu {cur}/{total}"} if total else None
    m = _PROGRESS_UNIT.search(status)
    if m:
        unit = _UNIT_LABELS.get(m.group(1).lower(), m.group(1).capitalize())
        cur, total = int(m.group(2)), int(m.group(3))
        return {"done": cur - 1, "total": total, "label": f"{unit} {cur}/{total}"} if total else None
    return None


def stream_with_status(synthesize_fn):
    """Adapt a (audio, status_text) generator to (audio_update, status_html) for the UI.

    Adds a progress bar and a time-remaining estimate measured from how fast
    units (lines, chunks, batches) finish. The audio player stays hidden until
    there is something to play.
    """
    from apps.ui_components import render_status

    def wrapper(*args):
        first_t = first_done = None
        last_done = None
        for audio, status in synthesize_fn(*args):
            status_text, embedded_eta = _split_estimate_status(status)
            progress = extract_job_progress(status_text)
            eta = ""
            m = re.search(r"ước tính còn lại:\s*([^)\n]+)", status_text or "", re.IGNORECASE)
            if embedded_eta:
                eta = embedded_eta
            elif m:
                eta = f"Còn khoảng {m.group(1).strip().rstrip('.')}"
            elif progress:
                now = time.time()
                if first_t is None or (last_done is not None and progress["done"] < last_done):
                    first_t, first_done = now, progress["done"]
                last_done = progress["done"]
                finished = progress["done"] - first_done
                if finished > 0:
                    per_unit = (now - first_t) / finished
                    remaining = per_unit * max(0, progress["total"] - progress["done"])
                    eta = f"Còn khoảng {_format_duration(remaining)}"
                else:
                    eta = "Đang ước tính thời gian…"
            if isinstance(eta, str) and eta.startswith("Ước tính còn lại: "):
                eta = "Còn khoảng " + eta[len("Ước tính còn lại: "):]
            has_audio = audio is not None
            yield gr.update(value=audio, visible=has_audio), render_status(status_text, eta, progress)

    return wrapper


def cleanup_gpu_memory():
    """Aggressively cleanup GPU memory (CUDA, MPS, XPU)"""
    if 'torch' in sys.modules:
        import torch
        if hasattr(torch, 'cuda') and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        if hasattr(torch, 'backends') and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            torch.mps.empty_cache()
        if hasattr(torch, 'xpu') and torch.xpu.is_available():
            torch.xpu.empty_cache()
            torch.xpu.synchronize()
    gc.collect()

@lru_cache(maxsize=32)
def get_ref_text_cached(text_path: str) -> str:
    """Cache reference text loading"""
    with open(text_path, "r", encoding="utf-8") as f:
        return f.read()

def on_codec_change(codec: str, current_mode: str):
    is_onnx = "onnx" in codec.lower()
    if is_onnx and current_mode == "custom_mode":
        return gr.update(visible=False), gr.update(selected="preset_mode"), "preset_mode"
    return gr.update(visible=not is_onnx), gr.update(), current_mode

def validate_audio_duration(audio_path):
    if not audio_path:
        return gr.update(visible=False)
    try:
        info = sf.info(audio_path)
        if info.duration > 5.1:
            return gr.update(
                value=f"⚠️ **Cảnh báo:** Audio mẫu hiện tại dài {info.duration:.1f} giây. Để có kết quả clone giọng tối ưu, bạn nên sử dụng đoạn audio có độ dài lý tưởng từ **3 đến 5 giây**.",
                visible=True
            )
    except Exception:
        pass
    return gr.update(visible=False)

def on_custom_id_change(model_id):
    # Auto detect LoRA and base model
    if model_id and "lora" in model_id.lower():
        # Detect base model
        if "0.3" in model_id:
            base_model = "VieNeu-TTS-0.3B (GPU)"
        else:
            base_model = "VieNeu-TTS (GPU)"

        return (
            gr.update(visible=True, value=base_model),
            gr.update(), gr.update()
        )

    return (
        gr.update(visible=False),
        gr.update(),
        gr.update()
    )
