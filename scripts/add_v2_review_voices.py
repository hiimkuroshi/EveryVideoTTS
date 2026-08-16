import os
import sys
import json
import torch
import librosa
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from neucodec import DistillNeuCodec

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading DistillNeuCodec on {device}...")
    codec = DistillNeuCodec.from_pretrained("neuphonic/distill-neucodec").to(device)
    codec.eval()

    voices_to_add = [
        {
            "name": "Review 1",
            "audio": r"D:\AI\Template Voice\Review 1.mp3",
            "text_path": r"D:\AI\Template Voice\Review 1.txt",
            "description": "Review 1 · Trợ lý AI (v2)"
        },
        {
            "name": "Review 2",
            "audio": r"D:\AI\Template Voice\Review 2.mp3",
            "text_path": r"D:\AI\Template Voice\Review 2.txt",
            "description": "Review 2 · Trợ lý AI (v2)"
        }
    ]

    voices_json_path = Path(r"D:\AI\VieNeu\VieNeu-TTS\src\vieneu\assets\voices.json")
    with open(voices_json_path, "r", encoding="utf-8") as f:
        voices_data = json.load(f)

    for item in voices_to_add:
        name = item["name"]
        audio_p = item["audio"]
        with open(item["text_path"], "r", encoding="utf-8") as tf:
            text_val = tf.read().strip()

        print(f"Encoding {name} from {audio_p}...")
        wav, _ = librosa.load(audio_p, sr=16000, mono=True)
        wav_tensor = torch.from_numpy(wav).float().unsqueeze(0).unsqueeze(0).to(device)

        with torch.no_grad():
            ref_codes = codec.encode_code(audio_or_path=wav_tensor).squeeze(0).squeeze(0)

        codes_list = ref_codes.cpu().numpy().flatten().tolist()
        print(f"  -> Generated {len(codes_list)} token codes for {name}")

        voices_data["presets"][name] = {
            "codes": codes_list,
            "text": text_val,
            "description": item["description"]
        }

    with open(voices_json_path, "w", encoding="utf-8") as f:
        json.dump(voices_data, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved Review 1 and Review 2 to {voices_json_path}")

if __name__ == "__main__":
    main()
