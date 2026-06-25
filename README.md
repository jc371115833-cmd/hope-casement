# 来日窗笺 HopeCasement

> 一纸笺文赴来日，日日新墨落屏窗。
> Words on screen, growth every coming day.

每日从句子库随机取一句良言，与背景组合渲染成壁纸，自动设为 Windows 桌面壁纸。
**单机离线、零网络依赖、无广告、轻量无感。**

古人书箴言于笺、贴于窗，抬目自省。本软件以「窗」喻屏幕，以「笺」作壁纸，每日择良言铺于桌面，以字句勉励自身、奔赴来日。

<p align="center">
  <img src="docs/screenshot.png" alt="壁纸效果" width="640">
</p>

<!-- 截图存放到 docs/screenshot.png 即可显示。建议放一张实际生成的壁纸效果图，最好再附一张配置窗口截图。 -->

> 仅支持 Windows 10 / 11（依赖 Windows 任务计划程序与桌面壁纸 API）。

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
| `history\` | 历史壁纸归档（开启「保存历史」后） |

卸载会清理上述运行期文件，不留痕迹。

---

## 功能特性

- **随机组合**：句子库 + 背景（纯色或图片）随机搭配，每次换出不同壁纸。
- **文字样式可调**：字号、颜色、阴影、行距、对齐方式、文本宽度、位置，以及文字衬底的颜色与透明度。
- **多种换壁纸计划**：开机时、按间隔、每日定时，可任意组合；底层由 Windows 任务计划程序驱动，关闭程序后仍生效。
- **中英文界面**：随安装语言或系统语言自动切换，也可手动指定。
- **保存历史**：可选将每次生成的壁纸归档留存（自动保留最近 200 张）。
- **全程离线**：不联网、不上报、不收集任何数据。

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

> 开发模式下，用户数据（config、quotes、backgrounds 等）位于项目根目录的 `userdata\`；
> 打包成 exe 后，则位于 exe 同目录。

### 技术栈

Python · [customtkinter](https://github.com/TomSchimansky/CustomTkinter)（配置界面）· [Pillow](https://python-pillow.org/)（文字渲染）· Windows `schtasks.exe`（定时调度）· ctypes（设置壁纸）。

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

## 贡献

欢迎通过 Issue 反馈问题或提出建议，也欢迎提交 Pull Request。

---

## 许可证

[MIT](LICENSE) © 2026 KingKing
