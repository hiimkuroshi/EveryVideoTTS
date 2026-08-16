from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Tuple, Callable
import json
import numpy as np
import logging
from huggingface_hub import hf_hub_download
# PuncNormalizer = sea_g2p.Normalizer luôn bật punc_norm=True (xem phonemize_text).
from vieneu_utils.phonemize_text import PuncNormalizer as Normalizer

# Configure logging
logger = logging.getLogger("Vieneu")


def _load_ref_mono(ref_audio_path: Union[str, Path], target_sr: int) -> np.ndarray:
    """Load a reference clip as mono float32 resampled to ``target_sr``.

    Prefers ``librosa`` when present, but falls back to ``soundfile`` + ``soxr``
    (both core deps) so voice cloning works without the optional ``[gpu]`` extra
    that ships librosa.
    """
    try:
        import librosa
        wav, _ = librosa.load(ref_audio_path, sr=target_sr, mono=True)
        return wav
    except ImportError:
        import soundfile as sf
        import soxr
        wav, sr = sf.read(str(ref_audio_path), dtype="float32", always_2d=False)
        if wav.ndim > 1:  # downmix to mono
            wav = wav.mean(axis=1)
        if sr != target_sr:
            wav = soxr.resample(wav, sr, target_sr)
        return np.ascontiguousarray(wav, dtype=np.float32)

