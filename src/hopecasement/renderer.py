import ctypes
import os
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from hopecasement.config import Config, get_appdata_dir

_FONT_CANDIDATES = ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc"]
_FONTS_DIR = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
_CANT_START_LINE = frozenset('，。、；：！？）】」』》〉…·—”’')
_CANT_END_LINE = frozenset('（【「『《〈“‘')

# Common Windows fonts (display names are localized in i18n, keyed by filename).
FONT_FILES = ["msyh.ttc", "simhei.ttf", "simsun.ttc", "simkai.ttf", "simfang.ttf", "Deng.ttf"]
DEFAULT_FONT_FILE = "msyh.ttc"


def available_font_files() -> list[str]:
    """FONT_FILES limited to fonts actually installed on this machine."""
    found = [f for f in FONT_FILES if (_FONTS_DIR / f).exists()]
    return found or list(FONT_FILES)


def _screen_size() -> tuple[int, int]:
    """Physical pixel resolution of the primary monitor.

    GetSystemMetrics returns the DPI-scaled (logical) size when the process isn't
    DPI-aware — rendering at that size makes Windows upscale the wallpaper and blur
    the text. DESKTOPHORZRES/VERTRES report the true physical pixels regardless.
    """
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    hdc = user32.GetDC(0)
    try:
        _DESKTOPVERTRES, _DESKTOPHORZRES = 117, 118
        w = gdi32.GetDeviceCaps(hdc, _DESKTOPHORZRES)
        h = gdi32.GetDeviceCaps(hdc, _DESKTOPVERTRES)
    finally:
        user32.ReleaseDC(0, hdc)
    if w and h:
        return w, h
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


@lru_cache(maxsize=16)
def _load_font(size: int, font_file: str = "") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = ([font_file] if font_file else []) + _FONT_CANDIDATES
    for name in candidates:
        path = _FONTS_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _draw_text_line(draw, line: str, lx: float, ly: float, font, gap: float, fill) -> None:
    """Draw one line; if gap > 0, advance each character by its width + gap (justify)."""
    if gap <= 0:
        draw.text((lx, ly), line, font=font, fill=fill)
        return
    cx = lx
    for ch in line:
        draw.text((cx, ly), ch, font=font, fill=fill)
        cx += font.getlength(ch) + gap


