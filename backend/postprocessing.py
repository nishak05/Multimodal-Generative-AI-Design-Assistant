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

def overlay_text(img, title="TITLE", subtitle="", title_font_path=None, subtitle_font_path=None, text_color="#FFFFFF"):
    if isinstance(img, str):
        img = Image.open(img)

    
    image = img.convert("RGBA")
    draw = ImageDraw.Draw(image)
    w, h = image.size

    # Choose font sizes relative to image height
    title_size = int(h * 0.10)
    sub_size = int(h * 0.045)

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

    print("Title size:", title_size, "Subtitle size:", sub_size)
    print("Brightness:", brightness)
    print("Image size:", image.size)

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
