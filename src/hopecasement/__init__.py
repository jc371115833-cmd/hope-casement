import sys


def main() -> None:
    if "--change" in sys.argv:
        from hopecasement.changer import change_wallpaper
        change_wallpaper()
    else:
        from hopecasement.ui.app import run_ui
        run_ui()


if __name__ == "__main__":
    main()
