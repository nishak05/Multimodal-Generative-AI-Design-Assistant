# backend/postprocessing.py
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import json
import os

def _load_font(font_path, size):
    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size=size)
    except Exception:
        pass
    # fallback
    try:
        return ImageFont.load_default()
    except Exception:
        return None

def draw_text_with_shadow(draw, position, text, font, fill):
    x, y = position
    # draw shadow
    shadow_color = (0, 0, 0, 180)
    try:
        draw.text((x+2, y+2), text, font=font, fill=shadow_color)
    except Exception:
        pass
    # draw text
    draw.text((x, y), text, font=font, fill=fill)

def overlay_text(img, title="TITLE", subtitle="", font_path=None, text_color="#FFFFFF"):
    """
    Draws a title and subtitle on the image and returns a new PIL.Image (RGB).
    - font_path: path to .ttf/.otf or None to use default font.
    - text_color: hex string like '#FFFFFF'
    """
    if isinstance(img, str):
        img = Image.open(img)

    image = img.convert("RGBA")
    draw = ImageDraw.Draw(image)
    w, h = image.size

    # Choose font sizes relative to image height
    title_size = max(24, int(h * 0.09))
    sub_size = max(16, int(h * 0.04))

    title_font = _load_font(font_path, title_size)
    sub_font = _load_font(font_path, sub_size)

    # compute positions (centered)
    title_text = title or ""
    subtitle_text = subtitle or ""

    # Title (near top center)
    tw, th = draw.textsize(title_text, font=title_font)
    title_x = max(10, (w - tw) / 2)
    title_y = int(h * 0.08)

    # Subtitle (near bottom center)
    sw, sh = draw.textsize(subtitle_text, font=sub_font)
    sub_x = max(10, (w - sw) / 2)
    sub_y = int(h * 0.82)

    # Draw text with shadow for readability
    try:
        draw_text_with_shadow(draw, (title_x, title_y), title_text, title_font, text_color)
        draw_text_with_shadow(draw, (sub_x, sub_y), subtitle_text, sub_font, text_color)
    except Exception:
        # fallback: draw simple text
        draw.text((title_x, title_y), title_text, fill=text_color)
        draw.text((sub_x, sub_y), subtitle_text, fill=text_color)

    return image.convert("RGB")

def save_layout_metadata(outpath, metadata):
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
