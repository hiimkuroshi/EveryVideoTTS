import os
import sys
import json
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from vieneu import Vieneu

def main():
    audio_path = r"D:\AI\Template Voice\Review 1.mp3"
    text_path = r"D:\AI\Template Voice\Review 1.txt"
    standalone_json_path = r"D:\AI\Template Voice\Review 1_preset.json"

    with open(text_path, "r", encoding="utf-8") as f:
        ref_text = f.read().strip()

    print("Reading audio: " + audio_path)
    print("Reading text: " + ref_text[:60] + "...")

    # Initialize v3 Turbo
    tts = Vieneu(mode="v3turbo")

    # Add and save to voices_v3_turbo.json
    tts.add_voice(
        name="Review 1",
        ref_audio=audio_path,
        description="Review 1 · Trợ lý AI / Tự nhiên",
        gender="male",
        save=True
    )
    print("Added to voices_v3_turbo.json successfully.")

    # Also export standalone preset JSON file in Template Voice directory
    voice_data = tts.get_preset_voice("Review 1")
    export_dict = {
        "name": "Review 1",
        "description": "Review 1 · Trợ lý AI / Tự nhiên",
        "gender": "male",
        "text": ref_text,
        "speaker_emb": [round(float(x), 6) for x in voice_data["speaker_emb"]],
        "codes": np.asarray(voice_data["codes"], dtype=int).tolist() if voice_data.get("codes") is not None else None
    }

    with open(standalone_json_path, "w", encoding="utf-8") as f:
        json.dump(export_dict, f, ensure_ascii=False, indent=2)

    print("Exported standalone preset to: " + standalone_json_path)

if __name__ == "__main__":
    main()
