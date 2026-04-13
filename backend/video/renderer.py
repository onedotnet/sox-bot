"""Video renderer — composites text overlays + audio into final video.

Uses moviepy to create scenes with:
- Dark background with subtle gradient
- Large text overlays (visual description from script)
- Narration audio
- SoxAI branding
"""

import os
import textwrap
from pathlib import Path

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)

# Video settings
WIDTH = 1080   # 9:16 for Shorts/TikTok
HEIGHT = 1920
FPS = 30
BG_COLOR = (9, 9, 11)          # Match sox.bot dark theme
ACCENT_COLOR = (16, 185, 129)   # Emerald
TEXT_COLOR = (245, 245, 245)
MUTED_COLOR = (113, 113, 122)

# Font — use a system font that's likely available
FONT = "DejaVu-Sans-Bold"
FONT_BODY = "DejaVu-Sans"


def _create_scene_clip(visual_text: str, audio_path: str | None,
                       duration: float, scene_index: int) -> CompositeVideoClip:
    """Create a single scene with text overlay and audio."""

    # Background
    bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR, duration=duration)

    layers = [bg]

    # Accent bar at top
    accent_bar = ColorClip(
        size=(WIDTH, 4), color=ACCENT_COLOR, duration=duration
    ).with_position(("center", 0))
    layers.append(accent_bar)

    # Main visual text (centered, large)
    wrapped = textwrap.fill(visual_text, width=25)
    try:
        main_text = TextClip(
            text=wrapped,
            font_size=52,
            color="white",
            font=FONT,
            text_align="center",
            size=(WIDTH - 120, None),
            duration=duration,
            method="caption",
        ).with_position(("center", "center"))
        layers.append(main_text)
    except Exception as e:
        print(f"Text rendering failed for scene {scene_index}: {e}")

    # Scene number indicator (subtle dots at bottom)
    try:
        scene_indicator = TextClip(
            text=f"{'●' * (scene_index + 1)}",
            font_size=16,
            color="rgb(113,113,122)",
            font=FONT_BODY,
            duration=duration,
        ).with_position(("center", HEIGHT - 100))
        layers.append(scene_indicator)
    except Exception:
        pass

    clip = CompositeVideoClip(layers, size=(WIDTH, HEIGHT))

    # Add audio if available
    if audio_path and os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        # Adjust scene duration to match audio if needed
        if audio.duration > duration:
            clip = clip.with_duration(audio.duration)
        clip = clip.with_audio(audio)

    return clip


def _create_hook_clip(hook_text: str, audio_path: str | None,
                      duration: float = 4.0) -> CompositeVideoClip:
    """Create the opening hook scene — more dramatic."""
    bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR, duration=duration)

    layers = [bg]

    # Big hook text
    try:
        hook = TextClip(
            text=hook_text,
            font_size=72,
            color="white",
            font=FONT,
            text_align="center",
            size=(WIDTH - 80, None),
            duration=duration,
            method="caption",
        ).with_position(("center", "center"))
        layers.append(hook)
    except Exception as e:
        print(f"Hook text rendering failed: {e}")

    clip = CompositeVideoClip(layers, size=(WIDTH, HEIGHT))

    if audio_path and os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        if audio.duration > duration:
            clip = clip.with_duration(audio.duration)
        clip = clip.with_audio(audio)

    return clip


def _create_cta_clip(cta_text: str, audio_path: str | None,
                     duration: float = 5.0) -> CompositeVideoClip:
    """Create the ending CTA scene with branding."""
    bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR, duration=duration)

    layers = [bg]

    # CTA text
    try:
        cta = TextClip(
            text=cta_text,
            font_size=48,
            color="rgb(16,185,129)",
            font=FONT,
            text_align="center",
            size=(WIDTH - 100, None),
            duration=duration,
            method="caption",
        ).with_position(("center", HEIGHT // 2 - 100))
        layers.append(cta)
    except Exception:
        pass

    # URL
    try:
        url = TextClip(
            text="soxai.io",
            font_size=64,
            color="white",
            font=FONT,
            duration=duration,
        ).with_position(("center", HEIGHT // 2 + 50))
        layers.append(url)
    except Exception:
        pass

    # sox.bot branding
    try:
        brand = TextClip(
            text="sox.bot",
            font_size=20,
            color="rgb(113,113,122)",
            font=FONT_BODY,
            duration=duration,
        ).with_position(("center", HEIGHT - 80))
        layers.append(brand)
    except Exception:
        pass

    clip = CompositeVideoClip(layers, size=(WIDTH, HEIGHT))

    if audio_path and os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        if audio.duration > duration:
            clip = clip.with_duration(audio.duration)
        clip = clip.with_audio(audio)

    return clip


def render_video(script: dict, audio_files: list[str], output_path: str) -> str:
    """Render complete video from script + audio files.

    Args:
        script: Parsed script from ScriptWriter
        audio_files: List of audio file paths (hook + scenes + cta)
        output_path: Where to save the final .mp4

    Returns:
        Path to rendered video
    """
    clips = []
    audio_idx = 0

    # Hook
    hook_audio = audio_files[audio_idx] if audio_idx < len(audio_files) else None
    audio_idx += 1
    clips.append(_create_hook_clip(
        script["hook"], hook_audio, duration=4.0
    ))

    # Scenes
    for i, scene in enumerate(script.get("scenes", [])):
        scene_audio = audio_files[audio_idx] if audio_idx < len(audio_files) else None
        audio_idx += 1
        duration = scene.get("duration", 5)
        clips.append(_create_scene_clip(
            scene.get("visual", ""),
            scene_audio,
            duration=duration,
            scene_index=i,
        ))

    # CTA
    cta_audio = audio_files[audio_idx] if audio_idx < len(audio_files) else None
    clips.append(_create_cta_clip(
        script.get("cta", "Try SoxAI free → soxai.io"),
        cta_audio,
        duration=5.0,
    ))

    # Concatenate all scenes
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None,
    )

    return output_path
