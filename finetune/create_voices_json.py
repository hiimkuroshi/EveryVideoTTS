"""
Helper script to create voices.json for custom fine-tuned models.

Usage:
    # Create new file with first voice
    python finetune/create_voices_json.py --audio ref1.wav --text "..." --name voice1
    
    # Add more voices to existing file
    python finetune/create_voices_json.py --audio ref2.wav --text "..." --name voice2 --append
"""

import argparse
import json
import os
import torch
import librosa
from pathlib import Path
from neucodec import DistillNeuCodec

def create_voices_json(audio_path, text, voice_name, output_path="voices.json", description="", append=False, set_default=True):
    """
    Create or update a voices.json file from reference audio.
    
    Args:
        audio_path: Path to reference audio file (.wav)
        text: Exact transcript of the audio
        voice_name: Name for this voice preset
        output_path: Where to save voices.json
        description: Optional description of the voice
        append: If True, add to existing file; if False, create new file
        set_default: If True, set this voice as default_voice
    """
    print(f"🎙️ {'Adding' if append else 'Creating'} voice preset '{voice_name}' from {audio_path}")
    
    # Load existing data if appending
    if append and Path(output_path).exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            voices_data = json.load(f)
        print(f"   📂 Loaded existing file with {len(voices_data.get('presets', {}))} voice(s)")
    else:
        voices_data = {
            "meta": {
                "spec": "vieneu.voice.presets",
                "spec_version": "1.0",
                "engine": "EveryVideoTTS",
                "author": "Tyr",
                "license": "CC BY-NC 4.0",
                "homepage": "https://github.com/hiimkuroshi/EveryVideoTTS",
                "notice": "Base model: VieNeu-TTS by pnnbao-ump (CC BY-NC 4.0) - non-commercial use only, attribution required."
            },
            "default_voice": voice_name if set_default else None,
            "presets": {}
        }
    
    # Load DistillNeuCodec (same codec VieNeu-TTS uses at inference)
    print("   🔊 Loading DistillNeuCodec...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    codec = DistillNeuCodec.from_pretrained("neuphonic/distill-neucodec").to(device)
    codec.eval()

    # Encode the reference audio
    print("   🎙️ Encoding audio...")
    wav, _ = librosa.load(audio_path, sr=16000, mono=True)
    wav_tensor = torch.from_numpy(wav).float().unsqueeze(0).unsqueeze(0).to(device)

    with torch.no_grad():
        ref_codes = codec.encode_code(audio_or_path=wav_tensor).squeeze(0).squeeze(0)

    # Convert to list for JSON serialization
    codes_list = ref_codes.cpu().numpy().flatten().tolist()
    
    # Add this voice to presets
    voices_data["presets"][voice_name] = {
        "codes": codes_list,
        "text": text,
        "description": description or f"Custom voice: {voice_name}"
    }
    
    # Update default if requested
    if set_default:
        voices_data["default_voice"] = voice_name
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(voices_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {'Updated' if append else 'Created'} {output_path}")
    print(f"   Total voices: {len(voices_data['presets'])}")
    print(f"   Default voice: {voices_data.get('default_voice', 'None')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create voices.json for custom models")
    parser.add_argument("--audio", type=str, required=True, help="Path to reference audio (.wav)")
    parser.add_argument("--text", type=str, required=True, help="Exact transcript of the audio")
    parser.add_argument("--name", type=str, required=True, help="Name for this voice preset")
    parser.add_argument("--description", type=str, default="", help="Optional description")
    parser.add_argument("--output", type=str, default="voices.json", help="Output file path")
    parser.add_argument("--append", action="store_true", help="Append to existing file instead of traversing")
    parser.add_argument("--no-default", action="store_true", help="Do NOT set this voice as default")
    
    args = parser.parse_args()
    
    create_voices_json(
        audio_path=args.audio,
        text=args.text,
        voice_name=args.name,
        output_path=args.output,
        description=args.description,
        append=args.append,
        set_default=not args.no_default
    )
