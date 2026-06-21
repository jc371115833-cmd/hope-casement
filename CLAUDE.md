# CLAUDE.md

## 项目名称

**来日窗笺 (HopeCasement)**

## 设计隐喻

古人书箴言于笺、贴于窗，抬目自省。本软件以"窗"喻屏幕，以"笺"作壁纸，每日择良言铺于桌面，以字句勉励自身、奔赴来日。

## Slogan

> 一纸笺文赴来日，日日新墨落屏窗。
> Words on screen, growth every coming day.

## 核心目标

用户维护背景图库和句子库，程序随机组合后渲染成带文字的壁纸，自动设为桌面壁纸。**单机、离线、零网络依赖、无广告、轻量、日常无感。**

## 技术栈

- Python 3.12+
- uv 管理依赖与虚拟环境
- hatchling 构建
- customtkinter UI（配置窗口，非常驻）
- Pillow 图片渲染
- Windows Task Scheduler（schtasks.exe）定时调度
- PyInstaller 打包为单文件 exe
- Inno Setup 制作安装包

## 代码规范

**符合 Python 简洁之道，面向公开发布：**

- 表达清晰优先于简短，不写"聪明代码"
- 无注释的标准库用法，只在 WHY 非显而易见时加注释
- 无调试 print，无注释掉的代码
- 函数职责单一，模块短小聚焦
- 类型注解完整（入参、返回值）

## 模块结构

```
src/hopecasement/
├── __init__.py      # 入口：--change → changer，否则 → UI
├── config.py        # Config dataclass + JSON 读写
├── quotes.py        # 句子库读写（quotes.txt，一行一句）
├── image.py         # 合并内置图 + 用户图，随机选取
├── renderer.py      # Pillow 文字渲染 → 临时 PNG
├── scheduler.py     # schtasks.exe 封装（4 种计划模式）
├── changer.py       # 整合：取图 → 取句 → 渲染 → 设壁纸
├── wallpaper.py     # set_wallpaper()：Windows ctypes API
└── ui/
    ├── app.py           # 主窗口
    ├── tab_quotes.py    # 句子库 Tab
    ├── tab_images.py    # 背景图 Tab
    └── tab_schedule.py  # 文字样式 + 换壁纸计划 Tab
```

## 用户数据路径

| 内容 | 路径 |
|---|---|
| 配置 | `%APPDATA%\HopeCasement\config.json` |
| 句子库 | `%APPDATA%\HopeCasement\quotes.txt` |
| 用户背景图 | `%APPDATA%\HopeCasement\backgrounds\` |
| 渲染输出文件 | `%APPDATA%\HopeCasement\current_wallpaper.png` |
| 内置背景图 | exe 同目录 `assets/images/` |

## 入口逻辑

- `HopeCasement.exe` → 打开 UI（配置窗口）
- `HopeCasement.exe --change` → 直接换壁纸（任务计划程序调用）

## 常用命令

```bash
# 开发运行
uv run python -m hopecasement

# 测试核心流程
uv run python -c "from hopecasement.changer import change_wallpaper; change_wallpaper()"

# 打包 exe
uv run pyinstaller HopeCasement.spec --clean

# 打包安装包（需先打包 exe）
"E:\software\Inno Setup 7\ISCC.exe" setup\Hopecasement.iss
```
