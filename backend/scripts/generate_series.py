#!/usr/bin/env python3
"""Batch-generate the 30-second tutorial video series.

Usage:
    python scripts/generate_series.py                    # Generate ALL videos
    python scripts/generate_series.py --list             # List all videos
    python scripts/generate_series.py --id game-npc-dialogue  # Generate one
    python scripts/generate_series.py --series "AI + Games"   # Generate one series
    python scripts/generate_series.py --upload            # Generate + upload to YouTube
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from video.series import SERIES, get_all_videos, get_videos_by_series, get_series_names
from video.code_animator import render_typing_frames
from video.tts import generate_audio

OUTPUT_BASE = Path("/tmp/sox-bot-videos/series")
FPS = 30
WIDTH = 1080
HEIGHT = 1920


def frames_to_clip(frames: list[str], audio_path: str | None, output_path: str):
    import subprocess
    work_dir = Path(output_path).parent
    frame_list = str(work_dir / "framelist.txt")
    with open(frame_list, "w") as f:
        for frame in frames:
            f.write(f"file '{frame}'\n")
            f.write(f"duration {1/FPS:.6f}\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", frame_list]
    if audio_path and os.path.exists(audio_path):
        cmd += ["-i", audio_path, "-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), output_path]
    subprocess.run(cmd, capture_output=True)


def render_hook_frames(text: str, output_dir: str) -> list[str]:
    """Render big hook text frames."""
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
    except:
        font = ImageFont.load_default()

    frames = []
    for f_idx in range(120):  # 4 seconds
        img = Image.new("RGB", (WIDTH, HEIGHT), (9, 9, 11))
        draw = ImageDraw.Draw(img)

        # Accent bar
        draw.rectangle([WIDTH // 2 - 50, HEIGHT // 2 - 120, WIDTH // 2 + 50, HEIGHT // 2 - 116],
                       fill=(16, 185, 129))

        # Series badge
        try:
            small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            draw.text((WIDTH // 2 - 80, HEIGHT // 2 - 160), "Build with AI in 30s",
                      fill=(16, 185, 129), font=small)
        except:
            pass

        # Hook text
        alpha = min(1.0, f_idx / 10)
        color = tuple(int(c * alpha) for c in (245, 245, 245))
        lines = text.split("\n")
        total_h = len(lines) * 75
        y = (HEIGHT - total_h) // 2 - 30
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((WIDTH // 2 - tw // 2, y), line, fill=color, font=font)
            y += 75

        fp = f"{output_dir}/hook_{f_idx:04d}.png"
        img.save(fp)
        frames.append(fp)
    return frames


def render_cta_frames(text: str, output_dir: str) -> list[str]:
    """Render CTA frames."""
    from PIL import Image, ImageDraw, ImageFont

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
        small = font

    frames = []
    for f_idx in range(120):  # 4 seconds
        img = Image.new("RGB", (WIDTH, HEIGHT), (9, 9, 11))
        draw = ImageDraw.Draw(img)

        alpha = min(1.0, f_idx / 15)
        accent = tuple(int(c * alpha) for c in (16, 185, 129))
        white = tuple(int(c * alpha) for c in (245, 245, 245))
        dim = tuple(int(c * alpha) for c in (100, 100, 110))

        # Logo
        draw.text((WIDTH // 2 - 80, HEIGHT // 2 - 80), "SoxAI", fill=white, font=font)

        # CTA lines
        lines = text.split("\n")
        y = HEIGHT // 2 + 10
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=small)
            tw = bbox[2] - bbox[0]
            draw.text((WIDTH // 2 - tw // 2, y), line, fill=accent, font=small)
            y += 30

        # Bottom brand
        draw.text((WIDTH // 2 - 25, HEIGHT - 80), "sox.bot", fill=dim, font=small)

        fp = f"{output_dir}/cta_{f_idx:04d}.png"
        img.save(fp)
        frames.append(fp)
    return frames


async def generate_one(video_id: str, video: dict, upload: bool = False) -> str | None:
    """Generate a single video. Returns path to .mp4."""
    work_dir = OUTPUT_BASE / video_id
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[{video_id}] {video['title']}")

    # 1. Hook audio + frames
    print(f"  Rendering hook...")
    hook_audio = str(work_dir / "hook_audio.mp3")
    await generate_audio(video["hook"].replace("\n", ". "), hook_audio, voice="en_casual", rate="+0%")
    hook_frames = render_hook_frames(video["hook"], str(work_dir / "hook_frames"))
    hook_clip = str(work_dir / "clip_hook.mp4")
    frames_to_clip(hook_frames, hook_audio, hook_clip)

    # 2. Code typing animation + narration
    print(f"  Rendering code...")
    code_audio = str(work_dir / "code_audio.mp3")
    await generate_audio(video["narration"], code_audio, voice="en_casual", rate="+5%")
    code_frames = render_typing_frames(
        video["code"], str(work_dir / "code_frames"),
        title=video.get("terminal_title", "app.py"),
        chars_per_frame=2,
        title_text=None,
    )
    code_clip = str(work_dir / "clip_code.mp4")
    frames_to_clip(code_frames, code_audio, code_clip)

    # 3. CTA
    print(f"  Rendering CTA...")
    cta_audio = str(work_dir / "cta_audio.mp3")
    await generate_audio("Try it free at soxai.io", cta_audio, voice="en_casual")
    cta_frames = render_cta_frames(video["cta"], str(work_dir / "cta_frames"))
    cta_clip = str(work_dir / "clip_cta.mp4")
    frames_to_clip(cta_frames, cta_audio, cta_clip)

    # 4. Concatenate
    import subprocess
    concat_file = str(work_dir / "concat.txt")
    with open(concat_file, "w") as f:
        f.write(f"file '{hook_clip}'\n")
        f.write(f"file '{code_clip}'\n")
        f.write(f"file '{cta_clip}'\n")

    output = str(work_dir / "final.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy", output,
    ], capture_output=True)

    if os.path.exists(output) and os.path.getsize(output) > 1000:
        size = os.path.getsize(output) // 1024
        print(f"  ✓ {output} ({size} KB)")

        if upload:
            from video.youtube_upload import YouTubeUploader
            uploader = YouTubeUploader()
            desc = f"{video['narration']}\n\nTry free: https://console.soxai.io/register\nDocs: https://docs.soxai.io\n\n#AI #API #coding #developer #SoxAI #shorts"
            url = uploader.upload(output, video["title"] + " #shorts", desc, privacy="public")
            if url:
                print(f"  ↑ Uploaded: {url}")

        return output
    else:
        print(f"  ✗ Failed")
        return None


async def main():
    args = sys.argv[1:]

    if "--list" in args:
        for series in sorted(get_series_names()):
            print(f"\n{series}:")
            for v in get_videos_by_series(series):
                print(f"  {v['id']:30s} {v['title']}")
        return

    upload = "--upload" in args
    target_id = None
    target_series = None

    for i, arg in enumerate(args):
        if arg == "--id" and i + 1 < len(args):
            target_id = args[i + 1]
        elif arg == "--series" and i + 1 < len(args):
            target_series = args[i + 1]

    if target_id:
        if target_id not in SERIES:
            print(f"Unknown video: {target_id}")
            print(f"Available: {', '.join(SERIES.keys())}")
            sys.exit(1)
        await generate_one(target_id, SERIES[target_id], upload=upload)
    elif target_series:
        videos = get_videos_by_series(target_series)
        if not videos:
            print(f"Unknown series: {target_series}")
            print(f"Available: {', '.join(get_series_names())}")
            sys.exit(1)
        for v in videos:
            await generate_one(v["id"], v, upload=upload)
    else:
        # Generate all
        for vid_id, vid in SERIES.items():
            await generate_one(vid_id, vid, upload=upload)

    print(f"\nDone! Videos at: {OUTPUT_BASE}")


if __name__ == "__main__":
    asyncio.run(main())
