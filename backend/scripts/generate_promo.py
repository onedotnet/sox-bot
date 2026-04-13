#!/usr/bin/env python3
"""Generate a landscape 16:9 promotional video for soxai.io.

Cinematic product promo with:
- Animated title sequences
- Feature showcase cards
- Code demos (horizontal terminal)
- Stats/numbers with emphasis
- CTA with branding
"""
import asyncio
import os
import sys
import uuid
import textwrap
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from video.tts import generate_audio

WIDTH = 1920
HEIGHT = 1080
FPS = 30

# Colors
BG = (6, 6, 8)
CARD_BG = (16, 16, 20)
ACCENT = (16, 185, 129)       # Emerald
ACCENT2 = (59, 130, 246)      # Blue
ACCENT3 = (245, 158, 11)      # Amber
PURPLE = (168, 85, 247)
WHITE = (245, 245, 245)
DIM = (100, 100, 110)
TERM_BG = (22, 22, 26)
TERM_HEADER = (38, 38, 42)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def _mono(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
    except:
        return ImageFont.load_default()


def _center_text(draw, text, y, font, color=WHITE, width=WIDTH):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((width // 2 - tw // 2, y), text, fill=color, font=font)


def _draw_gradient_bar(draw, x, y, w, h, color_left, color_right):
    for i in range(w):
        ratio = i / w
        r = int(color_left[0] * (1 - ratio) + color_right[0] * ratio)
        g = int(color_left[1] * (1 - ratio) + color_right[1] * ratio)
        b = int(color_left[2] * (1 - ratio) + color_right[2] * ratio)
        draw.line([(x + i, y), (x + i, y + h)], fill=(r, g, b))


def scene_title_intro(work_dir: str) -> list[str]:
    """Animated title: SoxAI logo + tagline."""
    frames = []
    total = 120  # 4 seconds

    for f in range(total):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        # Fade in (0-30), hold (30-90), fade out (90-120)
        if f < 30:
            alpha = f / 30
        elif f > 90:
            alpha = (120 - f) / 30
        else:
            alpha = 1.0

        # Gradient accent line
        bar_w = int(400 * min(1.0, f / 20))
        _draw_gradient_bar(draw, WIDTH // 2 - bar_w // 2, HEIGHT // 2 - 80,
                          bar_w, 3, ACCENT, ACCENT2)

        # Logo
        color = tuple(int(c * alpha) for c in WHITE)
        accent_c = tuple(int(c * alpha) for c in ACCENT)
        dim_c = tuple(int(c * alpha) for c in DIM)

        _center_text(draw, "SoxAI", HEIGHT // 2 - 50, _font(72, bold=True), color)
        _center_text(draw, "The AI API Gateway for Enterprise", HEIGHT // 2 + 40, _font(28), accent_c)
        _center_text(draw, "soxai.io", HEIGHT // 2 + 90, _font(20), dim_c)

        path = f"{work_dir}/title_{f:04d}.png"
        img.save(path)
        frames.append(path)

    return frames


def scene_problem(work_dir: str) -> list[str]:
    """The problem: multiple providers, multiple headaches."""
    frames = []
    total = 120

    problems = [
        ("4 API Keys", ACCENT3, 20),
        ("4 Billing Dashboards", ACCENT2, 40),
        ("3 Different SDKs", PURPLE, 60),
        ("Zero Visibility", (239, 68, 68), 80),
    ]

    for f in range(total):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        _center_text(draw, "The Problem", 80, _font(20), DIM)
        _center_text(draw, "Managing Multiple AI Providers", 120, _font(42, bold=True), WHITE)

        # Show problems appearing one by one
        for i, (text, color, appear_at) in enumerate(problems):
            if f >= appear_at:
                fade = min(1.0, (f - appear_at) / 15)
                c = tuple(int(v * fade) for v in color)
                text_c = tuple(int(v * fade) for v in WHITE)

                card_x = 200 + i * 380
                card_y = 350

                # Card background
                draw.rounded_rectangle(
                    [card_x, card_y, card_x + 340, card_y + 200],
                    radius=16, fill=CARD_BG, outline=c, width=2,
                )

                # Icon circle
                draw.ellipse([card_x + 140, card_y + 40, card_x + 200, card_y + 100], fill=c)

                # Text
                bbox = draw.textbbox((0, 0), text, font=_font(20, bold=True))
                tw = bbox[2] - bbox[0]
                draw.text((card_x + 170 - tw // 2, card_y + 130), text, fill=text_c, font=_font(20, bold=True))

        # Bottom stat
        if f > 60:
            fade = min(1.0, (f - 60) / 20)
            c = tuple(int(v * fade) for v in (239, 68, 68))
            _center_text(draw, "$800 surprise bill from one runaway loop", 650, _font(22), c)

        path = f"{work_dir}/problem_{f:04d}.png"
        img.save(path)
        frames.append(path)

    return frames


def scene_solution(work_dir: str) -> list[str]:
    """The solution: SoxAI gateway."""
    frames = []
    total = 120

    features = [
        ("200+ Models", "One endpoint, any provider", ACCENT),
        ("Auto Failover", "Provider down? Auto-switch", ACCENT2),
        ("Team Budgets", "Per-developer spending limits", ACCENT3),
        ("Cost Tracking", "Per-request cost visibility", PURPLE),
    ]

    for f in range(total):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        _center_text(draw, "The Solution", 60, _font(20), ACCENT)
        _center_text(draw, "One API Gateway for Everything", 100, _font(42, bold=True), WHITE)

        # Architecture diagram
        if f > 10:
            # Your App box
            draw.rounded_rectangle([140, 300, 380, 400], radius=12, fill=CARD_BG, outline=ACCENT, width=2)
            _center_text(draw, "Your App", 335, _font(18, bold=True), WHITE, width=520)

            # Arrow
            if f > 20:
                draw.line([(380, 350), (520, 350)], fill=ACCENT, width=2)
                draw.polygon([(520, 340), (540, 350), (520, 360)], fill=ACCENT)

            # SoxAI Gateway box
            if f > 25:
                draw.rounded_rectangle([540, 270, 860, 430], radius=16, fill=(16, 50, 40), outline=ACCENT, width=3)
                _center_text(draw, "SoxAI Gateway", 320, _font(22, bold=True), ACCENT, width=1400)
                _center_text(draw, "Route • Failover • Bill", 355, _font(14), DIM, width=1400)

            # Provider arrows + boxes
            providers = [
                ("OpenAI", 500, ACCENT2),
                ("Anthropic", 600, PURPLE),
                ("Google", 700, ACCENT3),
                ("DeepSeek", 800, (239, 68, 68)),
            ]

            for i, (name, x_offset, color) in enumerate(providers):
                appear = 35 + i * 10
                if f > appear:
                    py = 260 + i * 50
                    # Arrow from gateway
                    draw.line([(860, 350), (960, py)], fill=color, width=1)
                    # Provider box
                    draw.rounded_rectangle([960, py - 20, 1160, py + 20], radius=8, fill=CARD_BG, outline=color, width=1)
                    draw.text((980, py - 10), name, fill=color, font=_font(16))

        # Feature badges at bottom
        for i, (title, desc, color) in enumerate(features):
            appear = 50 + i * 15
            if f > appear:
                fade = min(1.0, (f - appear) / 15)
                bx = 140 + i * 430
                by = 520

                c = tuple(int(v * fade) for v in color)
                draw.rounded_rectangle([bx, by, bx + 400, by + 120], radius=12, fill=CARD_BG, outline=c, width=1)
                draw.text((bx + 20, by + 20), title, fill=c, font=_font(22, bold=True))
                draw.text((bx + 20, by + 60), desc, fill=tuple(int(v * fade) for v in DIM), font=_font(16))

        path = f"{work_dir}/solution_{f:04d}.png"
        img.save(path)
        frames.append(path)

    return frames


def scene_code_demo(work_dir: str) -> list[str]:
    """Code demo: show how easy it is."""
    frames = []
    total = 180  # 6 seconds

    code_lines = [
        'from openai import OpenAI',
        '',
        'client = OpenAI(',
        '    api_key="sox-your-key",',
        '    base_url="https://api.soxai.io/v1"',
        ')',
        '',
        '# Use ANY model from ANY provider',
        'response = client.chat.completions.create(',
        '    model="claude-sonnet-4-20250514",',
        '    messages=[{"role": "user", "content": "Hello!"}]',
        ')',
    ]
    full_text = "\n".join(code_lines)

    mono = _mono(20)
    line_h = 28

    # Terminal dimensions
    term_x, term_y = 360, 180
    term_w, term_h = 1200, 600

    for f in range(total):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        _center_text(draw, "Two Lines of Code", 60, _font(20), ACCENT)
        _center_text(draw, "That's All It Takes", 100, _font(42, bold=True), WHITE)

        # Terminal chrome
        draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + term_h],
                              radius=12, fill=TERM_BG, outline=(50, 50, 54), width=1)
        draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + 36],
                              radius=12, fill=TERM_HEADER)
        draw.rectangle([term_x, term_y + 24, term_x + term_w, term_y + 36], fill=TERM_HEADER)

        # Traffic lights
        draw.ellipse([term_x + 16, term_y + 10, term_x + 28, term_y + 22], fill=(255, 95, 86))
        draw.ellipse([term_x + 36, term_y + 10, term_x + 48, term_y + 22], fill=(39, 201, 63))
        draw.ellipse([term_x + 56, term_y + 10, term_x + 68, term_y + 22], fill=(255, 189, 46))

        # Title
        draw.text((term_x + term_w // 2 - 30, term_y + 10), "app.py", fill=DIM, font=_font(13))

        # Typing animation
        chars_visible = min(len(full_text), f * 3)
        visible = full_text[:chars_visible]
        vis_lines = visible.split("\n")

        text_x = term_x + 24
        text_y = term_y + 50

        keywords = {'from', 'import', 'def', 'class', 'return'}
        for li, line in enumerate(vis_lines):
            if text_y + li * line_h > term_y + term_h - 20:
                break

            x = text_x
            # Simple colorization
            if line.strip().startswith('#'):
                draw.text((x, text_y + li * line_h), line, fill=(92, 99, 112), font=mono)
            elif any(line.strip().startswith(kw) for kw in keywords):
                parts = line.split(' ', 1)
                draw.text((x, text_y + li * line_h), parts[0], fill=(198, 120, 221), font=mono)
                if len(parts) > 1:
                    bbox = draw.textbbox((0, 0), parts[0] + ' ', font=mono)
                    draw.text((x + bbox[2] - bbox[0], text_y + li * line_h), parts[1], fill=WHITE, font=mono)
            else:
                # Highlight strings
                in_str = False
                cx = x
                for ch in line:
                    if ch == '"':
                        in_str = not in_str
                    color = (152, 195, 121) if in_str or ch == '"' else WHITE
                    draw.text((cx, text_y + li * line_h), ch, fill=color, font=mono)
                    bbox = draw.textbbox((0, 0), ch, font=mono)
                    cx += bbox[2] - bbox[0]

        # Cursor
        if chars_visible < len(full_text) and f % 6 < 4:
            cursor_line = len(vis_lines) - 1
            cursor_col = len(vis_lines[-1]) if vis_lines else 0
            cx = text_x + cursor_col * 12
            cy = text_y + cursor_line * line_h
            draw.rectangle([cx, cy, cx + 10, cy + 22], fill=WHITE)

        # Highlight the key lines after typing is done
        if chars_visible >= len(full_text) and f % 60 > 30:
            # Highlight base_url line
            hl_y = text_y + 4 * line_h
            draw.rectangle([term_x + 10, hl_y - 2, term_x + term_w - 10, hl_y + line_h],
                          fill=(16, 185, 129, 30), outline=ACCENT, width=1)

        # Bottom text
        if f > 100:
            _center_text(draw, "Same OpenAI SDK. Zero code changes. 200+ models.", 850, _font(22), DIM)

        path = f"{work_dir}/code_{f:04d}.png"
        img.save(path)
        frames.append(path)

    return frames


def scene_stats(work_dir: str) -> list[str]:
    """Key stats with animated counters."""
    frames = []
    total = 120

    stats = [
        ("200+", "AI Models", ACCENT),
        ("40+", "Providers", ACCENT2),
        ("<5ms", "Gateway Latency", ACCENT3),
        ("$5", "Free Credit", PURPLE),
    ]

    for f in range(total):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        _center_text(draw, "By the Numbers", 100, _font(20), DIM)

        for i, (number, label, color) in enumerate(stats):
            appear = i * 20
            if f > appear:
                fade = min(1.0, (f - appear) / 20)
                c = tuple(int(v * fade) for v in color)
                tc = tuple(int(v * fade) for v in WHITE)
                lc = tuple(int(v * fade) for v in DIM)

                cx = 160 + i * 430
                cy = 300

                # Big number
                draw.text((cx + 50, cy), number, fill=c, font=_font(72, bold=True))
                draw.text((cx + 50, cy + 90), label, fill=lc, font=_font(22))

        # Bottom CTA
        if f > 80:
            fade = min(1.0, (f - 80) / 20)
            c = tuple(int(v * fade) for v in ACCENT)
            _center_text(draw, "Start free at soxai.io", 600, _font(28), c)

        path = f"{work_dir}/stats_{f:04d}.png"
        img.save(path)
        frames.append(path)

    return frames


def scene_cta(work_dir: str) -> list[str]:
    """Final CTA with branding."""
    frames = []
    total = 150  # 5 seconds

    for f in range(total):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        alpha = min(1.0, f / 30)
        if f > 120:
            alpha = (150 - f) / 30

        # Gradient line
        bar_w = int(600 * min(1.0, f / 25))
        _draw_gradient_bar(draw, WIDTH // 2 - bar_w // 2, HEIGHT // 2 - 150,
                          bar_w, 3, ACCENT, ACCENT2)

        c = tuple(int(v * alpha) for v in WHITE)
        ac = tuple(int(v * alpha) for v in ACCENT)
        dc = tuple(int(v * alpha) for v in DIM)

        _center_text(draw, "SoxAI", HEIGHT // 2 - 120, _font(80, bold=True), c)
        _center_text(draw, "One API. Every AI Model.", HEIGHT // 2, _font(32), ac)

        # Features row
        features = ["200+ Models", "Auto Failover", "Team Budgets", "Cost Tracking"]
        total_w = sum(len(f) * 12 + 60 for f in features)
        fx = WIDTH // 2 - total_w // 2
        for feat in features:
            draw.text((fx, HEIGHT // 2 + 70), f"✓  {feat}", fill=dc, font=_font(18))
            fx += len(feat) * 12 + 80

        _center_text(draw, "soxai.io", HEIGHT // 2 + 150, _font(36, bold=True), ac)
        _center_text(draw, "Free $5 credit • No card required", HEIGHT // 2 + 200, _font(18), dc)

        path = f"{work_dir}/cta_{f:04d}.png"
        img.save(path)
        frames.append(path)

    return frames


def frames_to_clip(frames: list[str], audio_path: str | None, output_path: str):
    """Convert frames + audio to video clip."""
    import subprocess
    work_dir = Path(output_path).parent
    frame_list = str(work_dir / f"fl_{Path(output_path).stem}.txt")

    with open(frame_list, "w") as f:
        for frame in frames:
            f.write(f"file '{frame}'\n")
            f.write(f"duration {1/FPS:.6f}\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", frame_list]
    if audio_path and os.path.exists(audio_path):
        cmd += ["-i", audio_path, "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), output_path]

    subprocess.run(cmd, capture_output=True)


async def main():
    video_id = uuid.uuid4().hex[:8]
    work_dir = f"/tmp/sox-bot-videos/promo-{video_id}"
    os.makedirs(work_dir, exist_ok=True)

    narrations = {
        "intro": "SoxAI. The AI API Gateway for Enterprise.",
        "problem": "Most teams use multiple AI providers. That means four API keys, four billing dashboards, three different SDKs, and zero visibility into who's spending what.",
        "solution": "SoxAI is an OpenAI-compatible gateway that sits between your code and the providers. One endpoint for two hundred plus models. Automatic failover. Team budgets. Per-request cost tracking.",
        "code": "It takes two lines of code. Set your API key, point the base URL to SoxAI, and you're done. Same OpenAI SDK. Any model from any provider.",
        "stats": "Two hundred plus models. Forty plus providers. Under five milliseconds of gateway latency. And a free five dollar credit to try it.",
        "cta": "SoxAI. One API for every AI model. Start free at soxai dot io.",
    }

    # Generate all audio
    print("Generating narration...")
    audio_files = {}
    for key, text in narrations.items():
        path = f"{work_dir}/audio_{key}.mp3"
        await generate_audio(text, path, voice="en_casual", rate="-5%")
        audio_files[key] = path

    # Render scenes
    scenes = [
        ("intro", scene_title_intro),
        ("problem", scene_problem),
        ("solution", scene_solution),
        ("code", scene_code_demo),
        ("stats", scene_stats),
        ("cta", scene_cta),
    ]

    clips = []
    for i, (name, renderer) in enumerate(scenes):
        print(f"Rendering {name}...")
        frame_dir = f"{work_dir}/{name}_frames"
        os.makedirs(frame_dir, exist_ok=True)
        frames = renderer(frame_dir)

        clip_path = f"{work_dir}/clip_{i:02d}_{name}.mp4"
        frames_to_clip(frames, audio_files.get(name), clip_path)
        clips.append(clip_path)

    # Concatenate
    print("Concatenating...")
    import subprocess
    concat_file = f"{work_dir}/concat.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")

    output = f"{work_dir}/soxai-promo.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy", output,
    ], capture_output=True)

    size = os.path.getsize(output) // 1024
    print(f"\nPromo video: {output} ({size} KB)")
    print(f"Download: scp server:{output} ~/Desktop/soxai-promo.mp4")


if __name__ == "__main__":
    asyncio.run(main())
