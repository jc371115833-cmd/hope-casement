import re
import shutil
from datetime import datetime
from pathlib import Path

from hopecasement.config import Config, get_history_dir, load_config
from hopecasement.image import get_background
from hopecasement.quotes import get_random_quote
from hopecasement.renderer import render_wallpaper
from hopecasement.storage import atomic_output
from hopecasement.wallpaper import set_wallpaper, wallpaper_change_lock


_HISTORY_KEEP = 200  # cap the archive so it can't grow without bound
_HISTORY_FILENAME = re.compile(r"([0-9]{8}_[0-9]{6})(?:_([0-9]{6}))?\.png")


def _save_to_history(wallpaper: Path) -> None:
    history = get_history_dir()
    history.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = []
    sequence = 0
    for path in history.glob("*.png"):
        match = _HISTORY_FILENAME.fullmatch(path.name)
        if match and path.is_file():
            try:
                saved.append((path.stat().st_mtime_ns, path))
            except FileNotFoundError:
                continue
            if match[1] == stamp:
                sequence = max(sequence, int(match[2] or 0) + 1)
    suffix = f"_{sequence:06d}" if sequence else ""
    target = history / f"{stamp}{suffix}.png"
    with atomic_output(target, overwrite=False) as temp:
        shutil.copyfile(wallpaper, temp)
    # Order by file time across daylight-saving clock changes. Always keep this save.
    excess = max(0, len(saved) + 1 - _HISTORY_KEEP)
    for _, old in sorted(saved)[:excess]:
        old.unlink(missing_ok=True)


def change_wallpaper(cfg: Config | None = None) -> None:
    if cfg is None:
        cfg = load_config()
    quote = get_random_quote() if cfg.show_text else ""
    bg = get_background(cfg.background_colors, cfg.images_dir)
    with wallpaper_change_lock():
        output = render_wallpaper(bg, quote, cfg)
        set_wallpaper(output)
        if cfg.save_history:
            _save_to_history(output)
