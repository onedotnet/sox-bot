"""Text-to-speech using Microsoft Edge TTS (free, high quality).

Supports multiple voices for different content types.
"""

import asyncio
from pathlib import Path

import edge_tts

# Good voices for developer content
VOICES = {
    "en_male": "en-US-ChristopherNeural",     # Clear male voice
    "en_female": "en-US-JennyNeural",          # Clear female voice
    "en_casual": "en-US-GuyNeural",            # More casual/friendly
    "zh_male": "zh-CN-YunxiNeural",            # Chinese male
    "zh_female": "zh-CN-XiaoxiaoNeural",       # Chinese female
}


async def generate_audio(text: str, output_path: str,
                         voice: str = "en_casual",
                         rate: str = "+10%") -> str:
    """Generate speech audio from text.

    Args:
        text: Text to speak
        output_path: Where to save the .mp3 file
        voice: Voice key from VOICES dict or full voice name
        rate: Speech rate adjustment (e.g. "+10%" for slightly faster)

    Returns:
        Path to the generated audio file
    """
    voice_name = VOICES.get(voice, voice)

    communicate = edge_tts.Communicate(text, voice_name, rate=rate)
    await communicate.save(output_path)

    return output_path


async def generate_scene_audios(scenes: list[dict], output_dir: str,
                                 voice: str = "en_casual") -> list[str]:
    """Generate audio for each scene's narration.

    Returns list of audio file paths.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    audio_files = []
    for i, scene in enumerate(scenes):
        narration = scene.get("narration", "")
        if not narration:
            continue
        filepath = str(output_path / f"scene_{i:02d}.mp3")
        await generate_audio(narration, filepath, voice=voice)
        audio_files.append(filepath)

    return audio_files
