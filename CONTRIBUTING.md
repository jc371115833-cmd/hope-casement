# 贡献指南

感谢你愿意为「来日窗笺 HopeCasement」出一份力！无论是反馈问题、提建议，还是贡献代码，都非常欢迎。

## 反馈问题 / 提建议

- 发现 Bug 或有功能想法，请在 [Issues](../../issues) 提交。
- 报告 Bug 时，尽量附上：你的 Windows 版本、复现步骤、期望结果与实际结果。若有报错，可附上安装目录下的 `error.log`。

## 贡献代码

1. Fork 本仓库并新建分支。
2. 完成修改，确保能正常运行。
3. 提交 Pull Request，并简要说明改动的目的。

小改动可直接提 PR；较大的改动建议先开 Issue 讨论方向，避免白做。

## 开发环境

需要 Python 3.12+ 和 [uv](https://github.com/astral-sh/uv)。

```shell
uv sync                              # 安装依赖
uv run python -m hopecasement        # 运行 UI
```

测试换壁纸核心流程（不启动 UI）：

```shell
uv run python -c "from hopecasement.changer import change_wallpaper; change_wallpaper()"
```

入口逻辑：`HopeCasement.exe` 打开配置窗口；`HopeCasement.exe --change` 直接换壁纸（供 Windows 任务计划程序调用）。

## 用户数据位置

打包成 exe 后，数据存在 exe 同目录；开发模式下存在项目根目录的 `userdata\`。

| 文件 / 目录 | 用途 |
|---|---|
| `config.json` | 所有设置 |
| `quotes.txt` | 句子库，一行一句 |
| `backgrounds\` | 用户自定义背景图 |
| `current_wallpaper.png` | 当前壁纸（程序自动覆盖） |
| `history\` | 历史壁纸归档（开启「保存历史」后） |

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

## 技术栈

Python · [customtkinter](https://github.com/TomSchimansky/CustomTkinter)（界面）· [Pillow](https://python-pillow.org/)（文字渲染）· Windows `schtasks.exe`（定时调度）· ctypes（设置壁纸）。

## 代码规范

- 表达清晰优先于简短，不写"聪明代码"。
- 注释只在「为什么这么做」不显而易见时才加，不解释标准库的常规用法。
- 不留调试 `print` 和注释掉的代码。
- 函数职责单一，模块短小聚焦。
- 入参与返回值都写类型注解。

## 打包发布

打包 exe（[PyInstaller](https://pyinstaller.org/) 配置已写好）：

```shell
uv run pyinstaller HopeCasement.spec --clean
```

制作安装包（需先打包 exe，使用 [Inno Setup](https://jrsoftware.org/isinfo.php)）：

```shell
ISCC.exe setup\Hopecasement.iss
```

产物在 `setup\HopeCasement.exe`。可选 [Inno Setup 简体中文汉化包](https://github.com/kira-96/Inno-Setup-Chinese-Simplified-Translation)。
