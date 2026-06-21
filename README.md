# 来日窗笺 HopeCasement

> 一纸笺文赴来日，日日新墨落屏窗。
> Words on screen, growth every coming day.

每日从句子库随机取句、与背景组合渲染成壁纸，自动设为 Windows 桌面壁纸。单机离线，无广告，轻量无感。

---

## 开发环境

需要 Python 3.12+ 和 [uv](https://github.com/astral-sh/uv)。

```shell
uv sync
```

运行 UI：

```shell
uv run python -m hopecasement
```

测试换壁纸核心流程（不启动 UI）：

```shell
uv run python -c "from hopecasement.changer import change_wallpaper; change_wallpaper()"
```

---

## 打包 exe

使用 [PyInstaller](https://pyinstaller.org/)，配置文件已写好，直接运行：

```shell
uv run pyinstaller HopeCasement.spec --clean
```

产物在 `dist\HopeCasement.exe`。

---

## 打包安装包

需要先完成上一步打包 exe，再用 [Inno Setup 7](https://jrsoftware.org/isinfo.php) 编译：

```shell
"E:\software\Inno Setup 7\ISCC.exe" setup\Hopecasement.iss
```

> 若 Inno Setup 安装路径不同，替换上面的 ISCC.exe 路径即可。

产物在 `setup\HopeCasement.exe`。

安装后程序位于 `%LocalAppData%\HopeCasement\`，无需管理员权限。

配置文件、句子库、背景图均存放在安装目录，方便直接编辑：

| 文件 / 目录 | 用途 |
|---|---|
| `config.json` | 所有设置 |
| `quotes.txt` | 句子库，一行一句 |
| `backgrounds\` | 用户自定义背景图 |
| `current_wallpaper.png` | 当前壁纸（程序自动覆盖） |

---

## Inno Setup 汉化

- 汉化包：[GitHub](https://github.com/kira-96/Inno-Setup-Chinese-Simplified-Translation)
