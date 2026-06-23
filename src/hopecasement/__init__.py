import sys

__version__ = "0.1.0"


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


def main() -> None:
    if "--change" in sys.argv:
        from hopecasement.changer import change_wallpaper
        try:
            change_wallpaper()
        except Exception:
            _log_change_error()
    else:
        from hopecasement.ui.app import run_ui
        run_ui()


if __name__ == "__main__":
    main()
