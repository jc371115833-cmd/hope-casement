# 在 Windows 上从源码运行

使用 Windows 10 或 11 和 [uv](https://github.com/astral-sh/uv)。Python 版本由仓库的 [.python-version](../../.python-version) 指定，依赖版本由 [uv.lock](../../uv.lock) 锁定。在 PowerShell 中检出仓库。

```powershell
git clone https://github.com/jc371115833-cmd/hope-casement.git
cd hope-casement
```

已有检出时直接从仓库根目录执行以下命令。

```powershell
uv sync --locked
uv run --locked hopecasement
```

成功后会打开配置窗口。若已有窗口，程序会尝试将它带到前台。源码版使用仓库中的 `userdata/`，请保留已有内容。修改界面时可按[首次使用教程](../user-guide/getting-started/first-wallpaper.md)核对按钮和效果。

**立即换壁纸** 和 `uv run --locked hopecasement --change` 都会更换当前用户的真实桌面。只想看合成效果时，可[生成临时预览图](testing.md#查看合成效果)。源码版可以保存设置，登记计划时会提示需要打包的 exe。用安装版验证真实触发的步骤见[安装版验收](release.md#安装版验收)。

命令行脚本指向 [`hopecasement:main`](../../pyproject.toml)。调试某项功能前，先从[源码对照表](../architecture/overview.md#按改动定位)找到正常的产品入口。
