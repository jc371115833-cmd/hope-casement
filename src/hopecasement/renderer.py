import ctypes
import os
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from hopecasement.config import Config, get_appdata_dir

_FONT_CANDIDATES = ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc"]
_FONTS_DIR = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
_CANT_START_LINE = frozenset('，。、；：！？）】」』》〉…·—')

# Common Windows fonts: display name → font filename
FONT_CHOICES: dict[str, str] = {
    "微软雅黑": "msyh.ttc",
    "黑体": "simhei.ttf",
    "宋体": "simsun.ttc",
    "楷体": "simkai.ttf",
    "仿宋": "simfang.ttf",
    "等线": "Deng.ttf",
}
DEFAULT_FONT_FILE = "msyh.ttc"


def available_fonts() -> dict[str, str]:
    """FONT_CHOICES limited to fonts actually installed on this machine."""
    found = {name: f for name, f in FONT_CHOICES.items() if (_FONTS_DIR / f).exists()}
    return found or dict(FONT_CHOICES)


def _screen_size() -> tuple[int, int]:
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def _load_font(size: int, font_file: str = "") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = ([font_file] if font_file else []) + _FONT_CANDIDATES
    for name in candidates:
        path = _FONTS_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _cover_resize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Scale to cover the target size (preserve aspect), then center-crop to it."""
    iw, ih = img.size
    scale = max(target_w / iw, target_h / ih)
    img = img.resize((max(1, round(iw * scale)), max(1, round(ih * scale))), Image.LANCZOS)
    left = (img.width - target_w) // 2
    top = (img.height - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _measure_text(font, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(text: str, font, max_width: int, max_lines: int) -> list[str]:
    w, _ = _measure_text(font, text)
    if w <= max_width:
        return [text]

    lines: list[str] = []
    current = ""
    truncated = False
    for char in text:
        trial = current + char
        tw, _ = _measure_text(font, trial)
        if tw > max_width and current:
            lines.append(current)
            if len(lines) >= max_lines:
                truncated = True
                break
            current = char
        else:
            current = trial
    else:
        if current and len(lines) < max_lines:
            lines.append(current)

    if truncated:
        last = lines[-1]
        while last and _measure_text(font, last + "…")[0] > max_width:
            last = last[:-1]
        lines[-1] = last + "…"

    return lines or [text]


def _fix_kinsoku(lines: list[str]) -> list[str]:
    """把行首的标点挪到上一行末尾（避头点）。"""
    result = list(lines)
    for i in range(1, len(result)):
        while result[i] and result[i][0] in _CANT_START_LINE:
            result[i - 1] += result[i][0]
            result[i] = result[i][1:]
    return [ln for ln in result if ln]


def _calc_position(
    img_w: int,
    img_h: int,
    text_w: int,
    text_h: int,
    text_x: int,
    text_y: int,
) -> tuple[int, int]:
    margin = 20
    x = int(img_w * text_x / 100) - text_w // 2
    y = int(img_h * text_y / 100) - text_h // 2
    x = max(margin, min(img_w - text_w - margin, x))
    y = max(margin, min(img_h - text_h - margin, y))
    return x, y


def render_wallpaper(background: Path | str, quote: str, cfg: Config) -> Path:
    screen_w, screen_h = _screen_size()
    if isinstance(background, str):
        rgb = ImageColor.getrgb(background)
        img = Image.new("RGBA", (screen_w, screen_h), (*rgb, 255))
    else:
        img = Image.open(background)
        img.draft("RGB", (screen_w, screen_h))  # fast approximate downscale while decoding JPEG
        img = _cover_resize(img.convert("RGBA"), screen_w, screen_h)
    img_w, img_h = img.size

    font_size_px = max(12, int(img_h * cfg.font_size / 100))
    font = _load_font(font_size_px, cfg.font_file)
    line_h = int(font_size_px * cfg.line_spacing)
    max_lines = max(1, (img_h - 80) // line_h)
    raw_lines = _wrap_text(quote, font, int(img_w * cfg.text_width_ratio), max_lines)
    lines = _fix_kinsoku(raw_lines)

    text_h = line_h * len(lines)
    text_w = max(_measure_text(font, ln)[0] for ln in lines)

    x, y = _calc_position(img_w, img_h, text_w, text_h, cfg.text_x, cfg.text_y)

    result_img = img
    if cfg.show_text:
        text_rgb = ImageColor.getrgb(cfg.font_color)
        shadow_rgb = ImageColor.getrgb(cfg.shadow_color)
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        if cfg.text_bg_opacity > 0:
            bg_rgb = ImageColor.getrgb(cfg.text_bg_color)
            bg_alpha = round(255 * cfg.text_bg_opacity / 100)
            ascent, descent = font.getmetrics()
            content_h = (len(lines) - 1) * line_h + ascent + descent
            pad_x = int(font_size_px * 0.3)
            pad_y = int(font_size_px * 0.12)
            draw.rounded_rectangle(
                (x - pad_x, y - pad_y, x + text_w + pad_x, y + content_h + pad_y),
                radius=int(font_size_px * 0.2),
                fill=(*bg_rgb, bg_alpha),
            )
        for i, line in enumerate(lines):
            lx = x
            ly = y + i * line_h
            draw.text((lx + cfg.shadow_offset, ly + cfg.shadow_offset), line,
                      font=font, fill=(*shadow_rgb, 180))
            draw.text((lx, ly), line, font=font, fill=(*text_rgb, 255))
        result_img = Image.alpha_composite(img, overlay)

    result = result_img.convert("RGB")

    out = get_appdata_dir() / "current_wallpaper.png"
    result.save(str(out), "PNG")
    return out
