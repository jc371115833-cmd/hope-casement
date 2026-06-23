import sys

__version__ = "0.1.0"


def _log_change_error() -> None:
    """Record why a scheduled --change run failed (it has no UI to show errors)."""
    try:
        import traceback
        from datetime import datetime

        from hopecasement.config import get_appdata_dir
        log = get_appdata_dir() / "change_error.log"
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}]\n{traceback.format_exc()}")
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
