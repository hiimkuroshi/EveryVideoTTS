"""
SRT (Subtitle) Parsing and Audio Timeline Alignment Utility for VieNeu-TTS.
===========================================================================
Pure Python implementation with no external subtitle parser dependency.
Supports:
- Timestamp parsing (HH:MM:SS,mmm and HH:MM:SS.mmm).
- Subtitle cleaning (strips HTML tags <i>, <b>, <font>, ASS tags {\\an8}, etc.).
- Speaker extraction (e.g. "Nam: Lời thoại", "[Nam] Lời thoại", "<v Nam>...").
- Audio timeline synchronization with accurate silence padding and cascade alignment.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np

# Regex for timestamps: HH:MM:SS,mmm or HH:MM:SS.mmm
RE_TIMESTAMP = re.compile(
    r"(?:(\d{1,2}):)?(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(?:(\d{1,2}):)?(\d{2}):(\d{2})[,.](\d{3})"
)

# HTML / Subtitle tag cleaner
RE_HTML_TAGS = re.compile(r"<[^>]+>")
RE_ASS_TAGS = re.compile(r"\{[^\}]+\}")

# Speaker detection regexes:
# 1. "Name: Text" or "Name:  Text"
# 2. "[Name] Text" or "(Name) Text"
# 3. "<v Name>Text</v>"
RE_SPEAKER_COLON = re.compile(r"^([A-ZÀ-Ỵa-zà-ỹ0-9_ -]{1,30})\s*:\s*(.+)$", re.DOTALL)
RE_SPEAKER_BRACKET = re.compile(r"^[\[\(]([A-ZÀ-Ỵa-zà-ỹ0-9_ -]{1,30})[\]\)]\s*(.+)$", re.DOTALL)
RE_SPEAKER_VOICE_TAG = re.compile(r"^<v\s+([^>]+)>(.*)(?:</v>)?$", re.IGNORECASE | re.DOTALL)


@dataclass
class SubtitleItem:
    """Represents a single subtitle entry."""
    index: int
    start_ms: int
    end_ms: int
    text: str
    speaker: Optional[str] = None
    raw_text: str = ""

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)

    @property
    def duration_s(self) -> float:
        return self.duration_ms / 1000.0

    @property
    def start_str(self) -> str:
        return format_timestamp(self.start_ms)

    @property
    def end_str(self) -> str:
        return format_timestamp(self.end_ms)


def parse_timestamp_part(hours: Optional[str], minutes: str, seconds: str, millis: str) -> int:
    """Convert time components to milliseconds."""
    h = int(hours) if hours else 0
    m = int(minutes)
    s = int(seconds)
    ms = int(millis)
    return (h * 3600 + m * 60 + s) * 1000 + ms


def parse_timestamp_string(ts_str: str) -> int:
    """Parse timestamp string like '00:01:23,456' or '01:02:03.500' into milliseconds."""
    ts_str = str(ts_str).strip()
    m = re.match(r"(?:(\d{1,2}):)?(\d{2}):(\d{2})[,.](\d{3})", ts_str)
    if not m:
        return 0
    return parse_timestamp_part(m.group(1), m.group(2), m.group(3), m.group(4))


def format_timestamp(ms: int) -> str:
    """Format milliseconds into SRT timestamp format: HH:MM:SS,mmm."""
    if ms < 0:
        ms = 0
    total_seconds = ms // 1000
    millis = ms % 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def clean_subtitle_text(raw_text: str) -> Tuple[str, Optional[str]]:
    """
    Clean formatting tags and extract speaker if present.
    Returns: (cleaned_text, speaker_name_or_None)
    """
    text = raw_text.strip()
    speaker = None

    # Check for <v Speaker> tag first
    m_vtag = RE_SPEAKER_VOICE_TAG.match(text)
    if m_vtag:
        speaker = m_vtag.group(1).strip()
        text = m_vtag.group(2)

    # Strip HTML and ASS tags
    text = RE_HTML_TAGS.sub("", text)
    text = RE_ASS_TAGS.sub("", text)

    # Normalize whitespace & newlines inside subtitle
    text = " ".join(text.split()).strip()

    # Check for speaker prefix if not already found
    if not speaker:
        m_bracket = RE_SPEAKER_BRACKET.match(text)
        if m_bracket:
            speaker = m_bracket.group(1).strip()
            text = m_bracket.group(2).strip()
        else:
            m_colon = RE_SPEAKER_COLON.match(text)
            if m_colon:
                possible_spk = m_colon.group(1).strip()
                # Exclude strings that look like times or URLs
                if not re.search(r"https?|www|\d{2}:\d{2}", possible_spk, re.IGNORECASE):
                    speaker = possible_spk
                    text = m_colon.group(2).strip()

    return text, speaker


def parse_srt(content_or_filepath: Union[str, Path]) -> List[SubtitleItem]:
    """
    Parse an SRT string or file into a list of SubtitleItem objects.
    """
    if isinstance(content_or_filepath, Path) or (isinstance(content_or_filepath, str) and os.path.exists(content_or_filepath)):
        path = Path(content_or_filepath)
        raw_content = ""
        for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1258", "latin-1"):
            try:
                raw_content = path.read_text(encoding=encoding)
                break
            except Exception:
                continue
    else:
        raw_content = str(content_or_filepath)

    # Normalize line endings
    raw_content = raw_content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw_content:
        return []

    # Split subtitle blocks by double newlines
    blocks = re.split(r"\n\s*\n", raw_content)
    items: List[SubtitleItem] = []
    fallback_index = 1

    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue

        # Find timestamp line
        ts_line_idx = -1
        m_ts = None
        for idx, line in enumerate(lines):
            m = RE_TIMESTAMP.search(line)
            if m:
                ts_line_idx = idx
                m_ts = m
                break

        if not m_ts:
            continue

        # Parse Index
        if ts_line_idx > 0 and lines[0].isdigit():
            idx_num = int(lines[0])
        else:
            idx_num = fallback_index
        fallback_index = idx_num + 1

        # Parse Timestamps
        g = m_ts.groups()
        start_ms = parse_timestamp_part(g[0], g[1], g[2], g[3])
        end_ms = parse_timestamp_part(g[4], g[5], g[6], g[7])

        # Text lines are everything after timestamp line
        text_lines = lines[ts_line_idx + 1:]
        raw_sub_text = " ".join(text_lines)

        cleaned_text, speaker = clean_subtitle_text(raw_sub_text)
        if not cleaned_text:
            continue

        items.append(
            SubtitleItem(
                index=idx_num,
                start_ms=start_ms,
                end_ms=end_ms,
                text=cleaned_text,
                speaker=speaker,
                raw_text=raw_sub_text,
            )
        )

    # Sort by start_ms
    items.sort(key=lambda x: x.start_ms)
    return items


def extract_srt_speakers(items: List[SubtitleItem]) -> List[str]:
    """Extract a list of unique speaker names found in the subtitle items."""
    speakers = []
    seen = set()
    for item in items:
        if item.speaker:
            name = item.speaker.strip()
            if name.lower() not in seen:
                seen.add(name.lower())
                speakers.append(name)
    return speakers


def adjust_audio_speed(
    wav: np.ndarray,
    speed_factor: float,
    sample_rate: int = 48000
) -> np.ndarray:
    """
    Adjust audio playback speed without changing pitch (Pitch-Preserving Time-Stretching).
    Uses high-fidelity Time-Domain WSOLA (Waveform Similarity Overlap-Add) to eliminate
    robotic / metallic / buzzing phase artifacts, preserving crystal-clear natural timbre.

    Args:
        wav: 1D numpy array of audio samples (float32).
        speed_factor: Playback rate factor (> 1.0 speeds up, < 1.0 slows down).
        sample_rate: Audio sampling rate (default 48000 Hz).

    Returns:
        np.ndarray: Speed-adjusted audio waveform.
    """
    if wav is None or len(wav) == 0 or abs(speed_factor - 1.0) < 0.01:
        return wav

    speed_factor = max(0.3, min(float(speed_factor), 3.5))
    target_len = int(len(wav) / speed_factor)
    if target_len < 100:
        return wav

    try:
        import scipy.signal as signal

        # 25ms analysis window for optimal speech pitch tracking
        win_size = int(0.025 * sample_rate)
        if win_size % 2 != 0:
            win_size += 1
        hop_out = win_size // 2
        hop_in = max(1, int(hop_out * speed_factor))
        search_range = win_size // 2

        window = np.hanning(win_size).astype(np.float32)

        pad_len = win_size + search_range + hop_out
        padded_x = np.pad(wav.astype(np.float32), (search_range, pad_len), mode='reflect')

        num_frames = int(np.ceil((len(wav) - win_size) / hop_in))
        out_len = (num_frames + 2) * hop_out + win_size
        y = np.zeros(out_len, dtype=np.float32)
        norm = np.zeros(out_len, dtype=np.float32)

        curr_in = search_range
        y[0:win_size] += padded_x[curr_in:curr_in + win_size] * window
        norm[0:win_size] += window

        prev_in = curr_in
        for k in range(1, num_frames):
            target_in = int(k * hop_in) + search_range
            out_pos = k * hop_out

            ref_seg = padded_x[prev_in + hop_out : prev_in + hop_out + win_size]
            search_start = max(0, target_in - search_range)
            search_end = min(len(padded_x) - win_size, target_in + search_range)
            search_block = padded_x[search_start : search_end + win_size]

            if len(search_block) >= win_size and len(ref_seg) == win_size:
                xcorr = signal.correlate(search_block, ref_seg, mode='valid', method='fft')
                best_offset = np.argmax(xcorr)
                best_in = search_start + best_offset
            else:
                best_in = target_in

            seg = padded_x[best_in : best_in + win_size] * window
            y[out_pos : out_pos + win_size] += seg
            norm[out_pos : out_pos + win_size] += window
            prev_in = best_in

        mask = norm > 1e-4
        y[mask] /= norm[mask]

        if len(y) > target_len:
            y = y[:target_len]

        # Preserve original peak energy level to keep loudness 100% uniform
        orig_peak = np.max(np.abs(wav))
        new_peak = np.max(np.abs(y))
        if orig_peak > 1e-4 and new_peak > 1e-4:
            y = y * (orig_peak / new_peak)

        return y.astype(np.float32)

    except Exception:
        # Fallback to librosa or resampling
        try:
            import librosa
            stretched = librosa.effects.time_stretch(np.ascontiguousarray(wav, dtype=np.float32), rate=speed_factor)
            return stretched.astype(np.float32)
        except Exception:
            try:
                from scipy.signal import resample
                if target_len > 0:
                    return resample(wav, target_len).astype(np.float32)
            except Exception:
                pass
            return wav


def build_srt_audio_timeline(
    items: List[SubtitleItem],
    infer_chunk_fn: Callable[[SubtitleItem], np.ndarray],
    sample_rate: int = 48000,
    align_mode: str = "sync",
    speed_mode: str = "auto_speed_up",
    max_speed_factor: float = 2.0,
    min_speed_factor: float = 0.8,
    speed_threshold: float = 1.25,
    lead_in_silence_s: float = 0.0,
    lead_in_s: Optional[float] = None,
    progress_callback: Optional[Callable[..., None]] = None,
) -> Tuple[np.ndarray, Dict[str, Union[int, float, List[dict]]]]:
    """
    Synthesize audio for each subtitle and assemble them onto the timeline.

    Args:
        items: List of parsed SubtitleItem objects.
        infer_chunk_fn: Function `(SubtitleItem) -> np.ndarray` that returns the generated waveform.
        sample_rate: Output audio sample rate (default 48000 Hz).
        align_mode: "sync" (Strict time-alignment with silence padding) or "sequential".
        speed_mode: Speed adjustment mode:
            - "auto_speed_up": Automatically speed up if spoken audio exceeds subtitle duration (Default).
            - "fit_exact": Stretch or compress to match exact subtitle slot duration.
            - "none": Keep original speed (1.0x).
        max_speed_factor: Maximum speed-up ratio allowed (default 2.0x).
        min_speed_factor: Minimum speed-down ratio allowed (default 0.8x).
        speed_threshold: Max factor before warning that spoken text is longer than subtitle slot.
        lead_in_silence_s: Initial silence offset before the first subtitle (seconds).
        lead_in_s: Alias for `lead_in_silence_s`.
        progress_callback: Optional callback `(current_index, total_count, item, [start_s, duration_s])`.

    Returns:
        `(final_waveform, statistics_dict)`
    """
    if lead_in_s is not None:
        lead_in_silence_s = lead_in_s

    if not items:
        return np.array([], dtype=np.float32), {
            "total_items": 0,
            "total_duration_s": 0.0,
            "subtitles_info": []
        }

    timeline_chunks: List[np.ndarray] = []
    current_ms = int(lead_in_silence_s * 1000)
    subtitles_info: List[dict] = []

    for i, item in enumerate(items):
        target_start_ms = item.start_ms
        target_end_ms = item.end_ms
        slot_duration_ms = item.duration_ms

        if align_mode == "sync":
            # If current position is behind target start -> pad silence
            if target_start_ms > current_ms:
                silence_ms = target_start_ms - current_ms
                silence_samples = int(silence_ms / 1000.0 * sample_rate)
                if silence_samples > 0:
                    timeline_chunks.append(np.zeros(silence_samples, dtype=np.float32))
                current_ms = target_start_ms
            # If previous audio ran over target start, we cascade naturally (current_ms > target_start_ms)
        elif align_mode == "sequential":
            # In sequential mode, preserve the relative gap between subtitle items if any
            if i > 0:
                prev_end_ms = items[i - 1].end_ms
                if target_start_ms > prev_end_ms:
                    gap_ms = target_start_ms - prev_end_ms
                    gap_samples = int(gap_ms / 1000.0 * sample_rate)
                    if gap_samples > 0:
                        timeline_chunks.append(np.zeros(gap_samples, dtype=np.float32))
                        current_ms += gap_ms
            elif lead_in_silence_s > 0:
                init_samples = int(lead_in_silence_s * sample_rate)
                if init_samples > 0:
                    timeline_chunks.append(np.zeros(init_samples, dtype=np.float32))

        actual_start_ms = current_ms

        # Generate audio for this subtitle
        wav = infer_chunk_fn(item)
        if wav is None or len(wav) == 0:
            wav = np.array([], dtype=np.float32)

        original_wav_len = len(wav)
        raw_duration_ms = int((original_wav_len / sample_rate) * 1000) if sample_rate > 0 else 0

        # Auto Speed Matching / Time-Stretching
        applied_speed = 1.0
        if raw_duration_ms > 0 and slot_duration_ms > 0 and speed_mode != "none":
            needed_speed = raw_duration_ms / slot_duration_ms
            if speed_mode == "auto_speed_up" and raw_duration_ms > slot_duration_ms:
                applied_speed = min(needed_speed, max_speed_factor)
            elif speed_mode == "fit_exact":
                applied_speed = max(min_speed_factor, min(needed_speed, max_speed_factor))

            if abs(applied_speed - 1.0) > 0.02:
                wav = adjust_audio_speed(wav, applied_speed, sample_rate)

        wav_len = len(wav)
        actual_duration_ms = int((wav_len / sample_rate) * 1000) if sample_rate > 0 else 0

        timeline_chunks.append(wav)
        current_ms += actual_duration_ms

        # Check for timing discrepancy
        ratio = (actual_duration_ms / slot_duration_ms) if slot_duration_ms > 0 else 1.0
        over_slot = ratio > speed_threshold

        info = {
            "index": item.index,
            "speaker": item.speaker,
            "text": item.text,
            "target_start_s": target_start_ms / 1000.0,
            "target_end_s": target_end_ms / 1000.0,
            "target_duration_s": slot_duration_ms / 1000.0,
            "actual_start_s": actual_start_ms / 1000.0,
            "actual_duration_s": actual_duration_ms / 1000.0,
            "raw_duration_s": raw_duration_ms / 1000.0,
            "applied_speed": round(applied_speed, 2),
            "over_slot": over_slot,
            "duration_ratio": round(ratio, 2),
        }
        subtitles_info.append(info)

        if progress_callback:
            try:
                progress_callback(i + 1, len(items), item, actual_start_ms / 1000.0, actual_duration_ms / 1000.0)
            except TypeError:
                try:
                    progress_callback(i + 1, len(items), item)
                except Exception:
                    pass

    # Pad ending silence up to the last subtitle's end if needed
    if align_mode == "sync" and items:
        last_end_ms = items[-1].end_ms
        if last_end_ms > current_ms:
            trailing_ms = last_end_ms - current_ms
            trailing_samples = int(trailing_ms / 1000.0 * sample_rate)
            if trailing_samples > 0:
                timeline_chunks.append(np.zeros(trailing_samples, dtype=np.float32))
            current_ms = last_end_ms

    final_waveform = np.concatenate(timeline_chunks) if timeline_chunks else np.array([], dtype=np.float32)
    total_duration_s = len(final_waveform) / sample_rate if sample_rate > 0 else 0.0

    stats = {
        "total_items": len(items),
        "total_duration_s": total_duration_s,
        "subtitles_info": subtitles_info,
    }
    return final_waveform, stats
