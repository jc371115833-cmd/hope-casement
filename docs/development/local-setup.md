# 在 Windows 上从源码运行

使用 Windows 10 或 11、Python 3.12 和 [uv](https://github.com/astral-sh/uv)。在 PowerShell 中执行：

```powershell
git clone https://github.com/jc371115833-cmd/hope-casement.git
cd hope-casement
uv sync --locked
uv run hopecasement
```

已检出仓库时，从项目根目录执行最后两行。配置窗口初次打开时会创建本地用户数据，位置见[配置与数据](../architecture/configuration-and-data.md)。修改界面时按[首次使用教程](../user-guide/getting-started/first-wallpaper.md)核对按钮和效果。

**立即换壁纸**会更换当前登录用户的真实桌面。只想检查生成的图像时，运行[渲染测试](testing.md)。源码版可以写入设置；Windows 定时计划使用打包 exe 的绝对路径，完整调度验证见[安装版验收](release.md)。

命令行脚本指向 [`hopecasement:main`](../../pyproject.toml)。调试某项功能前，先从[源码对照表](../architecture/overview.md#按改动定位)找到正常的产品入口。