def _cover_resize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Scale to cover the target size (preserve aspect), then center-crop to it."""
    iw, ih = img.size
    scale = max(target_w / iw, target_h / ih)
    img = img.resize((max(1, round(iw * scale)), max(1, round(ih * scale))), Image.LANCZOS)
    left = (img.width - target_w) // 2
    top = (img.height - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _wrap_text(text: str, font, max_width: int, max_lines: int) -> list[str]:
    if font.getlength(text) <= max_width:
        return [text]

    lines: list[str] = []
    current = ""
    current_w = 0.0
    truncated = False
    for char in text:
        cw = font.getlength(char)
        if current and current_w + cw > max_width:
            lines.append(current)
            if len(lines) >= max_lines:
                truncated = True
                break
            current, current_w = char, cw
        else:
            current += char
            current_w += cw
    else:
        if current and len(lines) < max_lines:
            lines.append(current)

    if truncated:
        last = lines[-1]
        ellipsis = font.getlength("…")
        while last and font.getlength(last) + ellipsis > max_width:
            last = last[:-1]
        lines[-1] = last + "…"

    return lines or [text]


def _fix_kinsoku(lines: list[str]) -> list[str]:
    """避头尾标点：行首的收口标点挪到上一行末尾，行尾的开口标点挪到下一行开头。"""
    result = list(lines)
    for i in range(1, len(result)):
        while result[i] and result[i][0] in _CANT_START_LINE:
            result[i - 1] += result[i][0]
            result[i] = result[i][1:]
    for i in range(len(result) - 1):
        while result[i] and result[i][-1] in _CANT_END_LINE:
            result[i + 1] = result[i][-1] + result[i + 1]
            result[i] = result[i][:-1]
    return [ln for ln in result if ln]


def _align_width(font, line: str) -> float:
    """Line width for alignment, excluding trailing punctuation (it hangs in the margin)."""
    body = line
    while body and body[-1] in _CANT_START_LINE:
        body = body[:-1]
    return font.getlength(body)


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


def compose_wallpaper(
    background: Path | str, quote: str, cfg: Config, size: tuple[int, int]
) -> Image.Image:
    """Compose an RGB image for the supplied canvas size, in pixels."""
    if isinstance(background, str):
        rgb = ImageColor.getrgb(background)
        img = Image.new("RGBA", size, (*rgb, 255))
    else:
        with Image.open(background) as source:
            source.draft("RGB", size)  # fast approximate downscale while decoding JPEG
            img = _cover_resize(source.convert("RGBA"), *size)
    img_w, img_h = img.size

    font_size_px = max(12, int(img_h * cfg.font_size / 100))
    font = _load_font(font_size_px, cfg.font_file)
    line_h = int(font_size_px * cfg.line_spacing)
    max_lines = max(1, (img_h - 80) // line_h)
    raw_lines = _wrap_text(quote, font, int(img_w * cfg.text_width_ratio), max_lines)
    lines = _fix_kinsoku(raw_lines)

    full_widths = [font.getlength(ln) for ln in lines]
    align_widths = [_align_width(font, ln) for ln in lines]
    text_h = line_h * len(lines)
    text_w = int(max(align_widths))

    x, y = _calc_position(img_w, img_h, text_w, text_h, cfg.text_x, cfg.text_y)

    result_img = img
    if cfg.show_text:
        text_rgb = ImageColor.getrgb(cfg.font_color)
        shadow_rgb = ImageColor.getrgb(cfg.shadow_color)
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # First pass: work out each line's left edge and inter-character gap.
        last_i = len(lines) - 1
        max_gap = font_size_px  # cap stretch at ~one character width, else it looks too sparse
        layout: list[tuple[float, float]] = []  # (lx, gap) per line
        for i, line in enumerate(lines):
            aw = align_widths[i]
            gap = 0.0
            # Justify every line but the last when left/right aligned, so both edges line up.
            justify = (cfg.text_align in ("left", "right")
                       and i != last_i and len(line) > 1 and text_w > aw)
            if justify:
                gap = (text_w - aw) / (len(line) - 1)
                if gap > max_gap:  # too few characters to fill the width nicely
                    gap = 0.0
                    justify = False
            if justify or cfg.text_align == "left":
                lx = x
            elif cfg.text_align == "center":
                lx = x + (text_w - aw) / 2
            else:  # right
                lx = x + (text_w - aw)
            layout.append((lx, gap))

        if cfg.text_bg_opacity > 0:
            bg_rgb = ImageColor.getrgb(cfg.text_bg_color)
            bg_alpha = round(255 * cfg.text_bg_opacity / 100)
            ascent, descent = font.getmetrics()
            content_h = (len(lines) - 1) * line_h + ascent + descent
            pad_x = int(font_size_px * 0.3)
            pad_y = int(font_size_px * 0.12)
            box_left = min(lx for lx, _ in layout)
            box_right = max(lx + full_widths[i] + gap * (len(lines[i]) - 1)
                            for i, (lx, gap) in enumerate(layout))
            draw.rounded_rectangle(
                (box_left - pad_x, y - pad_y, box_right + pad_x, y + content_h + pad_y),
                radius=int(font_size_px * 0.2),
                fill=(*bg_rgb, bg_alpha),
            )

        for i, line in enumerate(lines):
            lx, gap = layout[i]
            ly = y + i * line_h
            _draw_text_line(draw, line, lx + cfg.shadow_offset, ly + cfg.shadow_offset,
                            font, gap, (*shadow_rgb, 180))
            _draw_text_line(draw, line, lx, ly, font, gap, (*text_rgb, 255))
        result_img = Image.alpha_composite(img, overlay)

    return result_img.convert("RGB")


def render_wallpaper(background: Path | str, quote: str, cfg: Config) -> Path:
    result = compose_wallpaper(background, quote, cfg, _screen_size())
    out = get_appdata_dir() / "current_wallpaper.png"
    # compress_level=1: wallpaper file size is irrelevant; this is much faster than the default.
    result.save(str(out), "PNG", compress_level=1)
    return out
