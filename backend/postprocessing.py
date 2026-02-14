from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import json
import os
import re
import numpy as np

MAX_TITLE_SCALE = 0.12
MIN_TITLE_SCALE = 0.05

MAX_SUBTITLE_SCALE = 0.06
MIN_SUBTITLE_SCALE = 0.025

BRIGHTNESS_THRESHOLD = 145


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

def draw_text_adaptive(draw, position, text, font, text_color, brightness):
    x, y = position

    if text_color == "black" and brightness > 180:
        # light background → subtle dark stroke
        stroke_width = 2
        stroke_fill = "black"
        draw.text(
            (x, y),
            text,
            font=font,
            fill=text_color,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill
        )

    elif text_color == "white" and brightness < 100:
        # dark background → subtle shadow
        draw.text((x+2, y+2), text, font=font, fill="black")
        draw.text((x, y), text, font=font, fill=text_color)

    else:
        # normal case
        draw.text((x, y), text, font=font, fill=text_color)


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

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

def remove_emoji(text):
    # Removes emoji characters from text.
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )

    cleaned = emoji_pattern.sub("", text)
    return cleaned, cleaned != text


def find_low_texture_slice(image, slice_height_ratio=0.12):
    gray = image.convert("L")
    arr = np.array(gray)

    h, w = arr.shape

    # TITLE ZONE
    zone_top = int(h * 0.08)
    zone_bottom = int(h * 0.55)

    zone = arr[zone_top:zone_bottom, :]

    slice_height = int((zone_bottom - zone_top) * slice_height_ratio)

    best_score = float("inf")
    best_y = zone_top

    for y in range(0, zone.shape[0] - slice_height, slice_height):
        slice_region = zone[y:y + slice_height, :]

        # edge density using gradient magnitude
        gy, gx = np.gradient(slice_region.astype(float))
        edge_density = np.mean(np.sqrt(gx**2 + gy**2))

        # slight bias toward upper slices
        bias = y * 0.02
        score = edge_density + bias

        if score < best_score:
            best_score = score
            best_y = zone_top + y

    return best_y


