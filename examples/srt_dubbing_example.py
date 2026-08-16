"""
Ví dụ sử dụng tính năng lồng tiếng phim từ phụ đề SRT với VieNeu-TTS.
Hỗ trợ cả giọng đọc đơn (single-speaker) và phân vai đa nhân vật (multi-speaker).
"""

import os
import sys

# Thêm thư mục gốc src vào sys.path để import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from vieneu import Vieneu
from vieneu_utils import parse_srt, extract_srt_speakers


def main():
    srt_file_path = os.path.join(os.path.dirname(__file__), "sample.srt")
    output_audio_path = os.path.join(os.path.dirname(__file__), "output_srt_dubbed.wav")

    print(f"📄 Đang đọc file phụ đề: {srt_file_path}")
    with open(srt_file_path, "r", encoding="utf-8") as f:
        srt_content = f.read()

    items = parse_srt(srt_content)
    detected_speakers = extract_srt_speakers(items)
    print(f"📊 Tìm thấy {len(items)} câu phụ đề.")
    if detected_speakers:
        print(f"👥 Phát hiện các nhân vật: {detected_speakers}")

    # Khởi tạo TTS engine (v3 Turbo hoặc bất kỳ backend nào)
    print("\n📦 Khởi tạo VieNeu-TTS v3 Turbo...")
    tts = Vieneu(mode="v3turbo", device="auto")

    # Bản đồ gán giọng cho từng nhân vật (nếu có)
    speaker_mapping = {
        "phương": "Ly",
        "dũng": "Binh",
    }

    print("\n🎬 Bắt đầu lồng tiếng phụ đề SRT (Strict Timeline Sync)...")
    audio, info_list = tts.infer_srt(
        srt_input=srt_file_path,
        default_voice="Ly",
        speaker_map=speaker_mapping,
        align_mode="sync",
        progress_callback=lambda idx, total, item: print(
            f"   ⏳ [{idx}/{total}] {item.start_str} -> {item.end_str}: "
            f"[{item.speaker or 'Mặc định'}] {item.text[:30]}..."
        )
    )

    # Lưu file âm thanh hoàn chỉnh
    tts.save_srt_audio(output_audio_path, audio)
    print(f"\n✅ Đã lưu file audio lồng tiếng tại: {output_audio_path}")


if __name__ == "__main__":
    main()
