import unittest
import numpy as np
from vieneu_utils.srt_utils import (
    SubtitleItem,
    parse_timestamp_part,
    parse_timestamp_string,
    format_timestamp,
    clean_subtitle_text,
    parse_srt,
    extract_srt_speakers,
    build_srt_audio_timeline,
)


class TestSRTUtils(unittest.TestCase):

    def test_parse_timestamp_string(self):
        self.assertEqual(parse_timestamp_string("00:00:01,000"), 1000)
        self.assertEqual(parse_timestamp_string("00:01:23,456"), (1 * 60 + 23) * 1000 + 456)
        self.assertEqual(parse_timestamp_string("01:02:03.500"), (1 * 3600 + 2 * 60 + 3) * 1000 + 500)
        self.assertEqual(parse_timestamp_string("invalid"), 0)

    def test_format_timestamp(self):
        self.assertEqual(format_timestamp(1000), "00:00:01,000")
        self.assertEqual(format_timestamp(83456), "00:01:23,456")
        self.assertEqual(format_timestamp(3663500), "01:01:03,500")

    def test_clean_subtitle_text(self):
        text, speaker = clean_subtitle_text("<i>Xin chào các bạn</i>")
        self.assertIsNone(speaker)
        self.assertEqual(text, "Xin chào các bạn")

        text, speaker = clean_subtitle_text("{\\an8}<b>Phương:</b> Hôm nay trời đẹp quá.")
        self.assertEqual(speaker, "Phương")
        self.assertEqual(text, "Hôm nay trời đẹp quá.")

        text, speaker = clean_subtitle_text("[Dũng] Tính năng này rất hay!")
        self.assertEqual(speaker, "Dũng")
        self.assertEqual(text, "Tính năng này rất hay!")

        text, speaker = clean_subtitle_text("<v Nam>Alô 1 2 3 4</v>")
        self.assertEqual(speaker, "Nam")
        self.assertEqual(text, "Alô 1 2 3 4")

    def test_parse_srt(self):
        sample_srt = """1
00:00:01,000 --> 00:00:04,500
Xin chào các bạn!

2
00:00:05,000 --> 00:00:08,000
Phương: Đây là câu số hai.
Dòng phụ thứ hai của câu.

3
00:00:09,000 --> 00:00:12,000
[Dũng] Câu số ba kết thúc.
"""
        items = parse_srt(sample_srt)
        self.assertEqual(len(items), 3)

        self.assertEqual(items[0].index, 1)
        self.assertEqual(items[0].start_ms, 1000)
        self.assertEqual(items[0].end_ms, 4500)
        self.assertEqual(items[0].duration_ms, 3500)
        self.assertIsNone(items[0].speaker)
        self.assertEqual(items[0].text, "Xin chào các bạn!")

        self.assertEqual(items[1].index, 2)
        self.assertEqual(items[1].start_ms, 5000)
        self.assertEqual(items[1].end_ms, 8000)
        self.assertEqual(items[1].speaker, "Phương")
        self.assertIn("Đây là câu số hai", items[1].text)
        self.assertIn("Dòng phụ thứ hai", items[1].text)

        self.assertEqual(items[2].index, 3)
        self.assertEqual(items[2].start_ms, 9000)
        self.assertEqual(items[2].end_ms, 12000)
        self.assertEqual(items[2].speaker, "Dũng")
        self.assertEqual(items[2].text, "Câu số ba kết thúc.")

    def test_extract_srt_speakers(self):
        items = [
            SubtitleItem(index=1, start_ms=1000, end_ms=3000, text="Lời 1", speaker="Phương"),
            SubtitleItem(index=2, start_ms=4000, end_ms=6000, text="Lời 2", speaker="Dũng"),
            SubtitleItem(index=3, start_ms=7000, end_ms=9000, text="Lời 3", speaker="Phương"),
            SubtitleItem(index=4, start_ms=10000, end_ms=12000, text="Lời 4", speaker=None),
        ]
        speakers = extract_srt_speakers(items)
        self.assertEqual(speakers, ["Phương", "Dũng"])

    def test_build_srt_audio_timeline_sync(self):
        sample_rate = 16000
        items = [
            SubtitleItem(index=1, start_ms=1000, end_ms=3000, text="Câu 1"),
            SubtitleItem(index=2, start_ms=5000, end_ms=7000, text="Câu 2"),
        ]

        def mock_infer_chunk(item: SubtitleItem) -> np.ndarray:
            return np.ones(16000, dtype=np.float32)

        progress_events = []
        def progress_cb(idx, total, item):
            progress_events.append((idx, total, item.index))

        final_audio, info_dict = build_srt_audio_timeline(
            items=items,
            sample_rate=sample_rate,
            infer_chunk_fn=mock_infer_chunk,
            align_mode="sync",
            lead_in_s=0.0,
            progress_callback=progress_cb,
        )

        self.assertEqual(len(final_audio), 7 * sample_rate)
        self.assertEqual(len(info_dict["subtitles_info"]), 2)
        self.assertEqual(len(progress_events), 2)
        self.assertEqual(info_dict["subtitles_info"][0]["actual_duration_s"], 1.0)
        self.assertEqual(info_dict["subtitles_info"][0]["target_duration_s"], 2.0)

    def test_build_srt_audio_timeline_sequential(self):
        sample_rate = 16000
        items = [
            SubtitleItem(index=1, start_ms=1000, end_ms=3000, text="Câu 1"),
            SubtitleItem(index=2, start_ms=5000, end_ms=7000, text="Câu 2"),
        ]

        def mock_infer_chunk(item: SubtitleItem) -> np.ndarray:
            return np.ones(16000, dtype=np.float32)

        final_audio, info_list = build_srt_audio_timeline(
            items=items,
            sample_rate=sample_rate,
            infer_chunk_fn=mock_infer_chunk,
            align_mode="sequential",
            lead_in_s=0.5,
        )

        expected_len = int(0.5 * sample_rate + 1.0 * sample_rate + 2.0 * sample_rate + 1.0 * sample_rate)
        self.assertEqual(len(final_audio), expected_len)

    def test_resolve_ref_voice_string_and_dict(self):
        from vieneu.base import BaseVieneuTTS

        class DummyTTS(BaseVieneuTTS):
            def __init__(self):
                self._preset_voices = {
                    "Ly": {"codes": np.zeros(10), "text": "Chào bạn"},
                    "Binh": {"codes": np.ones(10), "text": "Alô"}
                }
                self._default_voice = "Ly"
                self.sample_rate = 24000
                self.watermarker = None

            def infer(self, text, **kwargs):
                return np.zeros(100)

            def infer_batch(self, texts, **kwargs):
                return [np.zeros(100) for _ in texts]

            def infer_stream(self, text, **kwargs):
                yield np.zeros(100)

            def encode_reference(self, ref_audio):
                return np.zeros(10)

        tts = DummyTTS()

        # Test passing string voice ID (should not raise 'str' object has no attribute 'get')
        codes, text = tts._resolve_ref_voice(voice="Ly")
        self.assertEqual(text, "Chào bạn")
        self.assertEqual(len(codes), 10)

        # Test case-insensitive lookup
        codes, text = tts._resolve_ref_voice(voice="binh")
        self.assertEqual(text, "Alô")

        # Test passing dict
        codes, text = tts._resolve_ref_voice(voice={"codes": np.ones(5), "text": "Tự do"})
        self.assertEqual(text, "Tự do")
        self.assertEqual(len(codes), 5)

        # Test calling infer_srt with string voice and speaker mapping
        srt_text = """1
00:00:01,000 --> 00:00:03,000
Phương: Xin chào

2
00:00:04,000 --> 00:00:06,000
Dũng: Tạm biệt
"""
        wav, stats = tts.infer_srt(
            srt_input=srt_text,
            default_voice="Ly",
            speaker_map={"phương": "Ly", "dũng": "Binh"}
        )
        self.assertEqual(stats["total_items"], 2)
        self.assertTrue(len(wav) > 0)


if __name__ == "__main__":
    unittest.main()
