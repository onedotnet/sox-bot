"""Code typing animation renderer.

Renders frames of code being "typed" character by character,
with syntax-like coloring, cursor blink, and terminal chrome.
Produces a series of PNG frames → ffmpeg compiles to video.
"""

import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1920

# Terminal chrome colors
TERM_BG = (22, 22, 26)
TERM_HEADER = (38, 38, 42)
TERM_BORDER = (50, 50, 54)
TERM_DOT_RED = (255, 95, 86)
TERM_DOT_YELLOW = (255, 189, 46)
TERM_DOT_GREEN = (39, 201, 63)

# Syntax colors (approximation)
COLOR_KEYWORD = (198, 120, 221)   # purple - import, from, def, class
COLOR_STRING = (152, 195, 121)    # green - strings
COLOR_COMMENT = (92, 99, 112)     # gray - comments
COLOR_FUNCTION = (97, 175, 239)   # blue - function calls
COLOR_NUMBER = (209, 154, 102)    # orange - numbers
COLOR_NORMAL = (220, 220, 220)    # white - normal text
COLOR_PROMPT = (86, 182, 194)     # cyan - $ prompt
COLOR_OUTPUT = (150, 150, 150)    # dim - command output
CURSOR_COLOR = (220, 220, 220)

KEYWORDS = {'import', 'from', 'def', 'class', 'return', 'if', 'else', 'for',
            'in', 'with', 'as', 'async', 'await', 'True', 'False', 'None',
            'try', 'except', 'finally', 'raise', 'yield', 'lambda', 'not',
            'and', 'or', 'is'}


