import sys
from importlib.metadata import version

__version__ = version("hopecasement")


def _log_change_error() -> None:
    """Record a failed scheduled --change run so silent failures are diagnosable."""
    import datetime
    import traceback

    try:
        from hopecasement.config import get_appdata_dir
        log = get_appdata_dir() / "error.log"
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] 换壁纸失败\n")
            f.write(traceback.format_exc())
    except Exception:
        pass


def main() -> int:
    if "--change" in sys.argv:
        try:
            from hopecasement import i18n
            from hopecasement.changer import change_wallpaper
            from hopecasement.config import load_config
            cfg = load_config()
            i18n.select_language(cfg.language)
            change_wallpaper(cfg)
        except Exception:
            _log_change_error()
            return 1
    else:
        from hopecasement.ui.app import run_ui
        run_ui()
    return 0


if __name__ == "__main__":
    sys.exit(main())
