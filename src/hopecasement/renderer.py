import ctypes
import os
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from hopecasement.config import Config, get_appdata_dir

_FONT_CANDIDATES = ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc"]
_FONTS_DIR = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
_CANT_START_LINE = frozenset('，。、；：！？）】」』》〉…·—”’')
_CANT_END_LINE = frozenset('（【「『《〈“‘')

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

    result = result_img.convert("RGB")

    out = get_appdata_dir() / "current_wallpaper.png"
    result.save(str(out), "PNG")
    return out
