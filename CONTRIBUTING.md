# 贡献指南

感谢你愿意为「来日窗笺 HopeCasement」出一份力！本指南帮助你快速上手开发、了解协作规范。无论是反馈问题、提建议，还是贡献代码，都非常欢迎。

## 反馈问题

- 🐛 **Bug 反馈**：在 [Issues](../../issues) 提交，附上你的 Windows 版本、复现步骤、期望与实际结果；若有报错，附上安装目录下的 `error.log`。
- 💡 **功能建议**：在 [Issues](../../issues) 描述你的想法和使用场景。

## 开发环境

本项目仅面向 **Windows 10 / 11**，需要 **Python 3.12+** 和 [uv](https://github.com/astral-sh/uv)。

```shell
git clone https://github.com/jc371115833-cmd/hope-casement.git
cd hope-casement
uv sync                              # 安装依赖
uv run python -m hopecasement        # 运行配置窗口
```

只测试换壁纸核心流程（不启动 UI）：

```shell
uv run python -c "from hopecasement.changer import change_wallpaper; change_wallpaper()"
```

入口逻辑：`HopeCasement.exe` 打开配置窗口；`HopeCasement.exe --change` 直接换壁纸（供 Windows 任务计划程序调用）。

> 定时调度（`scheduler.py`）依赖打包后的 exe 路径，**仅在打包版中生效**，开发模式下无法测试。

## 分支与提交规范

从 `main` 切出功能分支，分支名与改动类型对应，例如 `feat/text-shadow`、`fix/dpi-blur`、`docs/readme`。

提交信息采用 [Conventional Commits](https://www.conventionalcommits.org/) 风格：`<类型>: <简述>`。常用类型：

| 类型 | 含义 |
|---|---|
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `docs` | 文档 |
| `style` | 不影响逻辑的格式调整 |
| `refactor` | 重构（非新增、非修复） |
| `perf` | 性能优化 |
| `chore` | 构建、依赖、杂项 |

示例：`feat: 支持文字描边` / `fix: 修复高 DPI 下壁纸发虚`。

## 代码规范

- 表达清晰优先于简短，不写"聪明代码"。
- 注释只在「为什么这么做」不显而易见时才加，不解释标准库的常规用法。
- 不留调试 `print` 和注释掉的代码。
- 函数职责单一，模块短小聚焦。
- 入参与返回值都写类型注解。

提交前请确保代码能正常运行。推荐用 [ruff](https://docs.astral.sh/ruff/) 做静态检查与格式化：

```shell
uvx ruff check .                     # 静态检查
uvx ruff format .                    # 自动格式化
```

## 提交 Pull Request

1. 先在 [Issues](../../issues) / [Pull Requests](../../pulls) 搜一下，避免重复劳动。
2. Fork 仓库，从 `main` 切出分支。
3. 完成修改，确保本地运行正常、符合代码规范。
4. 提交 PR，标题遵循上面的提交规范，正文简述改动目的与影响。
5. 等待维护者 Review；较大的改动建议先开 Issue 讨论方向。

## 项目结构

```
src/hopecasement/
├── __init__.py      # 入口：--change → 换壁纸，否则 → UI
├── config.py        # Config 配置 + JSON 读写
├── quotes.py        # 句子库读写
├── image.py         # 背景选取（纯色或用户图片）
├── renderer.py      # Pillow 文字渲染 → PNG
├── scheduler.py     # schtasks.exe 封装（定时调度）
├── changer.py       # 整合：取图 → 取句 → 渲染 → 设壁纸
├── wallpaper.py     # 调用 Windows API 设置壁纸
├── single_instance.py  # 单实例运行
├── i18n.py          # 中英文文案
└── ui/              # 配置窗口（customtkinter）
```

**技术栈**：Python · [customtkinter](https://github.com/TomSchimansky/CustomTkinter)（界面）· [Pillow](https://python-pillow.org/)（文字渲染）· Windows `schtasks.exe`（定时调度）· ctypes（设置壁纸）。

**用户数据位置**：打包后存在 exe 同目录，开发模式下存在项目根目录的 `userdata\`。

| 文件 / 目录 | 用途 |
|---|---|
| `config.json` | 所有设置 |
| `quotes.txt` | 句子库，一行一句 |
| `backgrounds\` | 用户自定义背景图 |
| `current_wallpaper.png` | 当前壁纸（程序自动覆盖） |
| `history\` | 历史壁纸归档（开启「保存历史」后） |

## 打包与发布

> 仅维护者发版时需要。

**1. 同步版本号**（三处必须一致）：`pyproject.toml` 的 `version`、`src/hopecasement/__init__.py` 的 `__version__`、`setup/Hopecasement.iss` 的 `MyAppVersion`。

**2. 打包 exe**（[PyInstaller](https://pyinstaller.org/) 配置已写好）：

```shell
uv run pyinstaller HopeCasement.spec --clean
```

产物 `dist\HopeCasement.exe`，打完先运行确认无误。

**3. 制作安装包**（使用 [Inno Setup](https://jrsoftware.org/isinfo.php)，需先完成第 2 步）：

```shell
ISCC.exe setup\Hopecasement.iss
```

产物 `setup\HopeCasement.exe`。可选 [Inno Setup 简体中文汉化包](https://github.com/kira-96/Inno-Setup-Chinese-Simplified-Translation)。

**4. 打 tag 并发布**：

```shell
git tag v0.1.0
git push origin v0.1.0
```

在 GitHub 仓库 Releases 页新建 Release，选择该 tag，上传 `setup\HopeCasement.exe` 作为附件。
