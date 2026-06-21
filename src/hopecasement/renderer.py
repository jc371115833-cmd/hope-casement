from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from hopecasement.config import Config, get_appdata_dir

_FONT_CANDIDATES = ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc"]
_FONTS_DIR = Path("C:/Windows/Fonts")
_MAX_LINES = 3
_LINE_SPACING_RATIO = 1.4
_WRAP_WIDTH_RATIO = 0.75


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in _FONT_CANDIDATES:
        path = _FONTS_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _measure_text(font, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(text: str, font, max_width: int) -> list[str]:
    w, _ = _measure_text(font, text)
    if w <= max_width:
        return [text]

    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        tw, _ = _measure_text(font, trial)
        if tw > max_width and current:
            lines.append(current)
            if len(lines) >= _MAX_LINES:
                break
            current = char
        else:
            current = trial
    else:
        if current and len(lines) < _MAX_LINES:
            lines.append(current)

    if len(lines) == _MAX_LINES and current and current not in lines[-1]:
        last = lines[-1]
        while last and _measure_text(font, last + "…")[0] > max_width:
            last = last[:-1]
        lines[-1] = last + "…"

    return lines or [text]


def _calc_position(
    img_w: int,
    img_h: int,
    text_w: int,
    text_h: int,
    position: str,
    padding: int,
) -> tuple[int, int]:
    cx = (img_w - text_w) // 2
    cy = (img_h - text_h) // 2
    positions = {
        "top_left":      (padding, padding),
        "top_center":    (cx, padding),
        "center":        (cx, cy),
        "bottom_center": (cx, img_h - text_h - padding),
        "bottom_right":  (img_w - text_w - padding, img_h - text_h - padding),
    }
    return positions.get(position, positions["bottom_center"])


def render_wallpaper(background: Path, quote: str, cfg: Config) -> Path:
    font = _load_font(cfg.font_size)
    img = Image.open(background).convert("RGBA")
    img_w, img_h = img.size

    lines = _wrap_text(quote, font, int(img_w * _WRAP_WIDTH_RATIO))
    line_h = int(cfg.font_size * _LINE_SPACING_RATIO)
    text_h = line_h * len(lines)
    text_w = max(_measure_text(font, ln)[0] for ln in lines)

    x, y = _calc_position(img_w, img_h, text_w, text_h, cfg.text_position, cfg.text_padding)

    text_rgb = ImageColor.getrgb(cfg.font_color)
    shadow_rgb = ImageColor.getrgb(cfg.shadow_color)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for i, line in enumerate(lines):
        lx = x
        ly = y + i * line_h
        draw.text((lx + cfg.shadow_offset, ly + cfg.shadow_offset), line,
                  font=font, fill=(*shadow_rgb, 180))
        draw.text((lx, ly), line, font=font, fill=(*text_rgb, 255))

    result = Image.alpha_composite(img, overlay).convert("RGB")

    out = get_appdata_dir() / "current_wallpaper.png"
    result.save(str(out), "PNG")
    return out
