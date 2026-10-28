# 🎬 EveryVideoTTS

**Vietnamese text-to-speech & video dubbing studio** by **Tyr**.
Turn text, PDFs and SRT subtitles into natural, perfectly timed Vietnamese voice-over.

Repository: [hiimkuroshi/EveryVideoTTS](https://github.com/hiimkuroshi/EveryVideoTTS)

## ✨ Highlights
- **SRT → voice-over dubbing** — one audio track aligned to every subtitle timestamp, with automatic speaker detection and per-speaker voices (up to 8).
- **Auto Speed Matching (WSOLA)** — overflowing lines are sped up without changing pitch or adding metallic artifacts.
- **GPU-batched generation** — up to 32 lines per batch on CUDA.
- **v3 Turbo, 48 kHz** — 16 built-in voices (Northern, Central, Southern accents, plus Review 1 & Review 2).
- **Instant voice cloning** from a 3–8 s clip, auto-denoised.
- **Emotion cues** *(experimental)*: `[cười]`, `[thở dài]`, `[hắng giọng]`.
- **Torch-free on CPU** (ONNX, int8 by default); PyTorch on GPU.

## 📦 Install

Install from source:

```bash
pip install "git+https://github.com/hiimkuroshi/EveryVideoTTS.git"
```

For an NVIDIA GPU, install a CUDA build of PyTorch first:

```bash
pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
pip install "transformers==4.57.6"
pip install "git+https://github.com/hiimkuroshi/EveryVideoTTS.git"
```

To run the Studio web UI, clone the repo and follow the [README](https://github.com/hiimkuroshi/EveryVideoTTS#installation).

## 🚀 Quick start

```python
from vieneu import Vieneu

tts = Vieneu()  # v3 Turbo, 48 kHz

# Text to speech
audio = tts.infer("Xin chào, đây là EveryVideoTTS.", voice="Trúc Ly")
tts.save(audio, "output.wav")

# SRT dubbing
audio, stats = tts.infer_srt("subtitles.srt", voice="Minh Đức",
                             align_mode="sync", speed_mode="auto_speed_up")
tts.save(audio, "dubbed.wav")

# Voice cloning (PyTorch / GPU install)
audio = tts.infer("Đây là giọng được nhân bản.", ref_audio="my_voice.wav")
```

## 📄 License
- Code: Apache 2.0 — see `LICENSE` and `NOTICE`.
- Models & preset voices (downloaded from Hugging Face): CC BY-NC 4.0, non-commercial use only, with attribution.

## 🙏 Acknowledgements
Built on [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) (Apache 2.0) and its models.

**Made with ❤️ by Tyr for Vietnamese video creators**
