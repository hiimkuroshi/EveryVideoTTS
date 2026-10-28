import os
import sys
import subprocess

# --- Add XPU dll path ---
intel_dll_path = os.path.join(sys.prefix, 'Library', 'bin')

if os.path.exists(intel_dll_path):
    os.environ['PATH'] = intel_dll_path + os.pathsep + os.environ['PATH']
else:
    print(f"⚠️ Không tìm thấy thư mục DLL Intel XPU: {intel_dll_path}")
    
import torch
import gradio as gr
import soundfile as sf
import tempfile
import time
import numpy as np
import queue
import threading
import yaml
import gc

from vieneu.core_xpu import XPUVieNeuTTS
from vieneu_utils.core_utils import split_text_into_chunks, join_audio_chunks, env_bool
# PuncNormalizer = sea_g2p.Normalizer luôn bật punc_norm=True.
from vieneu_utils.phonemize_text import PuncNormalizer as Normalizer, normalize_to_chunks

from apps.ui_utils import (
    _format_duration,
    stream_with_status,
    cleanup_gpu_memory,
    get_ref_text_cached,
    on_codec_change,
    validate_audio_duration,
    on_custom_id_change
)
from apps.ui_constants import (
    theme,
    css,
    head_html,
    i18n,
    WAVEFORM_COLOR,
    WAVEFORM_PROGRESS_COLOR,
    DEFAULT_TEXT_GPU
)
from apps.ui_components import (
    render_header,
    render_model_status,
    render_status,
    model_state,
    model_accordion_label,
    section_head,
    panel_head,
    footnote_watermark,
)

try:
    if not hasattr(torch, 'xpu') or not torch.xpu.is_available():
        print("⚠️ Không tìm thấy thiết bị Intel XPU (Intel Arc GPU).")
        print("🔄 Đang tự động chuyển hướng sang phiên bản CPU/CUDA (gradio_app.py)...")
        # Chạy file gradio_app.py và truyền tiếp các arguments (nếu có)
        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "gradio_main.py")] + sys.argv[1:])
        sys.exit(0)
except ImportError:
    pass

print("⏳ Đang khởi động EveryVideoTTS Studio (Phiên bản tối ưu cho Intel XPU)...")


# --- CONSTANTS & CONFIG ---
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f) or {}
except Exception as e:
    raise RuntimeError(f"Không thể đọc config.yaml: {e}")

BACKBONE_CONFIGS = _config.get("backbone_configs", {})
CODEC_CONFIGS = _config.get("codec_configs", {})

_text_settings = _config.get("text_settings", {})
MAX_CHARS_PER_CHUNK = _text_settings.get("max_chars_per_chunk", 256)

if not BACKBONE_CONFIGS or not CODEC_CONFIGS:
    raise ValueError("config.yaml thiếu backbone_configs hoặc codec_configs")

# --- 1. MODEL CONFIGURATION ---
# Global model instance
tts = None
current_backbone = None
current_codec = None
model_loaded = False

# Normalizer (module-level singleton)
_text_normalizer = Normalizer()

def get_available_devices() -> list[str]:
    """Chỉ trả về XPU cho phiên bản này."""
    return ["XPU"]

def get_model_status_message() -> str:
    """Reconstruct status message from global state"""
    global model_loaded, tts, current_backbone, current_codec
    if not model_loaded or tts is None:
        return "⏳ Chưa tải model."
    
    backbone_config = BACKBONE_CONFIGS.get(current_backbone, {})
    codec_config = CODEC_CONFIGS.get(current_codec, {})
    
    backend_name = "Intel XPU (BFloat16)"
    codec_device = "CPU" if "ONNX" in (current_codec or "") else "XPU"

    preencoded_note = "\n⚠️ Codec ONNX không hỗ trợ clone giọng." if codec_config.get('use_preencoded') else ""

    # Format read by apps.ui_components.render_model_status.
    return (
        f"✅ Model đã sẵn sàng\n"
        f"Model: {current_backbone}\n"
        f"Thiết bị: Intel XPU\n"
        f"Backend: {backend_name}\n"
        f"Codec: {current_codec} ({codec_device}){preencoded_note}"
    )

def restore_ui_state():
    """Update UI components based on persistence"""
    global model_loaded
    msg = get_model_status_message()
    return (
        msg, 
        gr.update(interactive=model_loaded), # btn_generate
        gr.update(interactive=False)         # btn_stop
    )

