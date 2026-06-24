import shutil
from datetime import datetime
from pathlib import Path

from hopecasement.config import Config, get_history_dir, load_config
from hopecasement.image import get_background
from hopecasement.quotes import get_random_quote
from hopecasement.renderer import render_wallpaper
from hopecasement.wallpaper import set_wallpaper


_HISTORY_KEEP = 200  # cap the archive so it can't grow without bound


def _save_to_history(wallpaper: Path) -> None:
    history = get_history_dir()
    history.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wallpaper, history / f"{datetime.now():%Y%m%d_%H%M%S}.png")
    # Timestamp names sort chronologically, so drop the oldest beyond the cap.
    saved = sorted(history.glob("*.png"))
    for old in saved[:-_HISTORY_KEEP]:
        old.unlink(missing_ok=True)


def change_wallpaper(cfg: Config | None = None) -> None:
    if cfg is None:
        cfg = load_config()
    quote = get_random_quote()
    bg = get_background(cfg.background_colors, cfg.images_dir)
    tmp = render_wallpaper(bg, quote, cfg)
    set_wallpaper(tmp)
    if cfg.save_history:
        _save_to_history(tmp)
