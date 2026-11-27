# 验证一次改动

在 Windows 仓库根目录运行。测试使用标准库 `unittest`，将个人数据读写放在临时目录，并用测试替身隔离桌面设置、注册表和任务计划程序的写操作。

```powershell
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
```

## 只运行相关的回归

从[功能与源码对照表](../architecture/overview.md#按改动定位)找到测试文件，将文件名作为 `-p` 参数。例如，改了关闭窗口时的保存行为，可以运行下面的命令。

```powershell
uv run --locked python -m unittest discover -s tests -p test_save.py -v
```

文档改动可选 `-p test_documentation.py` 检查仓库内的相对链接、图片、标题锚点，以及各篇手册能否从索引到达。命令示例、按钮名称和排障步骤需要对照实现核实。

## 查看合成效果

以下命令只向临时目录写入 `hope-preview.png`，并打印路径。在默认图片查看器中打开它，可以检查文字外观和位置。

```powershell
uv run --locked python -c "from pathlib import Path; from tempfile import gettempdir; from hopecasement.config import Config; from hopecasement.renderer import compose_wallpaper; p=Path(gettempdir())/'hope-preview.png'; compose_wallpaper('#2D3033','今天看见了新的风景。',Config(),(800,450)).save(p); print(p)"
```

## 什么时候需要实机

[Windows CI](../../.github/workflows/ci.yml) 运行完整回归，在临时 Windows 环境中检查打包版 `--change` 的成功与失败路径，并用安装包验证首次安装、从旧版覆盖升级和卸载。桌面是否可见更新、用户登录或计划到点后是否实际换图，需要在专用 Windows 账户或虚拟机中观察。[安装版验收](release.md#安装版验收)
