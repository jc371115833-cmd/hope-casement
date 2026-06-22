# 来日窗笺 HopeCasement

> 一纸笺文赴来日，日日新墨落屏窗。
> Words on screen, growth every coming day.

每日从句子库随机取一句良言，与背景图组合渲染成壁纸，自动设为 Windows 桌面壁纸。
**单机离线、零网络依赖、无广告、轻量无感。**

古人书箴言于笺、贴于窗，抬目自省。本软件以「窗」喻屏幕，以「笺」作壁纸，每日择良言铺于桌面，以字句勉励自身、奔赴来日。

<!-- TODO: 在此放一张壁纸效果截图，桌面工具的截图非常重要 -->

---

## 安装使用

1. 前往 [Releases](../../releases) 下载最新安装包。
2. 运行安装，程序安装到 `%LocalAppData%\HopeCasement\`，**无需管理员权限**。
3. 打开后在配置窗口维护句子库、背景图，并设置换壁纸计划。

配置、句子库、背景图都以普通文件存放在安装目录，可直接编辑：

| 文件 / 目录 | 用途 |
|---|---|
| `config.json` | 所有设置 |
| `quotes.txt` | 句子库，一行一句 |
| `backgrounds\` | 用户自定义背景图 |
| `current_wallpaper.png` | 当前壁纸（程序自动覆盖） |

---

## 功能特性

- 句子库 + 背景图库随机组合，每日新壁纸
- 文字样式可调（字号、行距、文本宽度、衬底）
- 多种换壁纸计划（开机、每日、按间隔等），由 Windows 任务计划程序驱动
- 全程离线，不联网、不收集任何数据

---

## 从源码运行 / 开发

需要 Python 3.12+ 和 [uv](https://github.com/astral-sh/uv)。

```shell
uv sync                              # 安装依赖
uv run python -m hopecasement        # 运行 UI
```

测试换壁纸核心流程（不启动 UI）：

```shell
uv run python -c "from hopecasement.changer import change_wallpaper; change_wallpaper()"
```

入口逻辑：`HopeCasement.exe` 打开配置窗口；`HopeCasement.exe --change` 直接换壁纸（供任务计划程序调用）。

---

## 打包

打包 exe（[PyInstaller](https://pyinstaller.org/) 配置已写好）：

```shell
uv run pyinstaller HopeCasement.spec --clean
```

产物在 `dist\HopeCasement.exe`。

制作安装包（需先打包 exe，使用 [Inno Setup](https://jrsoftware.org/isinfo.php)）：

```shell
ISCC.exe setup\Hopecasement.iss
```

产物在 `setup\HopeCasement.exe`。可选 [Inno Setup 简体中文汉化包](https://github.com/kira-96/Inno-Setup-Chinese-Simplified-Translation)。

---

## 许可证

[MIT](LICENSE) © 2026 lingyao14