def load_model(backbone_choice: str, codec_choice: str, device_choice: str, 
               custom_model_id: str = "", custom_base_model: str = "", custom_hf_token: str = ""):
    """Load model with XPU optimizations"""
    global tts, current_backbone, current_codec, model_loaded
    model_loaded = False 
    
    yield (
        "⏳ Đang tải model lên Intel XPU… Lần đầu cần tải trọng số nên có thể mất vài phút.",
        gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False),
        gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
    )
    
    try:
        # Cleanup before loading new model
        if tts is not None:
            tts = None 
            cleanup_gpu_memory()
        
        custom_loading = False
        is_merged_lora = False

        if backbone_choice == "Custom Model":
            custom_loading = True
            if not custom_model_id or not custom_model_id.strip():
                yield (
                    "❌ Lỗi: Vui lòng nhập Model ID cho Custom Model.",
                    gr.update(interactive=False), gr.update(interactive=True), gr.update(interactive=False),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
                )
                return

            if "lora" in custom_model_id.lower():
                print(f"🔄 Detected LoRA in name. preparing merge with base: {custom_base_model}")
                if custom_base_model not in BACKBONE_CONFIGS:
                    yield (
                        f"❌ Lỗi: Base Model '{custom_base_model}' không hợp lệ.",
                        gr.update(interactive=False), gr.update(interactive=True), gr.update(interactive=False),
                        gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
                    )
                    return
                
                base_config = BACKBONE_CONFIGS[custom_base_model]
                backbone_config = {
                    "repo": base_config["repo"],
                    "supports_streaming": base_config["supports_streaming"],
                    "description": f"Custom Merged: {custom_model_id} + {custom_base_model}"
                }
                is_merged_lora = True
            else:
                backbone_config = {
                    "repo": custom_model_id.strip(),
                    "supports_streaming": False,
                    "description": f"Custom Model: {custom_model_id}"
                }
        else:
            backbone_config = BACKBONE_CONFIGS[backbone_choice]
            
        codec_config = CODEC_CONFIGS[codec_choice]
        
        # Bắt buộc thiết lập device là XPU
        backbone_device = "xpu"
        codec_device = "cpu" if "ONNX" in codec_choice else "xpu"
        
        print(f"📦 Loading model on XPU...")
        print(f"   Backbone: {backbone_config['repo']} on {backbone_device}")
        print(f"   Codec: {codec_config['repo']} on {codec_device}")
        
        tts = XPUVieNeuTTS(
            backbone_repo=backbone_config["repo"],
            backbone_device=backbone_device,
            codec_repo=codec_config["repo"],
            codec_device=codec_device,
            hf_token=custom_hf_token
        )

        # Xử lý LoRA Merge trực tiếp trên XPU
        if is_merged_lora and custom_loading:
            yield (
                f"🔄 Đang tải và merge LoRA adapter: {custom_model_id} trên XPU...",
                gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False),
                gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            )
            try:
                tts.load_lora_adapter(custom_model_id.strip(), hf_token=custom_hf_token)
                if hasattr(tts, 'backbone') and hasattr(tts.backbone, 'merge_and_unload'):
                    print("   🔄 Merging LoRA into backbone...")
                    tts.backbone = tts.backbone.merge_and_unload()
                    tts._lora_loaded = False 
                    tts._current_lora_repo = None
                    print("   ✅ Merged successfully!")
                else:
                    print("   ⚠️ Warning: Model does not support merge_and_unload, keeping adapter active.")
            except Exception as e:
                 raise RuntimeError(f"Failed to merge LoRA: {e}")
        
        current_backbone = backbone_choice
        current_codec = codec_choice
        model_loaded = True
        
        success_msg = get_model_status_message()
            
        # Prepare voice update
        try:
            voices = tts.list_preset_voices()
        except Exception:
            voices = []

        has_voices = len(voices) > 0
        
        if has_voices:
            default_v = tts._default_voice
            is_tuple = (len(voices) > 0 and isinstance(voices[0], tuple))
            voice_values = [v[1] for v in voices] if is_tuple else voices
            
            if not default_v and voice_values:
                 default_v = voice_values[0]

            if default_v and default_v not in voice_values:
                if is_tuple:
                    voices.append((default_v, default_v))
                else:
                    voices.append(default_v)
            
            if is_tuple:
                voices.sort(key=lambda x: str(x[0]))
            else:
                voices.sort()

            voice_update = gr.update(choices=voices, value=default_v, interactive=True)
            
            tab_p = gr.update(visible=True)
            tab_c = gr.update(visible=True)
            tab_sel = gr.update(selected="preset_mode")
            mode_state = "preset_mode"
        else:
            msg = "⚠️ Không tìm thấy file voices.json. Vui lòng dùng Tab Voice Cloning."
            voice_update = gr.update(choices=[msg], value=msg, interactive=False)
            
            tab_p = gr.update(visible=True)
            tab_c = gr.update(visible=True)
            tab_sel = gr.update(selected="preset_mode")
            mode_state = "preset_mode"

        yield (
            success_msg,
            gr.update(interactive=True), # btn_generate
            gr.update(interactive=True), # btn_load
            gr.update(interactive=False), # btn_stop
            voice_update,
            tab_p, tab_c, tab_sel, mode_state
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        model_loaded = False

        yield (
            f"❌ Lỗi khi tải model: {str(e)}",
            gr.update(interactive=False),
            gr.update(interactive=True),
            gr.update(interactive=False),
            gr.update(),
            gr.update(), gr.update(), gr.update(), gr.update()
        )


# --- 2. DATA & HELPERS ---

def synthesize_speech(text: str, voice_choice: str, custom_audio, custom_text: str, 
                      mode_tab: str, generation_mode: str,
                      use_batch: bool, max_batch_size_run: int, # Added as decoys
                      temperature: float, max_chars_chunk: int):
    """Synthesis using XPU logic (Sequential generation with autocast)"""
    global tts, current_backbone, current_codec, model_loaded
    
    if not model_loaded or tts is None:
        yield None, "⚠️ Vui lòng tải model trước!"
        return
    
    if not text or text.strip() == "":
        yield None, "⚠️ Vui lòng nhập văn bản!"
        return
    
    raw_text = text.strip()
    
    yield None, "📄 Đang xử lý Reference..."
    
    try:
        ref_codes = None
        ref_text_raw = ""
        
        if mode_tab == "preset_mode":
            if not voice_choice or "⚠️" in voice_choice:
                raise ValueError("Vui lòng chọn giọng mẫu hoặc chuyển sang Tab Voice Cloning.")
            
            voice_data = tts.get_preset_voice(voice_choice)
            ref_codes = voice_data['codes']
            ref_text_raw = voice_data['text']
            
        elif mode_tab == "custom_mode":
            if custom_audio is None:
                 raise ValueError("Vui lòng upload file Audio mẫu (Reference Audio)!")
            if not custom_text or not custom_text.strip():
                 raise ValueError("Vui lòng nhập nội dung văn bản của Audio mẫu (Reference Text)!")
            
            ref_text_raw = custom_text.strip()
            ref_codes = tts.encode_reference(custom_audio)
            
        else:
            raise ValueError(f"Unknown mode: {mode_tab}")

        if isinstance(ref_codes, torch.Tensor):
            ref_codes = ref_codes.cpu().numpy()

    except Exception as e:
        yield None, f"❌ Lỗi xử lý Reference Audio: {str(e)}"
        return
    
    # Chia chunk SAU normalize: normalize cả văn bản trước rồi mới cắt theo độ dài
    # ĐÃ chuẩn hóa (tránh chunk phình quá max_chars khi normalizer mở rộng text).
    text_chunks = normalize_to_chunks(raw_text, max_chars=max_chars_chunk)
    total_chunks = len(text_chunks)
    
    if not text_chunks:
        yield None, "❌ Không có đoạn văn bản nào để tổng hợp."
        return
    
    # === STANDARD MODE ===
    if generation_mode == "Standard (Một lần)":
        # Note: use_batch and max_batch_size_run are available here but currently ignored/decoy
        yield None, f"🚀 Bắt đầu tổng hợp trên Intel XPU ({total_chunks} đoạn)..."
        
        all_wavs = []
        sr = 24000
        start_time = time.time()
        
        if use_batch and total_chunks > 1:
            try:
                num_batches = (
                    total_chunks + max_batch_size_run - 1
                ) // max_batch_size_run
                total_batch_duration = 0.0
                completed_batches = 0

                for i in range(0, len(text_chunks), max_batch_size_run):
                    batch_idx = i // max_batch_size_run
                    estimate_info = ""
                    if completed_batches > 0:
                        average_batch_duration = total_batch_duration / completed_batches
                        estimated_total = average_batch_duration * num_batches
                        estimated_remaining = average_batch_duration * max(0, num_batches - batch_idx)
                        estimate_info = (
                            f" | Ước tính còn lại: {_format_duration(estimated_remaining)}"
                            f" / tổng: {_format_duration(estimated_total)}"
                        )
                    yield (
                        None,
                        f"⏳ Đang xử lý batch {batch_idx + 1}/{num_batches}{estimate_info} ...",
                    )
                    batch_chunks = text_chunks[i : i + max_batch_size_run]
                    
                    # Gọi hàm infer_batch đã viết ở trên
                    batch_start_time = time.time()
                    batch_results = tts.infer_batch(
                        texts = batch_chunks,  
                        ref_codes=ref_codes, 
                        ref_text=ref_text_raw,
                        temperature=temperature,
                        skip_normalize=True
                    )
                    batch_duration = time.time() - batch_start_time
                    total_batch_duration += batch_duration
                    completed_batches += 1
                    average_batch_duration = total_batch_duration / completed_batches
                    estimated_total = average_batch_duration * num_batches
                    estimated_remaining = average_batch_duration * max(0, num_batches - completed_batches)

                    if batch_results is not None and len(batch_results) > 0:
                        all_wavs.extend(batch_results)
                    yield (
                        None,
                        (
                            f"✅ Xong batch {batch_idx + 1}/{num_batches} "
                            f"(trung bình batch: {_format_duration(average_batch_duration)}, "
                            f"ước tính còn lại: {_format_duration(estimated_remaining)}, "
                            f"tổng: {_format_duration(estimated_total)})"
                        ),
                    )

                if not all_wavs:
                    yield None, "❌ Không sinh được audio nào."
                    return

                yield None, "💾 Đang ghép file và lưu..."
                
                final_wav = join_audio_chunks(all_wavs, sr=sr, silence_p=0.15)
            
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    sf.write(tmp.name, final_wav, sr)
                    output_path = tmp.name
                
                process_time = time.time() - start_time
                speed_info = f", Tốc độ: {len(final_wav)/sr/process_time:.2f}x realtime" if process_time > 0 else ""
            
                yield output_path, f"✅ Hoàn tất! (Thời gian: {process_time:.2f}s{speed_info}) (Backend: Intel XPU)"
                cleanup_gpu_memory()
                return
            
            except Exception as e:
                import traceback
                traceback.print_exc()
                cleanup_gpu_memory()
                yield None, f"❌ Lỗi Standard Mode khi infer batch: {str(e)}"
                return
        try:
            # Sequential processing (Native XPU backend)
            for i, chunk in enumerate(text_chunks):
                yield None, f"⏳ Đang xử lý đoạn {i+1}/{total_chunks} (XPU Bfloat16)..."
                
                chunk_wav = tts.infer(
                    chunk, 
                    ref_codes=ref_codes, 
                    ref_text=ref_text_raw,
                    temperature=temperature,
                    skip_normalize=True
                )
                
                if chunk_wav is not None and len(chunk_wav) > 0:
                    all_wavs.append(chunk_wav)
            
            if not all_wavs:
                yield None, "❌ Không sinh được audio nào."
                return
            
            yield None, "💾 Đang ghép file và lưu..."
            
            final_wav = join_audio_chunks(all_wavs, sr=sr, silence_p=0.15)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                sf.write(tmp.name, final_wav, sr)
                output_path = tmp.name
            
            process_time = time.time() - start_time
            speed_info = f", Tốc độ: {len(final_wav)/sr/process_time:.2f}x realtime" if process_time > 0 else ""
            
            yield output_path, f"✅ Hoàn tất! (Thời gian: {process_time:.2f}s{speed_info}) (Backend: Intel XPU)"
            cleanup_gpu_memory()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            cleanup_gpu_memory()
            yield None, f"❌ Lỗi Standard Mode: {str(e)}"
            return
    
    # === STREAMING MODE ===
    else:
        sr = 24000
        crossfade_samples = int(sr * 0.03)
        audio_queue = queue.Queue(maxsize=100)
        PRE_BUFFER_SIZE = 3
        
        end_event = threading.Event()
        error_event = threading.Event()
        error_msg = ""
        
        def producer_thread():
            nonlocal error_msg
            try:
                previous_tail = None
                
                for i, chunk_text in enumerate(text_chunks):
                    stream_gen = tts.infer_stream(
                        chunk_text, 
                        ref_codes=ref_codes, 
                        ref_text=ref_text_raw,
                        temperature=temperature,
                        skip_normalize=True
                    )
                    
                    for part_idx, audio_part in enumerate(stream_gen):
                        if audio_part is None or len(audio_part) == 0:
                            continue
                        
                        if previous_tail is not None and len(previous_tail) > 0:
                            overlap = min(len(previous_tail), len(audio_part), crossfade_samples)
                            if overlap > 0:
                                fade_out = np.linspace(1.0, 0.0, overlap, dtype=np.float32)
                                fade_in = np.linspace(0.0, 1.0, overlap, dtype=np.float32)
                                
                                blended = (audio_part[:overlap] * fade_in + 
                                         previous_tail[-overlap:] * fade_out)
                                
                                processed = np.concatenate([
                                    previous_tail[:-overlap] if len(previous_tail) > overlap else np.array([]),
                                    blended,
                                    audio_part[overlap:]
                                ])
                            else:
                                processed = np.concatenate([previous_tail, audio_part])
                            
                            tail_size = min(crossfade_samples, len(processed))
                            previous_tail = processed[-tail_size:].copy()
                            output_chunk = processed[:-tail_size] if len(processed) > tail_size else processed
                        else:
                            tail_size = min(crossfade_samples, len(audio_part))
                            previous_tail = audio_part[-tail_size:].copy()
                            output_chunk = audio_part[:-tail_size] if len(audio_part) > tail_size else audio_part
                        
                        if len(output_chunk) > 0:
                            audio_queue.put((sr, output_chunk))
                
                if previous_tail is not None and len(previous_tail) > 0:
                    audio_queue.put((sr, previous_tail))
                    
            except Exception as e:
                import traceback
                traceback.print_exc()
                error_msg = str(e)
                error_event.set()
            finally:
                end_event.set()
                audio_queue.put(None)
        
        threading.Thread(target=producer_thread, daemon=True).start()
        
        yield (sr, np.zeros(int(sr * 0.05))), "📄 Đang buffering..."
        
        pre_buffer = []
        while len(pre_buffer) < PRE_BUFFER_SIZE:
            try:
                item = audio_queue.get(timeout=5.0)
                if item is None:
                    break
                pre_buffer.append(item)
            except queue.Empty:
                if error_event.is_set():
                    yield None, f"❌ Lỗi: {error_msg}"
                    return
                break
        
        full_audio_buffer = []
        for sr, audio_data in pre_buffer:
            full_audio_buffer.append(audio_data)
            yield (sr, audio_data), f"🔊 Đang phát (Intel XPU)..."
        
        while True:
            try:
                item = audio_queue.get(timeout=0.05)
                if item is None:
                    break
                sr, audio_data = item
                full_audio_buffer.append(audio_data)
                yield (sr, audio_data), f"🔊 Đang phát (Intel XPU)..."
            except queue.Empty:
                if error_event.is_set():
                    yield None, f"❌ Lỗi: {error_msg}"
                    break
                if end_event.is_set() and audio_queue.empty():
                    break
                continue
        
        if full_audio_buffer:
            final_wav = np.concatenate(full_audio_buffer)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                sf.write(tmp.name, final_wav, sr)
                yield tmp.name, f"✅ Hoàn tất Streaming! (Intel XPU)"
            
            cleanup_gpu_memory()


def _short_model_name(name: str) -> str:
    name = name or ""
    return name[len("VieNeu-TTS-"):] if name.startswith("VieNeu-TTS-") else name


def _xpu_ui_extras(message: str, backbone: str):
    state = model_state(message)
    return (
        render_header(state, _short_model_name(backbone), edition="Intel XPU"),
        gr.update(open=(state != "ready"), label=model_accordion_label(state, backbone)),
    )


def load_model_ui(backbone_choice, codec_choice, device_choice,
                  custom_model_id="", custom_base_model="", custom_hf_token=""):
    for out in load_model(backbone_choice, codec_choice, device_choice,
                          custom_model_id, custom_base_model, custom_hf_token):
        out = list(out)
        message = out[0]
        out[0] = render_model_status(message)
        btn_update = dict(out[2]) if isinstance(out[2], dict) else {"__type__": "update"}
        btn_update["value"] = "Đang tải…" if model_state(message) == "loading" else "Tải model"
        out[2] = btn_update
        yield (*out, *_xpu_ui_extras(message, backbone_choice))


def restore_ui_state_ui():
    message, *rest = restore_ui_state()
    return (render_model_status(message), *rest, *_xpu_ui_extras(message, current_backbone or ""))


synthesize_speech_ui = stream_with_status(synthesize_speech)
_AUDIO_REF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "audio_ref")
_WAVEFORM = gr.WaveformOptions(waveform_color=WAVEFORM_COLOR, waveform_progress_color=WAVEFORM_PROGRESS_COLOR,
                               skip_length=5)

