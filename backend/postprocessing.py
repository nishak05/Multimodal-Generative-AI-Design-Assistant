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
    shadow_color = (0, 0, 0)
    try:
        draw.text((x+3, y+3), text, font=font, fill=shadow_color)
    except Exception:
        pass
    # draw text
    draw.text((x, y), text, font=font, fill=fill)

def get_average_brightness(image, box):
    crop = image.crop(box).convert("L")  # grayscale
    pixels = list(crop.getdata())
    if not pixels:
        return 255
    return sum(pixels) / len(pixels)

def get_text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height

def overlay_text(img, title="TITLE", subtitle="", title_font_path=None, subtitle_font_path=None, text_color="#FFFFFF", variant=None):
    if isinstance(img, str):
        img = Image.open(img)

    
    image = img.convert("RGBA")
    draw = ImageDraw.Draw(image)
    w, h = image.size

    # Choose font sizes relative to image height
    title_size = int(h * (variant.get("title_scale", 0.10)))
    sub_size = int(h * (variant.get("subtitle_scale", 0.045)))


    title_font = _load_font(title_font_path, title_size)
    sub_font = _load_font(subtitle_font_path, sub_size)


    # compute positions (centered)
    title_text = title or ""
    subtitle_text = subtitle or ""

    # Title (near top center)
    tw, th = get_text_size(draw, title_text, title_font)
    title_x = max(10, (w - tw) / 2)
    title_y = int(h * 0.08)

    # Subtitle (near bottom center)
    sw, sh = get_text_size(draw, subtitle_text, sub_font)
    sub_x = max(10, (w - sw) / 2)
    sub_y = int(h * 0.82)

    pad = int(th * 0.8)
    title_box = (
        max(0, int(title_x - pad)),
        max(0, int(title_y - pad)),
        min(w, int(title_x + tw + pad)),
        min(h, int(title_y + th + pad))
    )

    brightness = get_average_brightness(image.convert("RGB"), title_box)

    # choose text color
    if brightness < 145:
        text_color = "white"
    else:
        text_color = "black"

    # Draw text with shadow for readability
    try:
        draw_text_with_shadow(draw, (title_x, title_y), title_text, title_font, text_color)
        draw_text_with_shadow(draw, (sub_x, sub_y), subtitle_text, sub_font, text_color)
    except Exception:
        # fallback: draw simple text
        draw.text((title_x, title_y), title_text, fill=text_color)
        draw.text((sub_x, sub_y), subtitle_text, fill=text_color)

    metadata = {
        "title_font": os.path.basename(title_font_path) if title_font_path else "Default",
        "subtitle_font": os.path.basename(subtitle_font_path) if subtitle_font_path else "Default",
        "text_color": text_color,
        "layout": "Title at top-center, subtitle at bottom-center",
        "background_brightness": round(brightness, 2),
    }
    if variant:
        metadata["variant"] = variant.get("name", "default")
        metadata["layout"] = variant.get("layout", "top-center/bottom-center")
    else:
        metadata["variant"] = "default"
        metadata["layout"] = "top-center/bottom-center"


    return image.convert("RGB"), metadata

def save_layout_metadata(outpath, metadata):
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def export_for_platforms(image):
    platforms = {
        "Instagram": (1080, 1080),
        "LinkedIn": (1200, 627),
        "YouTube": (1280, 720),
    }

    exports = {}

    for name, (W, H) in platforms.items():
        canvas = Image.new("RGB", (W, H), (0, 0, 0))

        img_ratio = image.width / image.height
        canvas_ratio = W / H

        if img_ratio > canvas_ratio:
            new_w = W
            new_h = int(W / img_ratio)
        else:
            new_h = H
            new_w = int(H * img_ratio)

        resized = image.resize((new_w, new_h), Image.LANCZOS)
        x = (W - new_w) // 2
        y = (H - new_h) // 2

        canvas.paste(resized, (x, y))
        exports[name] = canvas

    return exports
