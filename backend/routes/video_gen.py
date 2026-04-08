"""
FastAPI router for AI video ad generation.

Generates short video ads (6-60 seconds) from ad copy with:
- Multiple templates (Product Showcase, Kinetic Typography, Before/After, Story/Reel)
- AI voiceover via Edge TTS
- User image upload support
- FFmpeg rendering to MP4
"""

import os
import re
import json
import uuid
import shutil
import asyncio
import subprocess
import tempfile
from typing import Optional, List
from datetime import datetime
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont
from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/video", tags=["video-generation"])

# Constants
OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
GPT4O_MODEL = "openai/gpt-4o"
FPS = 24  # Smooth animation
RENDER_SCALE = 1.0  # Full resolution rendering
MAX_DURATION = 60  # seconds
OUTPUT_DIR = Path(tempfile.gettempdir()) / "adlytics_videos"
OUTPUT_DIR.mkdir(exist_ok=True)

# Font paths - use system fonts
FONT_PATHS = {
    "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "light": "/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraLight.ttf",
}

# Video templates
TEMPLATES = {
    "product_showcase": {
        "name": "Product Showcase",
        "description": "Zoom-in product image with headline slide and CTA",
        "best_for": "E-commerce, real estate, SaaS",
        "default_duration": 6,
        "aspect_ratios": ["1:1", "16:9", "9:16"],
    },
    "kinetic_text": {
        "name": "Kinetic Typography",
        "description": "Bold animated text with word-by-word reveals",
        "best_for": "Awareness campaigns, brand ads",
        "default_duration": 5,
        "aspect_ratios": ["1:1", "16:9", "9:16"],
    },
    "before_after": {
        "name": "Before / After Split",
        "description": "Side-by-side comparison that slides in",
        "best_for": "Transformations, upgrades, results",
        "default_duration": 6,
        "aspect_ratios": ["1:1", "16:9"],
    },
    "story_reel": {
        "name": "Story / Reel",
        "description": "Vertical hero image with stacked text and swipe-up CTA",
        "best_for": "Instagram Stories, TikTok, Reels",
        "default_duration": 7,
        "aspect_ratios": ["9:16"],
    },
}

# Voice options for Edge TTS
VOICE_OPTIONS = {
    "male_us": "en-US-GuyNeural",
    "female_us": "en-US-JennyNeural",
    "male_uk": "en-GB-RyanNeural",
    "female_uk": "en-GB-SoniaNeural",
    "male_ng": "en-NG-AbeoNeural",
    "female_ng": "en-NG-EzinneNeural",
    "male_au": "en-AU-WilliamNeural",
    "female_au": "en-AU-NatashaNeural",
}

ASPECT_SIZES = {
    "1:1": (1080, 1080),
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
}


def get_openrouter_key():
    return os.getenv("OPENROUTER_API_KEY")


def get_font(style: str = "bold", size: int = 48):
    """Get a PIL font with fallback."""
    path = FONT_PATHS.get(style, FONT_PATHS["regular"])
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except Exception:
            return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


# Gradient background cache to avoid regenerating every frame
_gradient_cache = {}

def create_gradient_bg(width: int, height: int, color1: str, color2: str) -> Image.Image:
    """Create a gradient background image using fast vertical blend."""
    cache_key = (width, height, color1, color2)
    if cache_key in _gradient_cache:
        return _gradient_cache[cache_key].copy()

    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)
    # Fast: create two 1-pixel-wide strips and blend via resize
    top = Image.new("RGB", (1, 1), c1)
    bottom = Image.new("RGB", (1, 1), c2)
    # Stack them and resize — PIL interpolation creates the gradient
    gradient = Image.new("RGB", (1, 2))
    gradient.putpixel((0, 0), c1)
    gradient.putpixel((0, 1), c2)
    gradient = gradient.resize((width, height), Image.BILINEAR)

    _gradient_cache[cache_key] = gradient.copy()
    return gradient


def wrap_text(draw, text: str, font, max_width: int) -> list:
    """Wrap text to fit within max_width, returning list of lines."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_text_centered(draw, text: str, y: int, width: int, font, fill=(255, 255, 255)):
    """Draw centered text at y position."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    # Draw shadow
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 128))
    draw.text((x, y), text, font=font, fill=fill)


