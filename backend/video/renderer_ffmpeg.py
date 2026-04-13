"""Video renderer using pure ffmpeg — more reliable than moviepy.

Generates each scene as an image + audio, then concatenates with ffmpeg.
"""

import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import textwrap

WIDTH = 1080
HEIGHT = 1920
BG_COLOR = (9, 9, 11)
ACCENT_COLOR = (16, 185, 129)
TEXT_COLOR = (245, 245, 245)
MUTED_COLOR = (113, 113, 122)


def _find_font(bold: bool = False) -> str:
    """Find a usable font on the system."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for f in candidates:
        if os.path.exists(f):
            return f
    return ""  # PIL will use default


def _render_scene_image(text: str, output_path: str,
                        font_size: int = 52, text_color=TEXT_COLOR,
                        accent: bool = True):
    """Render a scene as a PNG image."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Accent bar at top
    if accent:
        draw.rectangle([0, 0, WIDTH, 4], fill=ACCENT_COLOR)

    # Load font
    font_path = _find_font(bold=True)
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default(font_size)
    except Exception:
        font = ImageFont.load_default()

    # Wrap text
    wrapped = textwrap.fill(text, width=28)
    lines = wrapped.split("\n")

    # Calculate total text height
    line_height = font_size + 10
    total_height = len(lines) * line_height
    y_start = (HEIGHT - total_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (WIDTH - text_width) // 2
        y = y_start + i * line_height
        draw.text((x, y), line, fill=text_color, font=font)

    # sox.bot branding at bottom
    try:
        small_font = ImageFont.truetype(_find_font(bold=False), 20) if _find_font() else ImageFont.load_default()
        draw.text((WIDTH // 2 - 30, HEIGHT - 80), "sox.bot", fill=MUTED_COLOR, font=small_font)
    except Exception:
        pass

    img.save(output_path)


def _make_scene_video(image_path: str, audio_path: str, output_path: str):
    """Combine an image + audio into a video clip using ffmpeg."""
    # Get audio duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True,
    )
    duration = float(result.stdout.strip()) if result.stdout.strip() else 5.0

    # Create video from still image + audio
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-t", str(duration + 0.5),  # slight padding
        output_path,
    ], capture_output=True)


def render_video(script: dict, audio_files: list[str], output_path: str) -> str:
    """Render complete video from script + audio.

    1. Render each scene as image
    2. Combine each image + audio into clip
    3. Concatenate all clips
    """
    work_dir = Path(output_path).parent
    clips = []

    # All parts: hook + scenes + cta
    parts = []
    parts.append({"text": script["hook"], "font_size": 72, "color": TEXT_COLOR})
    for scene in script.get("scenes", []):
        parts.append({"text": scene.get("visual", ""), "font_size": 52, "color": TEXT_COLOR})
    parts.append({"text": script.get("cta", "Try SoxAI → soxai.io"), "font_size": 48, "color": ACCENT_COLOR})

    for i, (part, audio_path) in enumerate(zip(parts, audio_files)):
        img_path = str(work_dir / f"frame_{i:02d}.png")
        clip_path = str(work_dir / f"clip_{i:02d}.mp4")

        _render_scene_image(part["text"], img_path,
                           font_size=part["font_size"],
                           text_color=part["color"])
        _make_scene_video(img_path, audio_path, clip_path)
        clips.append(clip_path)

    # Concatenate all clips
    concat_file = str(work_dir / "concat.txt")
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_path,
    ], capture_output=True)

    # Verify output
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        print(f"Video rendered: {output_path} ({os.path.getsize(output_path) // 1024} KB)")
        return output_path
    else:
        print("Video rendering failed!")
        return ""