with gr.Blocks(theme=theme, css=css, title="EveryVideoTTS Studio (Intel XPU)", head=head_html) as demo:

    with gr.Column(elem_id="evt-app"):
        header_html = gr.HTML(render_header("idle", edition="Intel XPU"), padding=False, container=False)

        # ================================ MODEL CARD ================================
        with gr.Accordion(model_accordion_label("idle"), open=True, elem_id="evt-model-card") as model_card:
            with gr.Row(elem_id="evt-model-row", equal_height=False):
                backbone_select = gr.Dropdown(
                    list(BACKBONE_CONFIGS.keys()) + ["Custom Model"],
                    value="VieNeu-TTS (GPU)",
                    label="Model",
                    scale=4,
                    min_width=220,
                )
                codec_select = gr.Dropdown(list(CODEC_CONFIGS.keys()), value="NeuCodec (Distill)", label="Codec",
                                           scale=3, min_width=180)
                device_choice = gr.Radio(get_available_devices(), value="XPU", label="Thiết bị", interactive=False,
                                         scale=1, min_width=110)
                btn_load = gr.Button("Tải model", variant="primary", scale=2, min_width=150)

            with gr.Row(visible=False, equal_height=False) as custom_model_group:
                custom_backbone_model_id = gr.Textbox(
                    label="Model ID",
                    placeholder="pnnbao-ump/VieNeu-TTS-0.3B-lora-ngoc-huyen",
                    info="Repo ID trên Hugging Face hoặc đường dẫn thư mục local.",
                    scale=2
                )
                custom_backbone_hf_token = gr.Textbox(
                    label="HF token",
                    placeholder="Để trống nếu repo public",
                    type="password",
                    info="Chỉ cần với repo private.",
                    scale=1
                )
                custom_backbone_base_model = gr.Dropdown(
                    [k for k in BACKBONE_CONFIGS.keys() if "gguf" not in k.lower()],
                    label="Base model cho LoRA",
                    value="VieNeu-TTS-0.3B (GPU)",
                    allow_custom_value=True,
                    visible=False,
                    info="Model gốc để merge LoRA.",
                    scale=1
                )

            model_status = gr.HTML(render_model_status("⏳ Chưa tải model."), padding=False)
            gr.HTML(
                '<div class="evt-note"><b>Chế độ tối ưu cho Intel Arc (XPU).</b> Ứng dụng chạy trên PyTorch XPU. '
                'Lần tạo giọng <b>đầu tiên</b> (hoặc sau khi đổi model) sẽ lâu hơn một chút; các lần sau sẽ nhanh hơn. '
                'Chọn <b>Custom Model</b> để nạp LoRA hoặc model finetune từ VieNeu-TTS / VieNeu-TTS-0.3B.</div>',
                padding=False,
            )

        # ================================ WORKSPACE =================================
        with gr.Row(elem_id="evt-workspace", equal_height=False):
            with gr.Column(scale=7, min_width=360, elem_classes="evt-card", elem_id="evt-main"):
                gr.HTML(section_head("Văn bản", count_for="evt-text"), padding=False)
                text_input = gr.Textbox(
                    label="Văn bản",
                    show_label=False,
                    lines=9,
                    max_lines=30,
                    value=DEFAULT_TEXT_GPU,
                    placeholder="Nhập hoặc dán nội dung cần đọc…",
                    elem_id="evt-text",
                )

                gr.HTML(section_head("Giọng đọc"), padding=False)
                with gr.Tabs(elem_classes="evt-seg") as tabs:
                    with gr.TabItem("Giọng có sẵn", id="preset_mode") as tab_preset:
                        voice_select = gr.Dropdown(choices=[], value=None, label="Giọng mẫu",
                                                   info="Mỗi model có bộ giọng riêng — danh sách hiện ra sau khi tải model.")

                    with gr.TabItem("Clone giọng", id="custom_mode") as tab_custom:
                        custom_audio = gr.Audio(label="Audio giọng mẫu (3–5 giây)", type="filepath",
                                                elem_classes="evt-ref-audio", waveform_options=_WAVEFORM)
                        cloning_warning_msg = gr.Markdown(visible=False, elem_id="cloning-warning")
                        custom_text = gr.Textbox(
                            label="Nội dung của audio mẫu",
                            info="Gõ đúng từng chữ trong audio mẫu, kể cả dấu câu (.,?!) — model rất nhạy với dấu câu.",
                        )
                        gr.Examples(
                            examples=[
                                [os.path.join(_AUDIO_REF_DIR, "example.wav"), "Ví dụ 2. Tính trung bình của dãy số."],
                                [os.path.join(_AUDIO_REF_DIR, "example_2.wav"), "Trên thực tế, các nghi ngờ đã bắt đầu xuất hiện."],
                                [os.path.join(_AUDIO_REF_DIR, "example_3.wav"), "Cậu có nhìn thấy không?"],
                                [os.path.join(_AUDIO_REF_DIR, "example_4.wav"), "Tết là dịp mọi người háo hức đón chào một năm mới với nhiều hy vọng và mong ước."]
                            ],
                            inputs=[custom_audio, custom_text],
                            label="Audio mẫu để thử"
                        )
                        gr.HTML(
                            '<p class="evt-help">Kết quả clone chưa ưng ý? Có thể <b>finetune LoRA</b> để đạt chất lượng '
                            'tốt nhất — xem <code>finetune/README.md</code> hoặc '
                            '<a href="https://github.com/hiimkuroshi/EveryVideoTTS/tree/main/finetune" target="_blank" '
                            'rel="noopener noreferrer">hướng dẫn trên GitHub</a>.</p>',
                            padding=False,
                        )

                # Only one generation mode exists; kept hidden because synthesize_speech reads it.
                generation_mode = gr.Radio(["Standard (Một lần)"], value="Standard (Một lần)", label="Chế độ sinh",
                                           visible=False)
                btn_generate = gr.Button("Tạo giọng nói", variant="primary", size="lg", interactive=False,
                                         elem_classes="evt-cta")
                gr.HTML('<p>Tải model ở khung phía trên để bắt đầu.</p>', padding=False, elem_classes="evt-cta-hint")

                with gr.Accordion("Tinh chỉnh nâng cao", open=False, elem_classes="evt-sub-acc"):
                    with gr.Row(equal_height=False):
                        use_batch = gr.Checkbox(
                            value=True,
                            label="Xử lý theo lô (batch)",
                            info="Chạy nhiều đoạn cùng lúc — nên luôn bật để tăng tốc."
                        )
                        max_batch_size_run = gr.Slider(
                            minimum=1, maximum=256, value=128, step=1,
                            label="Batch size",
                            info="Càng lớn càng nhanh. Khoảng 128 đoạn × 64 ký tự dùng hết ~7 GB VRAM."
                        )
                    with gr.Row(equal_height=False):
                        temperature_slider = gr.Slider(
                            minimum=0.1, maximum=1.5, value=1.0, step=0.1,
                            label="Temperature",
                            info="Cao: giàu cảm xúc hơn nhưng dễ lỗi. Thấp: ổn định hơn."
                        )
                        max_chars_chunk_slider = gr.Slider(
                            minimum=64, maximum=512, value=128, step=16,
                            label="Ký tự tối đa mỗi đoạn",
                            info="Đoạn càng ngắn thì xử lý càng nhanh khi tăng batch size."
                        )

                current_mode_state = gr.State("preset_mode")

            # ================================ OUTPUT ================================
            with gr.Column(scale=5, min_width=320, elem_classes="evt-card", elem_id="evt-output"):
                gr.HTML(panel_head("Kết quả", "Nghe thử & tải về"), padding=False)
                status_panel = gr.HTML(render_status(""), padding=False, elem_id="evt-status")
                audio_output = gr.Audio(
                    label="Bản thu",
                    type="filepath",
                    autoplay=True,
                    interactive=False,
                    visible=False,
                    show_share_button=False,
                    waveform_options=_WAVEFORM,
                    elem_id="evt-audio",
                )
                with gr.Row(elem_id="evt-actions"):
                    download_btn = gr.DownloadButton("Tải xuống WAV", variant="primary", visible=False)
                    btn_stop = gr.Button("Dừng", variant="stop", visible=False, interactive=False)
                gr.HTML(footnote_watermark(), padding=False)

    # ================================ EVENTS ================================
    codec_select.change(
        on_codec_change,
        inputs=[codec_select, current_mode_state],
        outputs=[tab_custom, tabs, current_mode_state]
    )

    tab_preset.select(lambda: "preset_mode", outputs=current_mode_state)
    tab_custom.select(lambda: "custom_mode", outputs=current_mode_state)

    custom_audio.change(validate_audio_duration, inputs=[custom_audio], outputs=[cloning_warning_msg])

    def on_backbone_change(choice):
        is_custom = (choice == "Custom Model")
        return gr.update(visible=is_custom)

    backbone_select.change(
        on_backbone_change,
        inputs=[backbone_select],
        outputs=[custom_model_group]
    )

    custom_backbone_model_id.change(
        on_custom_id_change,
        inputs=[custom_backbone_model_id],
        outputs=[custom_backbone_base_model, custom_audio, custom_text]
    )

    btn_load.click(
        fn=load_model_ui,
        inputs=[backbone_select, codec_select, device_choice,
                custom_backbone_model_id, custom_backbone_base_model, custom_backbone_hf_token],
        outputs=[model_status, btn_generate, btn_load, btn_stop, voice_select, tab_preset, tab_custom, tabs,
                 current_mode_state, header_html, model_card],
        show_progress="hidden",
    )

    def _job_started():
        return gr.update(visible=False), gr.update(interactive=True, visible=True), gr.update(interactive=False)

    def _job_finished(audio_path):
        ok = bool(isinstance(audio_path, str) and audio_path and os.path.exists(audio_path))
        return (gr.update(value=audio_path if ok else None, visible=ok),
                gr.update(interactive=False, visible=False),
                gr.update(interactive=model_loaded))

    generate_event = btn_generate.click(
        fn=synthesize_speech_ui,
        inputs=[text_input, voice_select, custom_audio, custom_text, current_mode_state,
                generation_mode, use_batch, max_batch_size_run,
                temperature_slider, max_chars_chunk_slider],
        outputs=[audio_output, status_panel],
        show_progress="hidden",
    )
    btn_generate.click(_job_started, outputs=[download_btn, btn_stop, btn_generate], show_progress="hidden")
    btn_generate.click(None, js="() => { if (window.evtScrollToOutput) window.evtScrollToOutput(); }")
    generate_event.then(_job_finished, inputs=[audio_output], outputs=[download_btn, btn_stop, btn_generate],
                        show_progress="hidden")

    btn_stop.click(fn=None, cancels=[generate_event])
    btn_stop.click(
        lambda: (gr.update(value=None, visible=False), render_status("⏹️ Đã dừng tạo giọng nói."),
                 gr.update(interactive=False, visible=False), gr.update(visible=False),
                 gr.update(interactive=model_loaded)),
        outputs=[audio_output, status_panel, btn_stop, download_btn, btn_generate],
        show_progress="hidden",
    )

    demo.load(
        fn=restore_ui_state_ui,
        outputs=[model_status, btn_generate, btn_stop, header_html, model_card],
        show_progress="hidden",
    )

def main():
    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    is_on_colab = os.getenv("COLAB_RELEASE_TAG") is not None
    share = env_bool("GRADIO_SHARE", default=is_on_colab)

    if server_name == "0.0.0.0" and os.getenv("GRADIO_SHARE") is None:
        share = False

    demo.queue().launch(server_name=server_name, server_port=server_port, share=share, i18n=i18n)

if __name__ == "__main__":
    main()
