from hopecasement.config import load_config
from hopecasement.image import get_background
from hopecasement.quotes import get_random_quote
from hopecasement.renderer import render_wallpaper
from hopecasement.wallpaper import set_wallpaper


def change_wallpaper() -> None:
    cfg = load_config()
    quote = get_random_quote()
    bg = get_background(cfg.background_colors)
    tmp = render_wallpaper(bg, quote, cfg)
    set_wallpaper(tmp)