class BaseVieneuTTS(ABC):
    """
    Abstract base class for VieNeu-TTS implementations.
    Provides shared functionality for voice management and common operations.
    """

    def __init__(self, codec_repo: Optional[str] = None, codec_device: str = "cpu"):
        self.sample_rate = 24_000
        self.max_context = 2048
        self.hop_length = 480

        # Default streaming parameters
        self.streaming_overlap_frames = 1
        self.streaming_frames_per_chunk = 50
        self.streaming_lookforward = 5
        self.streaming_lookback = 50
        self.streaming_stride_samples = self.streaming_frames_per_chunk * self.hop_length

        self.assets_dir = Path(__file__).parent / "assets"
        self._preset_voices: Dict[str, Any] = {}
        self._default_voice: Optional[str] = None
        self.normalizer = Normalizer()
        self._ref_phoneme_cache: Dict[str, str] = {}

        # Watermarker placeholder
        self.watermarker = None
        self._init_watermarker()

        if codec_repo:
            self._load_codec(codec_repo, codec_device)

    def _load_codec(self, codec_repo: str, codec_device: str) -> None:
        """Universal codec loader for all backends."""
        logger.info(f"📦 Loading codec from: {codec_repo} on {codec_device} ...")

        if any(x in codec_repo.lower() for x in ["onnx", "vieneu-codec"]) or codec_repo == "neuphonic/neucodec-onnx-decoder-int8":
            if codec_device != "cpu":
                logger.warning("⚠️ ONNX decoder only runs on CPU. Ignoring device selection.")
            try:
                from .utils import NeuCodecOnnx
                self.codec = NeuCodecOnnx.from_pretrained(codec_repo)
                self._is_onnx_codec = True
                return
            except Exception as e:
                logger.warning(f"Failed to load standalone ONNX decoder: {e}. Trying via neucodec package...")
                try:
                    from neucodec import NeuCodecOnnxDecoder
                    self.codec = NeuCodecOnnxDecoder.from_pretrained(codec_repo)
                    self._is_onnx_codec = True
                    return
                except ImportError:
                    raise ImportError(
                        "The 'onnxruntime' package is required for ONNX decoder. \n"
                        "Please install it via: pip install onnxruntime"
                    ) from e

        # For PyTorch codecs, check for torch first
        try:
            import torch
            from neucodec import NeuCodec, DistillNeuCodec
            
            # Check MPS
            if codec_device == "mps" and not torch.backends.mps.is_available():
                logger.warning("⚠️ MPS not available for codec, falling back to CPU")
                codec_device = "cpu"

            if codec_repo == "neuphonic/neucodec":
                self.codec = NeuCodec.from_pretrained(codec_repo)
            elif codec_repo == "neuphonic/distill-neucodec":
                self.codec = DistillNeuCodec.from_pretrained(codec_repo)
            else:
                raise ValueError(f"Unrecognized codec repository: {codec_repo}")

            self.codec.eval().to(codec_device)
        except ImportError:
            raise ImportError(
                f"Codec '{codec_repo}' requires PyTorch. \n"
                "To remain lightweight in Remote mode, please use 'neuphonic/neucodec-onnx-decoder-int8'. \n"
                "Or install torch via: pip install vieneu[gpu]"
            )


    def _init_watermarker(self) -> None:
        """Initialize optional audio watermarker."""
        try:
            import perth
            self.watermarker = perth.PerthImplicitWatermarker()
            logger.info("🔒 Audio watermarking initialized (Perth)")
        except (ImportError, AttributeError):
            self.watermarker = None

    def _load_voices(self, backbone_repo: Optional[str], hf_token: Optional[str] = None, clear_existing: bool = False) -> None:
        """Unified voice loading for Local and Remote paths."""
        if not backbone_repo:
            return

        path_obj = Path(backbone_repo)
        if path_obj.exists():
            # Local Path (Dir or File)
            if path_obj.is_dir():
                json_path = path_obj / "voices.json"
            else:
                json_path = path_obj.parent / "voices.json"

            if json_path.exists():
                self._load_voices_from_file(json_path, clear_existing=clear_existing)
            else:
                if clear_existing:
                     self._preset_voices.clear()
                logger.warning(f"Validation Warning: Local path '{backbone_repo}' missing 'voices.json'.")
                logger.warning(f"Falling back to Custom Voice Cloning mode.")
        else:
            # Remote Repo
            if clear_existing:
                self._preset_voices.clear()

            try:
                self._load_voices_from_repo(backbone_repo, hf_token)
            except Exception as e:
                logger.warning(f"Could not load voices from repo '{backbone_repo}': {e}")
                logger.warning(f"Falling back to Custom Voice Cloning mode.")

    def _load_voices_from_file(self, file_path: Path, clear_existing: bool = False) -> None:
        """Load voices from a local JSON file."""
        try:
            if not file_path.exists():
                logger.error(f"Voice file not found: {file_path}")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in voice file {file_path}: {e}")
                    return

            if "presets" in data:
                if clear_existing:
                    self._preset_voices.clear()
                    logger.info("🧹 Cleared existing voices for replacement")

                # Merge into existing presets
                self._preset_voices.update(data["presets"])
                logger.info(f"📢 Loaded {len(data['presets'])} voices from {file_path.name}")

            # Update default voice if provided
            if "default_voice" in data and data["default_voice"]:
                self._default_voice = data["default_voice"]

        except Exception as e:
            logger.error(f"Failed to load voices from {file_path}: {e}")

    def _load_voices_from_repo(self, repo_id: str, hf_token: Optional[str] = None) -> None:
        """Download and load voices.json from a HuggingFace repo."""
        voices_file = None
        try:
            # 1. Try normal download (checks for updates from server)
            voices_file = hf_hub_download(
                repo_id=repo_id,
                filename="voices.json",
                token=hf_token,
                repo_type="model"
            )
        except Exception:
            # 2. Network error? Try to use cached version if available
            logger.warning(f"Network check failed for voices.json. Trying local cache...")
            try:
                voices_file = hf_hub_download(
                    repo_id=repo_id,
                    filename="voices.json",
                    token=hf_token,
                    repo_type="model",
                    local_files_only=True
                )
                logger.info(f"✅ Using cached voices.json")
            except Exception:
                # 3. No cache available either
                pass

        if voices_file:
            self._load_voices_from_file(Path(voices_file))
        else:
            logger.warning(f"Repository '{repo_id}' is missing 'voices.json'. Falling back to Custom Voice mode.")

    def list_preset_voices(self) -> List[tuple[str, str]]:
        """List available preset voices as (description, id)."""
        return [
            (v.get("description", k) if isinstance(v, dict) else str(v), k)
            for k, v in self._preset_voices.items()
        ]

    def get_preset_voice(self, voice_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get reference codes and text for a preset voice.

        Args:
            voice_name: Name of voice. If None, uses default_voice.

        Returns:
            dict: { 'codes': Union[np.ndarray, 'torch.Tensor'], 'text': str }
        """
        if voice_name is None:
            voice_name = self._default_voice
            if voice_name is None:
                if self._preset_voices:
                    voice_name = next(iter(self._preset_voices))
                else:
                    raise ValueError("No voice specified and no preset voices available.")

        if voice_name not in self._preset_voices:
            matched = None
            for k in self._preset_voices:
                if k.lower() == str(voice_name).lower():
                    matched = k
                    break
            if matched:
                voice_name = matched
            else:
                raise ValueError(f"Voice '{voice_name}' not found. Available: {self.list_preset_voices()}")

        voice_data = self._preset_voices[voice_name]
        codes = voice_data["codes"]
        
        # Only convert to torch if explicitly requested or if we're not in turbo mode
        if isinstance(codes, list):
            if codes and isinstance(codes[0], float):
                codes = np.array(codes, dtype=np.float32)
            else:
                # Là integer token sequence (Standard mode)
                try:
                    import torch
                    codes = torch.tensor(codes, dtype=torch.long)
                except ImportError:
                    codes = np.array(codes, dtype=np.int64)

        return {"codes": codes, "text": voice_data["text"]}

    def get_ref_phonemes(self, ref_text: str) -> str:
        """
        Get phonemized version of reference text, using cache if available.
        """
        if ref_text not in self._ref_phoneme_cache:
            from vieneu_utils.phonemize_text import phonemize_with_dict
            self._ref_phoneme_cache[ref_text] = phonemize_with_dict(ref_text)
        return self._ref_phoneme_cache[ref_text]

    def save(self, audio: np.ndarray, output_path: Union[str, Path]) -> None:
        """Save audio waveform to a file."""
        import soundfile as sf
        sf.write(str(output_path), audio, self.sample_rate)

    def encode_reference(self, ref_audio_path: Union[str, Path]) -> Union[np.ndarray, 'torch.Tensor']:
        """
        Encode reference audio to codes.

        Args:
            ref_audio_path: Path to the reference audio file.

        Returns:
            Union[np.ndarray, torch.Tensor]: Encoded codes.
        """
        wav = _load_ref_mono(ref_audio_path, target_sr=16000)

        # If we have an ONNX encoder or specialized turbo encoder, handle it here
        # For now, default backends still use torch
        try:
            import torch
            wav_tensor = torch.from_numpy(wav).float().unsqueeze(0).unsqueeze(0)  # [1, 1, T]

            # Ensure device and dtype compatibility
            if hasattr(self.codec, "device"):
                wav_tensor = wav_tensor.to(self.codec.device)

            with torch.no_grad():
                ref_codes = self.codec.encode_code(audio_or_path=wav_tensor).squeeze(0).squeeze(0)
            return ref_codes
        except ImportError:
            raise ImportError("Torch is required for encode_reference in the current backend. Please install torch or use a backend that supports standalone encoding.")

    def _decode(self, codes_str: str) -> np.ndarray:
        """
        Decode speech tokens to audio waveform.

        Args:
            codes_str: String containing speech tokens.

        Returns:
            np.ndarray: Decoded audio waveform.
        """
        from .utils import extract_speech_ids
        speech_ids = extract_speech_ids(codes_str)

        if len(speech_ids) == 0:
            raise ValueError("No valid speech tokens found in the output.")

        # Onnx decode
        if getattr(self, "_is_onnx_codec", False):
            codes = np.array(speech_ids, dtype=np.int32)[np.newaxis, np.newaxis, :]
            recon = self.codec.decode_code(codes)
        # Torch decode
        else:
            try:
                import torch
                with torch.no_grad():
                    codes = torch.tensor(speech_ids, dtype=torch.long)[None, None, :]
                    if hasattr(self.codec, "device"):
                        codes = codes.to(self.codec.device)

                    recon = self.codec.decode_code(codes)
                    if hasattr(recon, "cpu"):
                        recon = recon.cpu()
                    if hasattr(recon, "numpy"):
                        recon = recon.numpy()
            except ImportError:
                raise ImportError("Torch is required for the current codec backend. Please install torch or use an ONNX-based codec.")


        return recon[0, 0, :]

    def _resolve_ref_voice(
        self,
        voice: Optional[Union[str, Dict[str, Any]]] = None,
        ref_audio: Optional[Union[str, Path]] = None,
        ref_codes: Optional[Union[np.ndarray, 'torch.Tensor']] = None,
        ref_text: Optional[str] = None
    ) -> tuple[Union[np.ndarray, 'torch.Tensor'], str]:
        """Resolve reference voice codes and text."""
        if voice is not None:
            if isinstance(voice, str):
                try:
                    voice_dict = self.get_preset_voice(voice)
                except Exception:
                    voice_dict = {}
            elif isinstance(voice, dict):
                voice_dict = voice
            else:
                voice_dict = {}
            ref_codes = voice_dict.get('codes', ref_codes)
            ref_text = voice_dict.get('text', ref_text)

        if ref_audio is not None and ref_codes is None:
            ref_codes = self.encode_reference(ref_audio)
        elif self._default_voice and (ref_codes is None or ref_text is None):
            try:
                voice_data = self.get_preset_voice(None)
                ref_codes = voice_data.get('codes', ref_codes)
                ref_text = voice_data.get('text', ref_text)
            except Exception:
                pass

        if ref_codes is None or ref_text is None:
            raise ValueError("Must provide either 'voice' (preset name or dict) or both 'ref_codes' and 'ref_text'.")

        return ref_codes, ref_text

    def _apply_watermark(self, wav: np.ndarray) -> np.ndarray:
        """Apply watermark to audio if enabled."""
        if self.watermarker:
            return self.watermarker.apply_watermark(wav, sample_rate=self.sample_rate)
        return wav

    def to_list(self, codes: Any) -> List[int]:
        """Convert reference codes (Tensor, Array, List) to a Python list of integers."""
        if isinstance(codes, list):
            return codes
        if isinstance(codes, np.ndarray):
            return codes.flatten().tolist()

        # Check for torch without importing it at module level
        try:
            import torch
            if isinstance(codes, torch.Tensor):
                return codes.flatten().tolist()
        except ImportError:
            pass

        # Fallback for other array-like types
        if hasattr(codes, "tolist"):
            return codes.flatten().tolist() if hasattr(codes, "flatten") else codes.tolist()

        return list(codes)

    def _format_prompt(
        self,
        ref_codes: Any,
        ref_text: str,
        input_text: str,
        ref_phonemes: Optional[str] = None,
        input_phonemes: Optional[str] = None,
        use_chat_format: bool = False,
        emotion_tag: Optional[str] = None
    ) -> str:
        """
        Format the prompt for the TTS model.
        Common implementation for LMDeploy (Fast) and Remote backends.
        Standard backend uses a specialized chat template via tokenizer.

        Args:
            use_chat_format: If True, wraps the prompt with chat-style user/assistant
                             tokens (used by VieNeu-TTS GPU model). If False (default),
                             returns a compact prompt without those wrappers.
        """
        ref_codes_list = self.to_list(ref_codes)

        # Import inside method to avoid potential circular dependencies between
        # base TTS and phonemization utilities.
        from vieneu_utils.phonemize_text import phonemize_with_dict

        ref_text_phones = ref_phonemes if ref_phonemes else self.get_ref_phonemes(ref_text)
        input_text_phones = input_phonemes if input_phonemes else phonemize_with_dict(input_text, skip_normalize=True)
        codes_str = "".join([f"<|speech_{idx}|>" for idx in ref_codes_list])

        emotion_prefix = emotion_tag if emotion_tag else ""

        if use_chat_format:
            return (
                f"user: Convert the text to speech:<|TEXT_PROMPT_START|>{emotion_prefix}{ref_text_phones} {input_text_phones}"
                f"<|TEXT_PROMPT_END|>\nassistant:<|SPEECH_GENERATION_START|>{codes_str}"
            )
        return (
            f"<|TEXT_PROMPT_START|>{emotion_prefix}{ref_text_phones} {input_text_phones}"
            f"<|TEXT_PROMPT_END|><|SPEECH_GENERATION_START|>{codes_str}"
        )

    def infer_srt(
        self,
        srt_input: Union[str, Path],
        voice: Optional[Union[str, dict]] = None,
        ref_audio: Optional[Union[str, Path]] = None,
        speaker_map: Optional[Dict[str, Union[str, dict]]] = None,
        align_mode: str = "sync",
        speed_mode: str = "auto_speed_up",
        max_speed_factor: float = 2.0,
        min_speed_factor: float = 0.8,
        speed_threshold: float = 1.25,
        lead_in_silence_s: float = 0.0,
        apply_watermark: bool = True,
        progress_callback: Optional[Any] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Synthesize audio from an SRT subtitle string or file.

        Args:
            srt_input: Path to .srt file or raw SRT string.
            voice: Default voice name or preset dictionary.
            ref_audio: Audio file to clone voice from (if not using voice preset).
            speaker_map: Optional mapping of speaker names in subtitle to voice presets.
            align_mode: "sync" (Strict time-alignment with silence padding) or "sequential".
            speed_mode: Speed adjustment mode: "auto_speed_up" (Default), "fit_exact", "none".
            max_speed_factor: Maximum speed-up ratio allowed (default 2.0x).
            min_speed_factor: Minimum speed-down ratio allowed (default 0.8x).
            speed_threshold: Threshold ratio before flagging that spoken audio exceeds subtitle slot.
            lead_in_silence_s: Initial silence offset before first subtitle (seconds).
            apply_watermark: Apply watermark to the final waveform.
            progress_callback: Callback `(current_idx, total_count, subtitle_item, start_s, duration_s)`.
            **kwargs: Extra parameters passed to `self.infer(...)`.

        Returns:
            Tuple[np.ndarray, dict]: (final_waveform, statistics_and_timeline_info)
        """
        from vieneu_utils.srt_utils import parse_srt, build_srt_audio_timeline

        items = parse_srt(srt_input)
        if not items:
            return np.array([], dtype=np.float32), {"total_items": 0, "total_duration_s": 0.0, "subtitles_info": []}

        def _infer_item(item):
            item_voice = voice
            item_ref_audio = ref_audio
            if speaker_map and item.speaker:
                mapped = speaker_map.get(item.speaker.strip()) or speaker_map.get(item.speaker.strip().lower())
                if mapped:
                    if isinstance(mapped, (str, Path)) and (str(mapped).endswith((".wav", ".mp3")) or Path(mapped).exists()):
                        item_ref_audio = str(mapped)
                        item_voice = None
                    else:
                        item_voice = mapped
                        item_ref_audio = None

            return self.infer(
                item.text,
                voice=item_voice,
                ref_audio=item_ref_audio,
                apply_watermark=False,
                **kwargs,
            )

        final_wav, stats = build_srt_audio_timeline(
            items=items,
            infer_chunk_fn=_infer_item,
            sample_rate=self.sample_rate,
            align_mode=align_mode,
            speed_mode=speed_mode,
            max_speed_factor=max_speed_factor,
            min_speed_factor=min_speed_factor,
            speed_threshold=speed_threshold,
            lead_in_silence_s=lead_in_silence_s,
            progress_callback=progress_callback,
        )

        if apply_watermark and len(final_wav) > 0:
            final_wav = self._apply_watermark(final_wav)

        return final_wav, stats

    def save_srt_audio(
        self,
        srt_input: Union[str, Path],
        output_path: Union[str, Path],
        voice: Optional[Union[str, dict]] = None,
        ref_audio: Optional[Union[str, Path]] = None,
        speaker_map: Optional[Dict[str, Union[str, dict]]] = None,
        align_mode: str = "sync",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Synthesize audio from an SRT file and save directly to output_path."""
        final_wav, stats = self.infer_srt(
            srt_input=srt_input,
            voice=voice,
            ref_audio=ref_audio,
            speaker_map=speaker_map,
            align_mode=align_mode,
            **kwargs,
        )
        self.save(final_wav, output_path)
        stats["output_path"] = str(output_path)
        return stats

    @abstractmethod
    def infer(self, text: str, apply_watermark: bool = True, **kwargs: Any) -> np.ndarray:
        """Main inference method for single text."""
        pass

    @abstractmethod
    def infer_batch(self, texts: List[str], apply_watermark: bool = True, **kwargs: Any) -> List[np.ndarray]:
        """Main inference method for batch processing."""
        pass

    def close(self) -> None:
        """Release resources."""
        pass

    def __enter__(self) -> 'BaseVieneuTTS':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