def _find_font(bold: bool = False, mono: bool = True) -> ImageFont.FreeTypeFont:
    """Find a monospace font."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for f in candidates:
        if os.path.exists(f):
            return ImageFont.truetype(f, 24)
    return ImageFont.load_default()


def _find_title_font() -> ImageFont.FreeTypeFont:
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if os.path.exists(path):
        return ImageFont.truetype(path, 36)
    return ImageFont.load_default()


def _colorize_token(token: str, in_string: bool, is_comment: bool) -> tuple:
    """Determine color for a code token."""
    if is_comment:
        return COLOR_COMMENT
    if in_string:
        return COLOR_STRING
    if token in KEYWORDS:
        return COLOR_KEYWORD
    if token.startswith('"') or token.startswith("'"):
        return COLOR_STRING
    if token.startswith('#'):
        return COLOR_COMMENT
    if token.replace('.', '').replace('-', '').isdigit():
        return COLOR_NUMBER
    if token.endswith('('):
        return COLOR_FUNCTION
    if token == '$':
        return COLOR_PROMPT
    return COLOR_NORMAL


def _draw_terminal_chrome(draw: ImageDraw.Draw, x: int, y: int,
                          w: int, h: int, title: str = "Terminal"):
    """Draw terminal window chrome (title bar + dots)."""
    # Window background
    draw.rounded_rectangle([x, y, x + w, y + h], radius=12,
                          fill=TERM_BG, outline=TERM_BORDER, width=1)

    # Title bar
    draw.rounded_rectangle([x, y, x + w, y + 36], radius=12,
                          fill=TERM_HEADER)
    draw.rectangle([x, y + 24, x + w, y + 36], fill=TERM_HEADER)

    # Traffic light dots
    draw.ellipse([x + 16, y + 10, x + 28, y + 22], fill=TERM_DOT_RED)
    draw.ellipse([x + 36, y + 10, x + 48, y + 22], fill=TERM_DOT_GREEN)
    draw.ellipse([x + 56, y + 10, x + 68, y + 22], fill=TERM_DOT_YELLOW)

    # Title
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), title, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((x + w // 2 - tw // 2, y + 10), title, fill=(150, 150, 150), font=font)


def render_typing_frames(code_lines: list[str], output_dir: str,
                         title: str = "Terminal",
                         chars_per_frame: int = 3,
                         title_text: str | None = None) -> list[str]:
    """Render frames of code being typed, character by character.

    Args:
        code_lines: Lines of code to animate
        output_dir: Directory to save frame PNGs
        title: Terminal window title
        chars_per_frame: Characters revealed per frame (speed)
        title_text: Optional big title text above terminal

    Returns:
        List of frame file paths
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    font = _find_font()
    title_font = _find_title_font()

    # Terminal window dimensions
    term_x = 40
    term_y = 200 if title_text else 100
    term_w = WIDTH - 80
    term_h = HEIGHT - term_y - 100
    text_x = term_x + 20
    text_y_start = term_y + 50

    # Build the full text
    full_text = "\n".join(code_lines)
    total_chars = len(full_text)

    frames = []
    line_height = 30

    # Generate frames
    for char_count in range(0, total_chars + 1, chars_per_frame):
        img = Image.new("RGB", (WIDTH, HEIGHT), (9, 9, 11))
        draw = ImageDraw.Draw(img)

        # Title text above terminal
        if title_text:
            draw.text((term_x + 10, 60), title_text, fill=(245, 245, 245), font=title_font)

        # Terminal chrome
        _draw_terminal_chrome(draw, term_x, term_y, term_w, term_h, title)

        # Render visible text
        visible = full_text[:char_count]
        visible_lines = visible.split("\n")

        y = text_y_start
        for line in visible_lines:
            if y > term_y + term_h - 40:
                break

            # Simple syntax coloring per word
            x = text_x
            in_string = False
            is_comment = False

            for char in line:
                if char in ('"', "'") and not is_comment:
                    in_string = not in_string
                if char == '#' and not in_string:
                    is_comment = True

                color = COLOR_STRING if in_string else (
                    COLOR_COMMENT if is_comment else COLOR_NORMAL
                )

                draw.text((x, y), char, fill=color, font=font)
                bbox = draw.textbbox((0, 0), char, font=font)
                x += bbox[2] - bbox[0]

            y += line_height

        # Cursor
        cursor_y = text_y_start + (len(visible_lines) - 1) * line_height
        last_line = visible_lines[-1] if visible_lines else ""
        cursor_x = text_x + len(last_line) * 14  # approximate char width
        if char_count % 6 < 4:  # blink
            draw.rectangle([cursor_x, cursor_y, cursor_x + 10, cursor_y + 24],
                          fill=CURSOR_COLOR)

        # Save frame
        frame_path = f"{output_dir}/frame_{len(frames):04d}.png"
        img.save(frame_path)
        frames.append(frame_path)

    # Hold last frame for a moment (30 extra frames = 1 second at 30fps)
    for i in range(30):
        frames.append(frames[-1])

    return frames


def render_spotlight_frames(base_image_path: str, regions: list[dict],
                           output_dir: str) -> list[str]:
    """Add spotlight/focus effect — dim everything except the highlighted region.

    Args:
        base_image_path: Path to the base screenshot/image
        regions: List of {"x": int, "y": int, "w": int, "h": int, "duration_frames": int}
        output_dir: Where to save frames

    Returns:
        List of frame paths
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    base = Image.open(base_image_path).convert("RGB")
    frames = []

    for region in regions:
        # Create darkened version
        dark = base.copy()
        dark_pixels = dark.load()
        w, h = dark.size
        for py in range(h):
            for px in range(w):
                r, g, b = dark_pixels[px, py]
                dark_pixels[px, py] = (r // 3, g // 3, b // 3)

        # Paste bright region back
        rx, ry, rw, rh = region["x"], region["y"], region["w"], region["h"]
        bright_region = base.crop((rx, ry, rx + rw, ry + rh))

        for f in range(region.get("duration_frames", 60)):
            frame = dark.copy()
            frame.paste(bright_region, (rx, ry))

            # Draw subtle border around focused area
            draw = ImageDraw.Draw(frame)
            draw.rounded_rectangle(
                [rx - 4, ry - 4, rx + rw + 4, ry + rh + 4],
                radius=8, outline=(16, 185, 129), width=2,
            )

            frame_path = f"{output_dir}/spotlight_{len(frames):04d}.png"
            frame.save(frame_path)
            frames.append(frame_path)

    return frames