def overlay_text(img, title="TITLE", subtitle="", title_font_path=None, subtitle_font_path=None, text_color="#FFFFFF", variant=None):
    if isinstance(img, str):
        img = Image.open(img)

    image = img.convert("RGBA")

    MIN_SIZE = 512

    w, h = image.size

    if min(w, h) < MIN_SIZE:
        scale = MIN_SIZE / min(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = image.resize((new_w, new_h), Image.LANCZOS)

    draw = ImageDraw.Draw(image)
    w, h = image.size

    # Choose font sizes relative to image height
    raw_title_scale = variant.get("title_scale", 0.10)
    raw_sub_scale = variant.get("subtitle_scale", 0.045)

    title_scale = max(MIN_TITLE_SCALE, min(MAX_TITLE_SCALE, raw_title_scale))
    sub_scale = max(MIN_SUBTITLE_SCALE, min(MAX_SUBTITLE_SCALE, raw_sub_scale))

    title_size = int(h * title_scale)
    sub_size = int(h * sub_scale)


    title_font = _load_font(title_font_path, title_size)
    sub_font = _load_font(subtitle_font_path, sub_size)


    # compute positions (centered)
    title_text = title or ""
    subtitle_text = subtitle or ""

    # Remove emoji
    title_text, title_emoji_removed = remove_emoji(title_text)
    subtitle_text, sub_emoji_removed = remove_emoji(subtitle_text)

    emoji_removed = title_emoji_removed or sub_emoji_removed
    has_long_word = any(len(word) > 25 for word in title_text.split())


    # -------- TITLE WRAPPING LOGIC --------

    SAFE_MARGIN = int(w * 0.10)
    max_text_width = w - 2 * SAFE_MARGIN

    MAX_TITLE_LINES = 3
    # MIN_TITLE_SCALE = 0.045

    title_lines = wrap_text(draw, title_text, title_font, max_text_width)
    original_title_line_count = len(title_lines)


    # Try shrinking if too many lines
    while len(title_lines) > MAX_TITLE_LINES and title_scale > MIN_TITLE_SCALE:
        title_scale *= 0.92
        title_size = int(h * title_scale)
        title_font = _load_font(title_font_path, title_size)
        title_lines = wrap_text(draw, title_text, title_font, max_text_width)

    title_overflow = len(title_lines) > MAX_TITLE_LINES

    title_lines = title_lines[:MAX_TITLE_LINES]

    line_spacing = int(title_size * 0.2)
   # Vision-aware placement
    try:
        detected_y = find_low_texture_slice(image)
        title_y_start = max(int(h * 0.05), min(detected_y, int(h * 0.6)))
    except Exception:
        # fallback to default placement
        title_y_start = max(int(h * 0.08), int(h * 0.05))

    title_positions = []
    current_y = title_y_start

    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]

        title_x = (w - line_width) // 2
        title_positions.append((line, title_x, current_y))
        current_y += line_height + line_spacing

    # Calculate total height AFTER building positions
    if title_positions:
        first_y = title_positions[0][2]
        last_line, _, last_y = title_positions[-1]
        bbox = draw.textbbox((0, 0), last_line, font=title_font)
        last_height = bbox[3] - bbox[1]
        total_title_height = (last_y - first_y) + last_height
    else:
        first_y = title_y_start
        total_title_height = title_size

    # Prevent title block overflow
    max_allowed_height = int(h * 0.45)
    if total_title_height > max_allowed_height:
        shrink_ratio = max_allowed_height / total_title_height
        title_size = int(title_size * shrink_ratio)
        title_font = _load_font(title_font_path, title_size)

        # Re-wrap
        title_lines = wrap_text(draw, title_text, title_font, max_text_width)
        title_lines = title_lines[:3]

        title_positions = []
        current_y = title_y_start

        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]

            title_x = (w - line_width) // 2
            title_positions.append((line, title_x, current_y))
            current_y += line_height + line_spacing

    # -------- SUBTITLE WRAPPING LOGIC --------
    SAFE_MARGIN = int(w * 0.10)
    max_sub_width = w - 2 * SAFE_MARGIN


    MAX_SUB_LINES = 2
    MIN_SUB_SCALE = 0.03

    subtitle_lines = wrap_text(draw, subtitle_text, sub_font, max_sub_width)
    original_sub_line_count = len(subtitle_lines)

    while len(subtitle_lines) > MAX_SUB_LINES and sub_scale > MIN_SUB_SCALE:
        sub_scale *= 0.92
        sub_size = int(h * sub_scale)
        sub_font = _load_font(subtitle_font_path, sub_size)
        subtitle_lines = wrap_text(draw, subtitle_text, sub_font, max_sub_width)

    subtitle_overflow = len(subtitle_lines) > MAX_SUB_LINES
    subtitle_lines = subtitle_lines[:MAX_SUB_LINES]

    sub_line_spacing = int(sub_size * 0.25)

    sub_y_start = int(h * 0.82)

    subtitle_positions = []

    current_y = sub_y_start

    for line in subtitle_lines:
        bbox = draw.textbbox((0, 0), line, font=sub_font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]

        sub_x = (w - line_width) // 2
        subtitle_positions.append((line, sub_x, current_y))
        current_y += line_height + sub_line_spacing

    # Now fix overflow AFTER building positions
    if subtitle_positions:
        last_line, _, last_y = subtitle_positions[-1]
        bbox = draw.textbbox((0, 0), last_line, font=sub_font)
        last_height = bbox[3] - bbox[1]

        bottom = last_y + last_height
        max_bottom = int(h * 0.95)

        if bottom > max_bottom:
            overflow = bottom - max_bottom
            subtitle_positions = [
                (line, x, y - overflow)
                for (line, x, y) in subtitle_positions
            ]

    pad = int(title_size * 0.8)
    title_box = (
        0,
        max(0, int(first_y - pad)),
        w,
        min(h, int(first_y + total_title_height + pad))
    )


    brightness = get_average_brightness(image.convert("RGB"), title_box)

    # choose text color
    if brightness < 145:
        text_color = "white"
    else:
        text_color = "black"

    # Draw text with shadow for readability
    try:
        if text_color == "white":
            for line, x, y in title_positions:
                draw_text_adaptive(
                    draw,
                    (x, y),
                    line,
                    title_font,
                    text_color,
                    brightness
                )


            for line, x, y in subtitle_positions:
                draw_text_adaptive(
                    draw,
                    (x, y),
                    line,
                    sub_font,
                    text_color,
                    brightness
                )

        else:
            for line, x, y in title_positions:
                draw.text((x, y), line, font=title_font, fill=text_color)
            for line, x, y in subtitle_positions:
                draw.text((x, y), line, font=sub_font, fill=text_color)
   
    except Exception:
        for line, x, y in title_positions:
            draw.text((x, y), line, fill=text_color)
        for line, x, y in subtitle_positions:
            draw.text((x, y), line, fill=text_color)


    metadata = {
        "title_font": os.path.basename(title_font_path) if title_font_path else "Default",
        "subtitle_font": os.path.basename(subtitle_font_path) if subtitle_font_path else "Default",
        "text_color": text_color,
        "layout": "Title at top-center, subtitle at bottom-center",
        "background_brightness": round(brightness, 2),
        "contrast_strategy": (
            "stroke" if text_color == "black" and brightness > 180
            else "shadow" if text_color == "white" and brightness < 100
            else "none"
        ),
        "emoji_removed": emoji_removed,
        "title_truncated": title_overflow,
        "subtitle_truncated": subtitle_overflow,
        "long_word_detected": has_long_word,

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


def export_with_text(base_image, title, subtitle, title_font_path, subtitle_font_path, variant):
    platforms = {
        "Instagram": (1080, 1080),
        "LinkedIn": (1200, 627),
        "YouTube": (1280, 720),
    }

    exports = {}

    for name, (W, H) in platforms.items():
        img_ratio = base_image.width / base_image.height
        target_ratio = W / H

        if img_ratio > target_ratio:
            new_h = H
            new_w = int(H * img_ratio)
        else:
            new_w = W
            new_h = int(W / img_ratio)

        resized = base_image.resize((new_w, new_h), Image.LANCZOS)

        left = (new_w - W) // 2
        top = (new_h - H) // 2
        cropped = resized.crop((left, top, left + W, top + H))

        final_img, _ = overlay_text(
            cropped,
            title=title,
            subtitle=subtitle,
            title_font_path=title_font_path,
            subtitle_font_path=subtitle_font_path,
            variant=variant
        )

        exports[name] = final_img

    return exports

# def export_for_platforms(image):
#     platforms = {
#         "Instagram": (1080, 1080),
#         "LinkedIn": (1200, 627),
#         "YouTube": (1280, 720),
#     }

#     exports = {}

#     for name, (W, H) in platforms.items():
#         img_ratio = image.width / image.height
#         target_ratio = W / H

#         if img_ratio > target_ratio:
#             # Image is wider → crop width
#             new_h = H
#             new_w = int(H * img_ratio)
#         elsw - W) // 2
#         top = (new_h - H) // 2
#         right = left + W
#         bottom = top + H

#         cropped = resized.crop((left, top, right, bottom))
#         exports[name] = cropped

#             # Image is taller → crop height
#             new_w = W
#             new_h = int(W / img_ratio)

#         resized = image.resize((new_w, new_h), Image.LANCZOS)

#         left = (new_
#     return exports

