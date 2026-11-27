[简体中文](CONTRIBUTING.md) | **English**

# Contributing

Thanks for your interest in **HopeCasement 来日窗笺**! This guide will help you get started with development.

## Getting started

On Windows, use Python 3.12 and uv. From the root of your checkout, run:

```powershell
uv sync --locked
uv run hopecasement
```

Run `uv run --locked python -m unittest discover -s tests -v` for regression tests. They use temporary files and stand-ins for Windows system calls. See the [engineering guides (Chinese)](docs/index.md#维护软件) for the architecture, test scope and installer build. When behavior changes, update its guide and regression tests in the same PR and describe what you verified on Windows.

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

1. Search [Issues](https://github.com/jc371115833-cmd/hope-casement/issues) / [Pull Requests](https://github.com/jc371115833-cmd/hope-casement/pulls) first to avoid duplicate work.
2. Fork the repo and branch off `main`.
3. Make your changes; make sure they run locally and follow the code style.
4. Open a PR with a title following the commit convention, and describe the purpose and impact in the body.
5. Wait for a maintainer review; for larger changes, open an Issue to discuss direction first.

## Feedback

- 🐛 **Bug reports**: open an [Issue](https://github.com/jc371115833-cmd/hope-casement/issues)
- 💡 **Feature requests**: open an [Issue](https://github.com/jc371115833-cmd/hope-casement/issues)
- 💬 **General discussion**: head to [Discussions](https://github.com/jc371115833-cmd/hope-casement/discussions)
