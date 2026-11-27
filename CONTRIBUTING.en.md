[简体中文](CONTRIBUTING.md) | **English**

# Contributing

Use Windows, Python 3.12 and uv. Run these commands from the repository root.

```powershell
uv sync --locked
uv run --locked hopecasement
```

**Change Now** changes your Windows desktop. To exercise the rendering and scheduling code with temporary files and mock Windows calls, run `uv run --locked python -m unittest discover -s tests -v`. The [feature map (Chinese)](docs/architecture/overview.md#按改动定位) links each feature to its source, guide and tests.

## Submitting a change

1. Check existing [issues](https://github.com/jc371115833-cmd/hope-casement/issues) and [pull requests](https://github.com/jc371115833-cmd/hope-casement/pulls). Consider discussing larger changes in an issue first. Create a branch from `main` in your fork.
2. Update the user guide and regression tests when behavior changes. Use a dedicated Windows account or VM to verify installation, upgrades and actual scheduled runs. See the [release checks (Chinese)](docs/development/release.md#安装版验收).
3. Use [Conventional Commits](https://www.conventionalcommits.org/) in commit messages and PR titles, for example `fix: apply the daily schedule when saving on exit`. Other common types include `feat`, `docs`, `style`, `refactor`, `perf` and `chore`.
4. Describe the purpose and impact in the PR. List the tests you ran, observations from Windows and any checks still pending.

## Reporting a problem

Include your app and Windows versions, steps to reproduce, and the expected and actual results. For feature requests, describe the workflow you want to support. Use [Discussions](https://github.com/jc371115833-cmd/hope-casement/discussions) for general questions.
