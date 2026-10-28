<div align="center">

# 🎬 EveryVideoTTS

**Vietnamese text-to-speech & video dubbing studio.**
Turn text, PDFs and SRT subtitles into natural, perfectly timed Vietnamese voice-over.

[![GitHub](https://img.shields.io/badge/GitHub-EveryVideoTTS-181717?logo=github)](https://github.com/hiimkuroshi/EveryVideoTTS)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%20–%203.13-3776AB?logo=python&logoColor=white)](#installation)
[![Audio](https://img.shields.io/badge/Audio-48%20kHz-8B5CF6)](#models)

**English** · [Tiếng Việt](README.vi.md)

</div>

![EveryVideoTTS Studio](docs/images/studio-main.png)

## ✨ Highlights

- 🎬 **SRT → voice-over dubbing** — load a `.srt`/`.txt` subtitle file and get one audio track aligned to every timestamp, ready to drop onto your video timeline.
- 👥 **Multi-speaker subtitles** — speakers are detected automatically (`Name: line`, `[Name] line`, `<v Name>line`), and each one (up to 8) can get its own voice.
- ⚡ **Auto Speed Matching (WSOLA)** — when a line is longer than its subtitle slot, it is sped up without changing pitch, using time-domain WSOLA instead of a phase vocoder, so there is no metallic buzz.
- 🚀 **GPU-batched generation** — up to 32 subtitle lines per batch on CUDA, grouped by length to cut padding.
- 🎙️ **16 built-in voices** on v3 Turbo (48 kHz), covering Northern, Central and Southern accents, including the new **Review 1** and **Review 2** voices.
- 🦜 **Instant voice cloning** from a 3–8 s clip, with automatic denoising.
- 📄 **Long text & PDF reading**, plus a multi-speaker **conversation / podcast** mode.
- 😄 **Emotion cues** *(experimental)*: `[cười]`, `[thở dài]`, `[hắng giọng]` inline in the text.
- 💻 **Runs anywhere** — torch-free on CPU (ONNX, int8 by default), PyTorch on NVIDIA GPUs and Apple Silicon, plus an Intel Arc (XPU) edition.
- 🎨 **Studio UI** — redesigned Gradio interface with light and dark themes.

## 📌 Table of Contents

1. [Installation](#installation)
2. [Using the Studio](#studio)
3. [SRT dubbing](#srt)
4. [Python SDK](#sdk)
5. [Self-hosted API server (Docker)](#docker)
6. [Models & voices](#models)
7. [Author & license](#author)
8. [Acknowledgements](#acknowledgements)

---

## 🦜 1. Installation <a name="installation"></a>

**Requirements:** Python 3.10–3.13 (3.12 recommended), Windows / Linux / macOS (Apple Silicon). A GPU is optional: NVIDIA with CUDA ≥ 12.8.

1. **Install `uv`** (fast Python package manager):
   ```bash
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

   # Linux / macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repo:**
   ```bash
   git clone https://github.com/hiimkuroshi/EveryVideoTTS.git
   cd EveryVideoTTS
   ```

3. **Install dependencies — pick one:**

   | Setup | Command | Notes |
   |---|---|---|
   | **CPU / macOS** *(default)* | `uv sync` | Torch-free. Runs v3 Turbo on ONNX Runtime (int8). On Apple Silicon this is faster than the MPS build for v3 Turbo. |
   | **NVIDIA GPU** | `uv sync --group gpu` | Adds PyTorch. Needed for batched SRT dubbing and voice cloning. |
   | **+ PDF reading** | add `--extra pdf` | e.g. `uv sync --group gpu --extra pdf` |
   | **Intel Arc (Windows)** | `setup_xpu_uv.bat`, then `run_xpu.bat` | Separate XPU edition of the Studio. |

4. **Start the Studio:**
   ```bash
   uv run vieneu-web
   ```
   Open `http://127.0.0.1:7860`. Models are downloaded from Hugging Face automatically the first time you load them.

---

## 🎛️ 2. Using the Studio <a name="studio"></a>

1. **Load a model** — pick a *Backbone* (on CPU, `VieNeu-TTS-v3-Turbo (int8)` is the fastest) and a *Device*, then click **Tải Model**.
2. **🦜 Đọc truyện (Read text)** — paste text or extract it from a PDF, choose a preset voice or switch to **Voice Cloning**, then click **Bắt đầu**.
3. **🎬 Lồng tiếng SRT (SRT dubbing)** — see the next section.
4. **🎭 Hội thoại (Conversation)** — appears when the loaded model supports multi-speaker dialogue. Write a script as `Name: line`, assign a voice to each character and set the pause between turns.

---

## 🎬 3. SRT dubbing <a name="srt"></a>

![SRT dubbing tab](docs/images/studio-srt.png)

1. Upload a `.srt` / `.txt` file (or paste the subtitles) and click **Quét & Phân tích SRT** to check the lines and detect speakers.
2. Choose the main voice (preset or cloned). Under **Phân vai nhân vật**, optionally give each detected speaker their own voice.
3. Set the timing options, then click **Bắt đầu lồng tiếng SRT**.

| Option | Values | What it does |
|---|---|---|
| Timeline mode | **Strict Sync** *(default)* / Sequential | Strict Sync starts every line at its timestamp and fills the gaps with silence (if a line still runs over, the next one follows right after it). Sequential reads the lines back to back and keeps the original gaps between subtitles. |
| Lead-in | 0–5 s | Silence added before the first line. |
| Auto Speed Matching | **Auto speed-up** *(default)* / Fit exactly / Keep 1.0× | Auto speed-up only speeds up lines that overflow their slot. Fit exactly speeds up or slows down (to 0.8× at most) every line to match its slot. Keep 1.0× leaves speed untouched. |
| Max speed | 1.1–3.0× (default 2.0×) | Upper limit for speed-up, so speech stays intelligible. |

The result is a single WAV track (48 kHz with v3 Turbo) that lines up with your video.

---

## 📦 4. Python SDK <a name="sdk"></a>

The engine ships as the `vieneu` Python package inside this repo. Run your scripts from the project with `uv run python your_script.py`, or install it into another environment from source:

```bash
pip install "git+https://github.com/hiimkuroshi/EveryVideoTTS.git"
```

### Text to speech

```python
from vieneu import Vieneu

tts = Vieneu()  # v3 Turbo, 48 kHz. CPU → ONNX int8, CUDA → PyTorch (auto-detected)

audio = tts.infer("Xin chào, đây là EveryVideoTTS.", voice="Trúc Ly")
tts.save(audio, "output.wav")

for label, voice_id in tts.list_preset_voices():
    print(label, voice_id)
```

### SRT dubbing

```python
from vieneu import Vieneu

tts = Vieneu()
audio, stats = tts.infer_srt(
    "examples/sample.srt",
    voice="Minh Đức",                                       # default voice
    speaker_map={"Phương": "Trúc Ly", "Dũng": "Xuân Vĩnh"},  # optional, per speaker
    align_mode="sync",            # "sync" or "sequential"
    speed_mode="auto_speed_up",   # "auto_speed_up", "fit_exact" or "none"
    max_speed_factor=2.0,
)
tts.save(audio, "dubbed.wav")
print(f"{stats.get('total_duration_s', 0):.1f}s of audio")
```

A full runnable example is in [`examples/srt_dubbing_example.py`](examples/srt_dubbing_example.py).

### Voice cloning

```python
audio = tts.infer("Đây là giọng được nhân bản.", ref_audio="my_voice.wav")  # 3–8 s clip, auto-denoised

tts.add_voice("Giọng của tôi", "my_voice.wav")   # save once…
audio = tts.infer("Dùng lại giọng đã lưu.", voice="Giọng của tôi")  # …reuse by name
tts.save_voices()                                # keep it for the next session
```

> `denoise`, `add_voice` and voice cloning need the PyTorch (GPU) install. Built-in voices work everywhere.

### Emotion cues, batching and streaming

```python
# Emotion cues (experimental)
audio = tts.infer("Nghe hay quá đi [cười]. Để mình nói tiếp [hắng giọng].", voice="Trúc Ly")

# Many texts in one batched pass (big speed-up on CUDA; runs sequentially on CPU)
audios = tts.infer_batch(["Câu thứ nhất.", "Câu thứ hai."], voice="Minh Đức")

# Real-time streaming (ONNX/CPU engine, audio arrives frame by frame)
stream_tts = Vieneu(backend="onnx")
for chunk in stream_tts.infer_stream("Xin chào các bạn!", voice="Minh Đức"):
    ...  # np.float32 @ 48 kHz — play or write as it arrives
```

A FastAPI streaming demo is in [`apps/web_stream.py`](apps/web_stream.py): `uv run vieneu-stream` → `http://127.0.0.1:8001`.

---

## 🐳 5. Self-hosted API server (Docker) <a name="docker"></a>

Build the LMDeploy-based server image from this repo and run it on an NVIDIA GPU ([NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) required):

```bash
make docker-build-serve
docker run --gpus all -p 23333:23333 -v huggingface_cache:/root/.cache/huggingface everyvideotts:serve --model pnnbao-ump/VieNeu-TTS-v2 --tunnel
```

Then connect from anywhere with the SDK (`pip install "vieneu[legacy] @ git+https://github.com/hiimkuroshi/EveryVideoTTS.git"`):

```python
from vieneu import Vieneu

tts = Vieneu(mode="remote", api_base="http://your-server-ip:23333/v1", model_name="pnnbao-ump/VieNeu-TTS-v2")
tts.save(tts.infer("Xin chào từ server."), "remote.wav")
```

More options (Docker Compose, production setup, pushing to your own registry): [`docs/Deploy.md`](docs/Deploy.md) · full remote example: [`examples/main_remote.py`](examples/main_remote.py).

---

## 🔬 6. Models & voices <a name="models"></a>

EveryVideoTTS runs on the VieNeu-TTS model family. Models are downloaded from Hugging Face the first time they are loaded.

| Model | Engine | Device | Sample rate | Used for |
|---|---|---|---|---|
| **VieNeu-TTS-v3-Turbo** *(default)* | ONNX (CPU) / PyTorch (GPU) | CPU / GPU | 48 kHz | Preset voices, cloning, emotion cues, SRT dubbing, conversation |
| **VieNeu-TTS-v2** | PyTorch (+ LMDeploy) | GPU | 24 kHz | Bilingual En–Vi, podcast mode, Docker server |
| **VieNeu-TTS (v1)** | PyTorch | GPU | 24 kHz | Stable Vietnamese-only voice |

**Built-in voices (v3 Turbo):**

| Region | Male | Female |
|---|---|---|
| Northern | Minh Đức *(default)*, Phạm Tuyên, Thanh Bình | Trúc Ly, Ngọc Linh, Đoan Trang, Mai Anh |
| Central | Quang Sơn | Ngọc Trân |
| Southern | Thái Sơn, Xuân Vĩnh, Minh Triết | Thục Đoan, Thùy Dung |
| AI assistant | Review 1, Review 2 | — |

The v2 model has 8 presets: Bình, Tuyên, Vĩnh, Đoan, Ly, Ngọc, Review 1 and Review 2.

To fine-tune your own voice with LoRA, see [`finetune/README.md`](finetune/README.md). To load custom or LoRA models in the Studio, see [`docs/CUSTOM_MODEL_USAGE.md`](docs/CUSTOM_MODEL_USAGE.md).

---

## 👤 7. Author & license <a name="author"></a>

- **Author:** **Tyr** — [github.com/hiimkuroshi](https://github.com/hiimkuroshi)
- **Repository:** [hiimkuroshi/EveryVideoTTS](https://github.com/hiimkuroshi/EveryVideoTTS)
- **Bug reports & ideas:** [GitHub Issues](https://github.com/hiimkuroshi/EveryVideoTTS/issues)
- **Code license:** [Apache 2.0](LICENSE), see also [NOTICE](NOTICE).
- **Models & preset voices:** CC BY-NC 4.0, for **non-commercial use only**, with attribution. They are not covered by the Apache license of this repo.

### Citation

```bibtex
@misc{everyvideotts2026,
  title        = {EveryVideoTTS: Advanced Vietnamese Text-to-Speech & Video SRT Dubbing Studio},
  author       = {Tyr},
  year         = {2026},
  howpublished = {\url{https://github.com/hiimkuroshi/EveryVideoTTS}}
}
```

### 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=hiimkuroshi/EveryVideoTTS&type=Date)](https://star-history.com/#hiimkuroshi/EveryVideoTTS&Date)

---

## 🙏 Acknowledgements <a name="acknowledgements"></a>

EveryVideoTTS is built on [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) (Apache 2.0) and uses its models. Audio coding uses [neucodec](https://huggingface.co/neuphonic/neucodec) and [MOSS-Audio-Tokenizer-Nano](https://huggingface.co/OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano); text normalization and phonemization use [sea-g2p](https://github.com/pnnbao97/sea-g2p).

<div align="center">

**Made with ❤️ by Tyr for Vietnamese video creators**

</div>
