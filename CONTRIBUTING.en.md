[简体中文](CONTRIBUTING.md) | **English**

# Contributing

Thanks for your interest in **HopeCasement 来日窗笺**! This guide will help you get started with development.

## Development Setup

The project currently targets **Windows 10 / 11** only, and requires **Python 3.12+** and [uv](https://github.com/astral-sh/uv).

```shell
git clone https://github.com/jc371115833-cmd/hope-casement.git
cd hope-casement
uv sync                              # install dependencies
uv run python -m hopecasement        # launch the config window
```

Test just the wallpaper-change flow (without the UI):

```shell
uv run python -c "from hopecasement.changer import change_wallpaper; change_wallpaper()"
```

Entry points: `HopeCasement.exe` opens the config window; `HopeCasement.exe --change` changes the wallpaper directly (called by Windows Task Scheduler).

> Scheduling (`scheduler.py`) relies on the packaged exe path, so it **only works in the built version** and cannot be tested in development mode.

## Project Structure

**Tech stack**: Python · [customtkinter](https://github.com/TomSchimansky/CustomTkinter) (UI) · [Pillow](https://python-pillow.org/) (text rendering) · Windows `schtasks.exe` (scheduling) · ctypes (setting the wallpaper).

**User data location**: next to the exe when packaged; in `userdata\` at the project root in development mode.

| File / Folder           | Purpose                                  |
| ----------------------- | ---------------------------------------- |
| `config.json`           | All settings                             |
| `quotes.txt`            | Quote library, one line per quote        |
| `backgrounds\`          | User-provided background images          |
| `current_wallpaper.png` | Current wallpaper (overwritten by app)   |
| `history\`              | Wallpaper archive (when "Save history" is on) |

## Branch & Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/): `<type>: <summary>`. Common types:

| Type       | Meaning                          |
| ---------- | -------------------------------- |
| `feat`     | New feature                      |
| `fix`      | Bug fix                          |
| `docs`     | Documentation                    |
| `style`    | Formatting only, no logic change |
| `refactor` | Refactor (not a feature or fix)  |
| `perf`     | Performance improvement          |
| `chore`    | Build, dependencies, misc        |

Example: `feat: add font selection` / `fix: resolve blurry text on high DPI`

## Pull Request Flow

1. Search [Issues](../../issues) / [Pull Requests](../../pulls) first to avoid duplicate work.
2. Fork the repo and branch off `main`.
3. Make your changes; make sure they run locally and follow the code style.
4. Open a PR with a title following the commit convention, and describe the purpose and impact in the body.
5. Wait for a maintainer review; for larger changes, open an Issue to discuss direction first.

## Feedback

- 🐛 **Bug reports**: open an [Issue](../../issues)
- 💡 **Feature requests**: open an [Issue](../../issues)
- 💬 **General discussion**: head to [Discussions](../../discussions)
