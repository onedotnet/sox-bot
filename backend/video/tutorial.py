"""Tutorial video generator — combines code typing, terminal demos, and narration.

Generates a multi-scene tutorial with:
- Title card
- Code typing animation with syntax coloring
- Terminal command execution (simulated)
- Narration overlay
- Focus/spotlight effects on key areas

Usage:
    python scripts/generate_tutorial.py
"""

import os
import subprocess
from pathlib import Path

from video.code_animator import render_typing_frames, _find_font, _find_title_font
from video.tts import generate_audio
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1920
FPS = 30


def _frames_to_video(frames: list[str], audio_path: str | None,
                     output_path: str, fps: int = FPS):
    """Convert a sequence of frames + audio to video using ffmpeg."""
    work_dir = Path(output_path).parent

    # Create frame list file
    frame_list = str(work_dir / "framelist.txt")
    with open(frame_list, "w") as f:
        for frame in frames:
            f.write(f"file '{frame}'\n")
            f.write(f"duration {1/fps:.6f}\n")

    if audio_path and os.path.exists(audio_path):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", frame_list,
            "-i", audio_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            "-r", str(fps),
            output_path,
        ], capture_output=True)
    else:
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", frame_list,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-r", str(fps),
            output_path,
        ], capture_output=True)


def _render_title_card(title: str, subtitle: str, output_path: str,
                       duration_frames: int = 90) -> list[str]:
    """Render a title card (3 seconds at 30fps)."""
    frames = []
    Path(output_path).mkdir(parents=True, exist_ok=True)

    title_font = _find_title_font()
    try:
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except Exception:
        sub_font = ImageFont.load_default()

    for i in range(duration_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), (9, 9, 11))
        draw = ImageDraw.Draw(img)

        # Fade in effect (first 15 frames)
        alpha = min(1.0, i / 15)
        color = tuple(int(c * alpha) for c in (245, 245, 245))
        sub_color = tuple(int(c * alpha) for c in (16, 185, 129))

        # Accent line
        draw.rectangle([WIDTH // 2 - 40, HEIGHT // 2 - 80, WIDTH // 2 + 40, HEIGHT // 2 - 76],
                       fill=sub_color)

        # Title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text((WIDTH // 2 - tw // 2, HEIGHT // 2 - 60), title, fill=color, font=title_font)

        # Subtitle
        bbox2 = draw.textbbox((0, 0), subtitle, font=sub_font)
        sw = bbox2[2] - bbox2[0]
        draw.text((WIDTH // 2 - sw // 2, HEIGHT // 2 + 10), subtitle, fill=sub_color, font=sub_font)

        # sox.bot branding
        try:
            brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            draw.text((WIDTH // 2 - 25, HEIGHT - 100), "sox.bot", fill=(80, 80, 85), font=brand_font)
        except Exception:
            pass

        frame_path = f"{output_path}/title_{i:04d}.png"
        img.save(frame_path)
        frames.append(frame_path)

    return frames


class TutorialStep:
    """A single step in a tutorial video."""

    def __init__(self, step_type: str, **kwargs):
        self.type = step_type  # "title", "code", "terminal", "text"
        self.kwargs = kwargs


def build_tutorial(title: str, subtitle: str, steps: list[TutorialStep],
                   output_path: str, voice: str = "en_casual") -> str:
    """Build a complete tutorial video from steps.

    Args:
        title: Video title
        subtitle: Video subtitle
        steps: List of TutorialStep objects
        output_path: Where to save final .mp4
        voice: TTS voice to use

    Returns:
        Path to final video
    """
    import asyncio

    work_dir = Path(output_path).parent
    work_dir.mkdir(parents=True, exist_ok=True)

    clips = []
    clip_index = 0

    # Title card
    print("Rendering title card...")
    title_frames = _render_title_card(title, subtitle, str(work_dir / "title_frames"))
    title_audio = str(work_dir / "title_audio.mp3")
    asyncio.run(generate_audio(f"{title}. {subtitle}", title_audio, voice=voice, rate="-5%"))
    title_clip = str(work_dir / f"clip_{clip_index:02d}.mp4")
    _frames_to_video(title_frames, title_audio, title_clip)
    clips.append(title_clip)
    clip_index += 1

    for step in steps:
        print(f"Rendering step: {step.type}...")

        if step.type == "code":
            # Code typing animation
            code_lines = step.kwargs.get("code", [])
            narration = step.kwargs.get("narration", "")
            step_title = step.kwargs.get("title", "")

            frame_dir = str(work_dir / f"code_frames_{clip_index}")
            frames = render_typing_frames(
                code_lines, frame_dir,
                title=step.kwargs.get("terminal_title", "code.py"),
                chars_per_frame=step.kwargs.get("speed", 2),
                title_text=step_title,
            )

            # Generate narration audio
            audio_path = None
            if narration:
                audio_path = str(work_dir / f"narration_{clip_index}.mp3")
                asyncio.run(generate_audio(narration, audio_path, voice=voice))

            clip_path = str(work_dir / f"clip_{clip_index:02d}.mp4")
            _frames_to_video(frames, audio_path, clip_path)
            clips.append(clip_path)

        elif step.type == "terminal":
            # Terminal command + output
            commands = step.kwargs.get("commands", [])  # [{"cmd": "...", "output": "..."}]
            narration = step.kwargs.get("narration", "")
            step_title = step.kwargs.get("title", "")

            # Build lines: $ command \n output
            lines = []
            for cmd in commands:
                lines.append(f"$ {cmd['cmd']}")
                if cmd.get("output"):
                    for out_line in cmd["output"].split("\n"):
                        lines.append(out_line)
                lines.append("")  # blank line between commands

            frame_dir = str(work_dir / f"term_frames_{clip_index}")
            frames = render_typing_frames(
                lines, frame_dir,
                title="Terminal",
                chars_per_frame=2,
                title_text=step_title,
            )

            audio_path = None
            if narration:
                audio_path = str(work_dir / f"narration_{clip_index}.mp3")
                asyncio.run(generate_audio(narration, audio_path, voice=voice))

            clip_path = str(work_dir / f"clip_{clip_index:02d}.mp4")
            _frames_to_video(frames, audio_path, clip_path)
            clips.append(clip_path)

        elif step.type == "text":
            # Simple text card
            text = step.kwargs.get("text", "")
            narration = step.kwargs.get("narration", "")

            frame_dir = str(work_dir / f"text_frames_{clip_index}")
            Path(frame_dir).mkdir(parents=True, exist_ok=True)

            # Render text card frames
            font = _find_title_font()
            import textwrap
            wrapped = textwrap.fill(text, width=25)

            frame_paths = []
            for f_idx in range(90):  # 3 seconds
                img = Image.new("RGB", (WIDTH, HEIGHT), (9, 9, 11))
                draw = ImageDraw.Draw(img)
                lines = wrapped.split("\n")
                total_h = len(lines) * 50
                y = (HEIGHT - total_h) // 2
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    tw = bbox[2] - bbox[0]
                    draw.text((WIDTH // 2 - tw // 2, y), line, fill=(245, 245, 245), font=font)
                    y += 50
                fp = f"{frame_dir}/text_{f_idx:04d}.png"
                img.save(fp)
                frame_paths.append(fp)

            audio_path = None
            if narration:
                audio_path = str(work_dir / f"narration_{clip_index}.mp3")
                asyncio.run(generate_audio(narration, audio_path, voice=voice))

            clip_path = str(work_dir / f"clip_{clip_index:02d}.mp4")
            _frames_to_video(frame_paths, audio_path, clip_path)
            clips.append(clip_path)

        clip_index += 1

    # Concatenate all clips
    print("Concatenating clips...")
    concat_file = str(work_dir / "concat_final.txt")
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy",
        output_path,
    ], capture_output=True)

    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"Tutorial video: {output_path} ({size // 1024} KB)")
        return output_path

    print("Tutorial rendering failed!")
    return ""