def draw_rounded_rect(draw, xy, radius, fill):
    """Draw a rounded rectangle with safety checks."""
    x0, y0, x1, y1 = [int(v) for v in xy]
    if x1 <= x0 or y1 <= y0:
        return  # Skip if rect is too small
    # Clamp radius to fit
    radius = min(radius, (x1 - x0) // 2, (y1 - y0) // 2)
    if radius < 1:
        draw.rectangle([x0, y0, x1, y1], fill=fill)
        return
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.pieslice([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270, fill=fill)
    draw.pieslice([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90, fill=fill)


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out for smooth animations."""
    return 1 - pow(1 - t, 3)


def ease_out_back(t: float) -> float:
    """Back ease-out for bouncy animations."""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def lerp(start: float, end: float, t: float) -> float:
    """Linear interpolation."""
    return start + (end - start) * t


# ========== FRAME RENDERERS ==========

def render_product_showcase_frame(
    frame_num: int, total_frames: int,
    width: int, height: int,
    headline: str, body: str, cta: str,
    colors: list, product_img: Optional[Image.Image] = None,
    brand_name: str = "ADLYTICS"
) -> Image.Image:
    """Render a single frame for Product Showcase template."""
    c1 = colors[0] if colors else "#1a1c2e"
    c2 = colors[1] if len(colors) > 1 else "#0f1119"
    accent = colors[2] if len(colors) > 2 else "#6366F1"

    bg = create_gradient_bg(width, height, c1, c2)
    draw = ImageDraw.Draw(bg)
    t = frame_num / total_frames  # 0 to 1

    # Phase timings — image visible for most of the video
    logo_start, logo_end = 0.0, 0.08
    img_start, img_end = 0.03, 0.20
    headline_start, headline_end = 0.20, 0.40
    body_start, body_end = 0.35, 0.50
    cta_start, cta_end = 0.45, 0.65

    # Logo
    if t >= logo_start:
        logo_t = min(1, (t - logo_start) / (logo_end - logo_start))
        font_logo = get_font("bold", int(width * 0.035))
        draw.text((int(width * 0.04), int(height * 0.03)), brand_name, font=font_logo, fill=hex_to_rgb(accent))

    # Product image — large and visible for most of the video
    if t >= img_start and product_img:
        img_t = min(1, (t - img_start) / (img_end - img_start))
        scale = ease_out_back(img_t)
        # Image fills ~80% width and ~45% height
        target_w = int(width * 0.80)
        target_h = int(height * 0.45)
        img_w = int(target_w * scale)
        img_h = int(target_h * scale)
        if img_w > 10 and img_h > 10:
            resized = product_img.resize((img_w, img_h), Image.LANCZOS)
            x = (width - img_w) // 2
            y = int(height * 0.08)
            # Add a subtle rounded border effect
            bg.paste(resized, (x, y))

    # Headline
    if t >= headline_start:
        hl_t = min(1, (t - headline_start) / (headline_end - headline_start))
        ease_v = ease_out_cubic(hl_t)
        font_hl = get_font("bold", int(width * 0.055))
        lines = wrap_text(draw, headline, font_hl, int(width * 0.85))
        y_offset = int(height * 0.62) + int(30 * (1 - ease_v))
        for line in lines:
            draw_text_centered(draw, line, y_offset, width, font_hl)
            y_offset += int(width * 0.065)

    # Body copy
    if t >= body_start:
        bd_t = min(1, (t - body_start) / (body_end - body_start))
        alpha = ease_out_cubic(bd_t)
        font_body = get_font("regular", int(width * 0.03))
        lines = wrap_text(draw, body, font_body, int(width * 0.8))
        y_offset = int(height * 0.78)
        for line in lines[:3]:
            draw_text_centered(draw, line, y_offset, width, font_body, fill=(220, 220, 220))
            y_offset += int(width * 0.038)

    # CTA Button
    if t >= cta_start:
        cta_t = min(1, (t - cta_start) / (cta_end - cta_start))
        scale = ease_out_back(cta_t)
        font_cta = get_font("bold", int(width * 0.035))
        bbox = draw.textbbox((0, 0), cta, font=font_cta)
        btn_w = (bbox[2] - bbox[0]) + int(width * 0.08)
        btn_h = int(height * 0.06)
        btn_x = (width - int(btn_w * scale)) // 2
        btn_y = int(height * 0.90)
        if scale > 0.1:
            draw_rounded_rect(draw,
                (btn_x, btn_y, btn_x + int(btn_w * scale), btn_y + int(btn_h * scale)),
                12, hex_to_rgb(accent))
            if scale > 0.5:
                draw_text_centered(draw, cta, btn_y + int(btn_h * 0.15 * scale), width, font_cta)

    return bg


def render_kinetic_text_frame(
    frame_num: int, total_frames: int,
    width: int, height: int,
    words: list, subtext: str, cta: str,
    colors: list
) -> Image.Image:
    """Render a single frame for Kinetic Typography template."""
    c1 = colors[0] if colors else "#6366F1"
    c2 = colors[1] if len(colors) > 1 else "#3B1F8B"

    bg = create_gradient_bg(width, height, c1, c2)
    draw = ImageDraw.Draw(bg)
    t = frame_num / total_frames

    num_words = len(words)
    word_duration = 0.12
    word_gap = 0.05

    for i, word in enumerate(words):
        word_start = 0.05 + i * (word_duration + word_gap)
        word_end = word_start + word_duration

        if t >= word_start:
            wt = min(1, (t - word_start) / word_duration)
            ease_v = ease_out_cubic(wt)

            font_size = int(width * 0.1)
            font_word = get_font("bold", font_size)

            scale_val = lerp(2.0, 1.0, ease_v)
            actual_size = int(font_size * min(scale_val, 1.5))
            font_word = get_font("bold", actual_size)

            y_pos = int(height * (0.2 + i * 0.15))

            # Last word in accent color
            color = (251, 191, 36) if i == num_words - 1 else (255, 255, 255)
            draw_text_centered(draw, word.upper(), y_pos, width, font_word, fill=color)

    # Subtext
    sub_start = 0.05 + num_words * (word_duration + word_gap) + 0.1
    if t >= sub_start:
        st = min(1, (t - sub_start) / 0.15)
        font_sub = get_font("regular", int(width * 0.032))
        lines = wrap_text(draw, subtext, font_sub, int(width * 0.8))
        y_off = int(height * 0.68)
        for line in lines:
            draw_text_centered(draw, line, y_off, width, font_sub, fill=(220, 220, 230))
            y_off += int(width * 0.04)

    # CTA
    cta_start = sub_start + 0.15
    if t >= cta_start:
        ct = min(1, (t - cta_start) / 0.12)
        ease_v = ease_out_cubic(ct)
        font_cta = get_font("bold", int(width * 0.04))
        bbox = draw.textbbox((0, 0), cta, font=font_cta)
        btn_w = (bbox[2] - bbox[0]) + int(width * 0.1)
        btn_h = int(height * 0.065)
        btn_x = (width - btn_w) // 2
        btn_y = int(height * 0.85)
        draw_rounded_rect(draw, (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), 30, (255, 255, 255))
        draw_text_centered(draw, cta, btn_y + int(btn_h * 0.15), width, font_cta, fill=hex_to_rgb(colors[0] if colors else "#6366F1"))

    return bg


def render_before_after_frame(
    frame_num: int, total_frames: int,
    width: int, height: int,
    before_text: str, after_text: str,
    headline: str, cta: str, colors: list
) -> Image.Image:
    """Render a single frame for Before/After template."""
    bg = Image.new("RGB", (width, height), hex_to_rgb("#0f1119"))
    draw = ImageDraw.Draw(bg)
    t = frame_num / total_frames

    half_w = width // 2
    slide_start, slide_end = 0.0, 0.25

    if t >= slide_start:
        st = min(1, (t - slide_start) / (slide_end - slide_start))
        ease_v = ease_out_cubic(st)

        # Left panel (red tint) - slides from left
        left_x = int(-half_w + half_w * ease_v)
        draw.rectangle([left_x, 0, left_x + half_w, height], fill=(30, 15, 15))

        # Right panel (green tint) - slides from right
        right_x = int(width - half_w * ease_v)
        draw.rectangle([right_x, 0, right_x + half_w, height], fill=(15, 30, 20))

        # Left content
        if ease_v > 0.5:
            font_label = get_font("bold", int(width * 0.025))
            font_emoji = get_font("regular", int(width * 0.07))
            font_txt = get_font("regular", int(width * 0.028))

            cx_left = left_x + half_w // 2
            draw_text_centered(draw, "WITHOUT US", int(height * 0.3), left_x + half_w, font_label, fill=(239, 68, 68))
            draw_text_centered(draw, ":(", int(height * 0.38), left_x + half_w, font_emoji, fill=(239, 68, 68))
            lines = wrap_text(draw, before_text, font_txt, int(half_w * 0.8))
            y_off = int(height * 0.5)
            for line in lines[:3]:
                draw_text_centered(draw, line, y_off, left_x + half_w, font_txt, fill=(180, 180, 180))
                y_off += int(width * 0.035)

            cx_right = right_x + half_w // 2
            # Offset right-side text by right_x
            draw.text((right_x + int(half_w * 0.2), int(height * 0.3)), "WITH US", font=font_label, fill=(16, 185, 129))
            draw_text_centered(draw, ":)", int(height * 0.38), right_x + half_w + right_x, font_emoji, fill=(16, 185, 129))
            lines = wrap_text(draw, after_text, font_txt, int(half_w * 0.8))
            y_off = int(height * 0.5)
            for line in lines[:3]:
                bbox = draw.textbbox((0, 0), line, font=font_txt)
                tw = bbox[2] - bbox[0]
                draw.text((right_x + (half_w - tw) // 2, y_off), line, font=font_txt, fill=(200, 220, 200))
                y_off += int(width * 0.035)

        # Divider
        if t > slide_end:
            div_t = min(1, (t - slide_end) / 0.1)
            div_h = int(height * ease_out_cubic(div_t))
            draw.rectangle([half_w - 1, 0, half_w + 1, div_h], fill=(100, 100, 100))

    # Headline
    hl_start = 0.55
    if t >= hl_start:
        hl_t = min(1, (t - hl_start) / 0.15)
        font_hl = get_font("bold", int(width * 0.045))
        lines = wrap_text(draw, headline, font_hl, int(width * 0.85))
        y_off = int(height * 0.75)
        for line in lines:
            draw_text_centered(draw, line, y_off, width, font_hl)
            y_off += int(width * 0.055)

    # CTA
    cta_start = 0.72
    if t >= cta_start:
        ct = min(1, (t - cta_start) / 0.12)
        font_cta = get_font("bold", int(width * 0.032))
        bbox = draw.textbbox((0, 0), cta, font=font_cta)
        btn_w = (bbox[2] - bbox[0]) + int(width * 0.08)
        btn_h = int(height * 0.055)
        btn_x = (width - btn_w) // 2
        btn_y = int(height * 0.90)
        draw_rounded_rect(draw, (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), 10, (16, 185, 129))
        draw_text_centered(draw, cta, btn_y + int(btn_h * 0.12), width, font_cta)

    return bg


def render_story_reel_frame(
    frame_num: int, total_frames: int,
    width: int, height: int,
    badge_text: str, headline: str, body: str, cta: str,
    colors: list, product_img: Optional[Image.Image] = None
) -> Image.Image:
    """Render a single frame for Story/Reel vertical template."""
    c1 = colors[0] if colors else "#1e1b4b"
    c2 = colors[1] if len(colors) > 1 else "#6366f1"

    bg = create_gradient_bg(width, height, c1, c2)
    draw = ImageDraw.Draw(bg)
    t = frame_num / total_frames

    # Badge
    badge_start = 0.0
    if t >= badge_start:
        bt = min(1, (t - badge_start) / 0.1)
        scale = ease_out_back(bt)
        if scale > 0.3:
            font_badge = get_font("bold", int(width * 0.035))
            bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
            bw = (bbox[2] - bbox[0]) + int(width * 0.06)
            bh = int(height * 0.025)
            bx = (width - bw) // 2
            by = int(height * 0.04)
            draw_rounded_rect(draw, (bx, by, bx + bw, by + bh), 15, (245, 158, 11))
            draw_text_centered(draw, badge_text, by + int(bh * 0.1), width, font_badge)

    # Product image — large hero image
    img_start = 0.05
    if t >= img_start and product_img:
        it = min(1, (t - img_start) / 0.15)
        scale = ease_out_cubic(it)
        img_w = int(width * 0.90 * scale)
        img_h = int(height * 0.40 * scale)
        if img_w > 10 and img_h > 10:
            resized = product_img.resize((img_w, img_h), Image.LANCZOS)
            x = (width - img_w) // 2
            y = int(height * 0.08)
            bg.paste(resized, (x, y))

    # Headline
    hl_start = 0.3
    if t >= hl_start:
        ht = min(1, (t - hl_start) / 0.15)
        font_hl = get_font("bold", int(width * 0.065))
        lines = wrap_text(draw, headline, font_hl, int(width * 0.85))
        y_off = int(height * 0.5)
        for line in lines:
            draw_text_centered(draw, line, y_off, width, font_hl)
            y_off += int(width * 0.075)

    # Body
    body_start = 0.45
    if t >= body_start:
        bdt = min(1, (t - body_start) / 0.12)
        font_body = get_font("regular", int(width * 0.033))
        lines = wrap_text(draw, body, font_body, int(width * 0.8))
        y_off = int(height * 0.66)
        for line in lines[:3]:
            draw_text_centered(draw, line, y_off, width, font_body, fill=(220, 220, 230))
            y_off += int(width * 0.04)

    # CTA
    cta_s = 0.6
    if t >= cta_s:
        ct = min(1, (t - cta_s) / 0.12)
        scale = ease_out_back(ct)
        font_cta = get_font("bold", int(width * 0.04))
        bbox = draw.textbbox((0, 0), cta, font=font_cta)
        btn_w = (bbox[2] - bbox[0]) + int(width * 0.12)
        btn_h = int(height * 0.04)
        btn_x = (width - btn_w) // 2
        btn_y = int(height * 0.82)
        if scale > 0.3:
            draw_rounded_rect(draw, (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), 14, (255, 255, 255))
            draw_text_centered(draw, cta, btn_y + int(btn_h * 0.12), width, font_cta, fill=hex_to_rgb(c1))

    # Swipe up text
    if t >= 0.75:
        font_sw = get_font("regular", int(width * 0.022))
        # Bounce effect
        bounce = int(5 * abs(((t - 0.75) * 10) % 2 - 1))
        draw_text_centered(draw, "SWIPE UP", int(height * 0.92) - bounce, width, font_sw, fill=(180, 180, 180))

    return bg


# ========== VOICEOVER ==========

async def generate_voiceover(text: str, voice: str, output_path: str, rate: str = "+0%") -> bool:
    """Generate voiceover audio using Edge TTS."""
    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_path)
        print(f"[video_gen] Voiceover saved: {output_path}")
        return True
    except Exception as e:
        print(f"[video_gen] Voiceover failed: {e}")
        return False


async def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


# ========== STOCK IMAGE FETCH ==========

async def fetch_stock_image_for_video(keywords: list, width: int, height: int) -> Optional[Image.Image]:
    """Fetch a stock image and return as PIL Image. Tries multiple sources."""
    import random
    from io import BytesIO

    search_query = ",".join(k.strip().lower() for k in keywords[:3] if k.strip())
    if not search_query:
        search_query = "business,modern"

    # Fetch at reasonable size (at least 800px wide for quality)
    fetch_w = max(width, 800)
    fetch_h = max(height, 600)

    sources = [
        # Source 1: Unsplash Source API (high quality, reliable)
        f"https://source.unsplash.com/{fetch_w}x{fetch_h}/?{search_query.replace(',', ',')}",
        # Source 2: loremflickr
        f"https://loremflickr.com/{fetch_w}/{fetch_h}/{search_query}?lock={random.randint(1000, 9999)}",
        # Source 3: Picsum (random but reliable)
        f"https://picsum.photos/seed/{search_query[:5]}{random.randint(1,999)}/{fetch_w}/{fetch_h}",
        # Source 4: Picsum random fallback
        f"https://picsum.photos/{fetch_w}/{fetch_h}?random={random.randint(1, 9999)}",
    ]

    for i, url in enumerate(sources):
        try:
            print(f"[video_gen] Trying image source {i+1}: {url[:80]}...")
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code == 200 and len(response.content) > 5000:
                    img = Image.open(BytesIO(response.content)).convert("RGB")
                    print(f"[video_gen] Got image from source {i+1}: {img.size}")
                    return img
                else:
                    print(f"[video_gen] Source {i+1} returned status {response.status_code}, size {len(response.content)}")
        except Exception as e:
            print(f"[video_gen] Source {i+1} failed: {e}")
            continue

    # Last resort: generate a colored placeholder
    print("[video_gen] All image sources failed, generating placeholder")
    placeholder = Image.new("RGB", (fetch_w, fetch_h), (40, 40, 60))
    draw = ImageDraw.Draw(placeholder)
    font = get_font("bold", 48)
    text = search_query.split(",")[0].upper()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((fetch_w - tw) // 2, fetch_h // 2 - 30), text, font=font, fill=(120, 120, 160))
    return placeholder


# ========== VIDEO ASSEMBLY ==========

def render_frames_to_video(
    frames_dir: str, output_path: str, fps: int = 24,
    audio_path: Optional[str] = None,
    output_width: int = 1080, output_height: int = 1080
) -> bool:
    """Use FFmpeg to assemble frames into MP4, optionally with audio."""
    try:
        has_audio = audio_path and os.path.exists(audio_path)

        cmd = ["ffmpeg", "-y"]

        # Video input
        cmd.extend(["-framerate", str(fps), "-i", f"{frames_dir}/frame_%05d.jpg"])

        # Audio input (must come right after video input, before output options)
        if has_audio:
            cmd.extend(["-i", audio_path])

        # Video encoding
        cmd.extend([
            "-vf", f"scale={output_width}:{output_height}:flags=lanczos",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "22",
        ])

        # Audio encoding
        if has_audio:
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "192k",
                "-map", "0:v:0",   # Map video from first input
                "-map", "1:a:0",   # Map audio from second input
                "-shortest",       # Stop when shortest stream ends
            ])

        cmd.extend(["-movflags", "+faststart", output_path])

        print(f"[video_gen] FFmpeg cmd: {' '.join(cmd[:15])}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print(f"[video_gen] FFmpeg error: {result.stderr[:800]}")
            # Retry without audio if muxing failed
            if has_audio:
                print("[video_gen] Retrying without audio...")
                cmd_noaudio = [
                    "ffmpeg", "-y",
                    "-framerate", str(fps),
                    "-i", f"{frames_dir}/frame_%05d.jpg",
                    "-vf", f"scale={output_width}:{output_height}:flags=lanczos",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-preset", "fast", "-crf", "22",
                    "-movflags", "+faststart", output_path
                ]
                result2 = subprocess.run(cmd_noaudio, capture_output=True, text=True, timeout=120)
                if result2.returncode == 0:
                    print("[video_gen] Video rendered without audio (fallback)")
                    return True
            return False

        print(f"[video_gen] Video rendered: {output_path} (audio={'yes' if has_audio else 'no'})")
        return True
    except Exception as e:
        print(f"[video_gen] FFmpeg failed: {e}")
        return False


# ========== AI SCRIPT GENERATION ==========

async def generate_video_script(
    product_description: str, industry: str, template: str,
    brand_name: Optional[str], duration: int
) -> dict:
    """Use GPT-4o to generate video ad script content."""
    if not get_openrouter_key():
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    template_info = TEMPLATES.get(template, TEMPLATES["product_showcase"])

    prompt = f"""You are an expert video ad creative director. Generate a video ad script for:

Product/Service: {product_description}
Brand: {brand_name or "Not specified"}
Industry: {industry}
Template Style: {template_info['name']} - {template_info['description']}
Duration: {duration} seconds

Return a JSON object with these fields:
1. "headline" - main headline text (5-8 words, punchy)
2. "body_copy" - supporting text (1-2 sentences, max 80 words)
3. "cta_text" - call-to-action button text (2-4 words)
4. "voiceover_script" - natural speech for voiceover narration that fits in {duration} seconds (~{duration * 2.5} words). Make it conversational and compelling.
5. "words_for_kinetic" - array of 3-4 impactful words for kinetic text animation (if template is kinetic_text)
6. "before_text" - pain point description (if template is before_after, max 15 words)
7. "after_text" - solution description (if template is before_after, max 15 words)
8. "badge_text" - short badge/label text like "NEW" or "LIMITED OFFER" (if template is story_reel)
9. "color_palette" - array of 3 hex colors that match the brand/industry
10. "image_keywords" - array of 2-3 simple nouns for stock photo search

Return ONLY valid JSON, no additional text or markdown."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OPENROUTER_API,
            headers={
                "Authorization": f"Bearer {get_openrouter_key()}",
                "HTTP-Referer": "https://adlytics.ai",
                "X-Title": "Adlytics Video Generation",
            },
            json={
                "model": GPT4O_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 1500,
            },
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"AI script generation failed: {response.text[:200]}")

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Strip markdown
        md_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if md_match:
            content = md_match.group(1)

        content = content.strip()
        if not content.startswith('{'):
            obj_match = re.search(r'\{[\s\S]*\}', content)
            if obj_match:
                content = obj_match.group(0)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[video_gen] JSON parse error: {content[:300]}")
            raise HTTPException(status_code=500, detail=f"Failed to parse video script: {str(e)}")


# ========== API ENDPOINTS ==========

@router.get("/templates")
async def get_templates():
    """Return available video ad templates."""
    return {
        "success": True,
        "data": {
            "templates": TEMPLATES,
            "voices": {k: v for k, v in VOICE_OPTIONS.items()},
            "aspect_ratios": list(ASPECT_SIZES.keys()),
            "max_duration": MAX_DURATION,
        }
    }


@router.post("/generate")
async def generate_video(
    product_description: str = Form(...),
    template: str = Form("product_showcase"),
    aspect_ratio: str = Form("1:1"),
    duration: int = Form(6),
    voice: str = Form("female_us"),
    voice_speed: str = Form("+0%"),
    industry: str = Form("general"),
    brand_name: Optional[str] = Form(None),
    enable_voiceover: bool = Form(True),
    uploaded_image: Optional[UploadFile] = File(None),
):
    """Generate a video ad with optional voiceover and user image."""

    # Validate
    if template not in TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid template. Choose from: {list(TEMPLATES.keys())}")

    if aspect_ratio not in ASPECT_SIZES:
        raise HTTPException(status_code=400, detail=f"Invalid aspect ratio. Choose from: {list(ASPECT_SIZES.keys())}")

    if duration < 3 or duration > MAX_DURATION:
        raise HTTPException(status_code=400, detail=f"Duration must be between 3 and {MAX_DURATION} seconds")

    voice_id = VOICE_OPTIONS.get(voice, VOICE_OPTIONS["female_us"])
    full_width, full_height = ASPECT_SIZES[aspect_ratio]
    # Render at half size for speed, ffmpeg scales up to full
    width = int(full_width * RENDER_SCALE)
    height = int(full_height * RENDER_SCALE)
    total_frames = duration * FPS

    # Generate unique job ID
    job_id = str(uuid.uuid4())[:8]
    job_dir = OUTPUT_DIR / job_id
    frames_dir = job_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Generate script with AI
        print(f"[video_gen] Generating script for job {job_id}...")
        script = await generate_video_script(
            product_description=product_description,
            industry=industry,
            template=template,
            brand_name=brand_name,
            duration=duration,
        )

        headline = script.get("headline", "Amazing Offer")
        body = script.get("body_copy", "Discover more today.")
        cta = script.get("cta_text", "Learn More")
        voiceover_text = script.get("voiceover_script", headline + ". " + body)
        colors = script.get("color_palette", ["#6366F1", "#1a1c2e", "#8B5CF6"])
        image_keywords = script.get("image_keywords", ["business", "modern"])

        # Step 2: Handle user image or fetch stock (at full resolution)
        product_img = None
        if uploaded_image and uploaded_image.filename:
            print(f"[video_gen] Using uploaded image: {uploaded_image.filename}")
            img_data = await uploaded_image.read()
            from io import BytesIO
            product_img = Image.open(BytesIO(img_data)).convert("RGB")
        else:
            print(f"[video_gen] Fetching stock image with keywords: {image_keywords}")
            product_img = await fetch_stock_image_for_video(image_keywords, full_width, int(full_height * 0.5))

        # Step 3: Generate voiceover
        audio_path = None
        if enable_voiceover:
            audio_path = str(job_dir / "voiceover.mp3")
            print(f"[video_gen] Generating voiceover with {voice_id}...")
            vo_success = await generate_voiceover(voiceover_text, voice_id, audio_path, rate=voice_speed)
            if vo_success:
                # Adjust duration to match audio if audio is longer
                audio_dur = await get_audio_duration(audio_path)
                if audio_dur > 0 and audio_dur > duration:
                    duration = min(int(audio_dur) + 1, MAX_DURATION)
                    total_frames = duration * FPS
                    print(f"[video_gen] Adjusted duration to {duration}s to match voiceover")
            else:
                audio_path = None

        # Resize product image to render dimensions
        if product_img:
            img_target_w = int(width * 0.80)
            img_target_h = int(height * 0.45)
            product_img = product_img.resize((img_target_w, img_target_h), Image.LANCZOS)
            print(f"[video_gen] Product image resized to {img_target_w}x{img_target_h}")

        # Step 4: Render frames
        print(f"[video_gen] Rendering {total_frames} frames at {width}x{height} (will scale to {full_width}x{full_height})...")

        for frame_num in range(total_frames):
            if template == "product_showcase":
                frame = render_product_showcase_frame(
                    frame_num, total_frames, width, height,
                    headline, body, cta, colors, product_img, brand_name or "ADLYTICS"
                )
            elif template == "kinetic_text":
                words = script.get("words_for_kinetic", headline.split()[:4])
                frame = render_kinetic_text_frame(
                    frame_num, total_frames, width, height,
                    words, body, cta, colors
                )
            elif template == "before_after":
                before_text = script.get("before_text", "The old way is broken")
                after_text = script.get("after_text", "We have the solution")
                frame = render_before_after_frame(
                    frame_num, total_frames, width, height,
                    before_text, after_text, headline, cta, colors
                )
            elif template == "story_reel":
                badge = script.get("badge_text", "NEW")
                frame = render_story_reel_frame(
                    frame_num, total_frames, width, height,
                    badge, headline, body, cta, colors, product_img
                )
            else:
                frame = render_product_showcase_frame(
                    frame_num, total_frames, width, height,
                    headline, body, cta, colors, product_img
                )

            frame.save(str(frames_dir / f"frame_{frame_num:05d}.jpg"), "JPEG", quality=85)

            # Log progress
            if frame_num % (FPS) == 0:
                print(f"[video_gen] Frame {frame_num}/{total_frames} ({int(frame_num/total_frames*100)}%)")

        # Step 5: Assemble video with FFmpeg
        output_path = str(job_dir / f"adlytics_video_{job_id}.mp4")
        print(f"[video_gen] Assembling video with FFmpeg...")

        success = render_frames_to_video(
            str(frames_dir), output_path, FPS,
            audio_path if audio_path and os.path.exists(audio_path) else None,
            output_width=full_width, output_height=full_height
        )

        if not success:
            raise HTTPException(status_code=500, detail="Video rendering failed")

        # Clean up frames
        shutil.rmtree(str(frames_dir), ignore_errors=True)

        file_size = os.path.getsize(output_path)
        print(f"[video_gen] Video complete: {output_path} ({file_size} bytes)")

        return {
            "success": True,
            "data": {
                "video_id": job_id,
                "video_url": f"/api/video/download/{job_id}",
                "duration": duration,
                "resolution": f"{full_width}x{full_height}",
                "aspect_ratio": aspect_ratio,
                "template": template,
                "has_voiceover": audio_path is not None,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "script": {
                    "headline": headline,
                    "body_copy": body,
                    "cta_text": cta,
                    "voiceover_script": voiceover_text,
                },
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        shutil.rmtree(str(job_dir), ignore_errors=True)
        print(f"[video_gen] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.get("/download/{video_id}")
async def download_video(video_id: str):
    """Download a generated video."""
    # Sanitize
    video_id = re.sub(r'[^a-f0-9-]', '', video_id)
    video_dir = OUTPUT_DIR / video_id

    if not video_dir.exists():
        raise HTTPException(status_code=404, detail="Video not found or expired")

    # Find the MP4 file
    mp4_files = list(video_dir.glob("*.mp4"))
    if not mp4_files:
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        str(mp4_files[0]),
        media_type="video/mp4",
        filename=f"adlytics_video_{video_id}.mp4",
    )


@router.get("/status")
async def get_video_status():
    """Check video generation capabilities."""
    has_ffmpeg = shutil.which("ffmpeg") is not None

    try:
        import edge_tts
        has_tts = True
    except ImportError:
        has_tts = False

    return {
        "ffmpeg_available": has_ffmpeg,
        "edge_tts_available": has_tts,
        "openrouter_available": bool(get_openrouter_key()),
        "templates_count": len(TEMPLATES),
        "max_duration": MAX_DURATION,
    }
