# 验证一次改动

在 Windows 仓库根目录运行。测试使用 Python 标准库 `unittest`。文件读写放在临时目录，调度注册和桌面设置使用测试替身；可以在日常开发账号上执行。

```powershell
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
```

## 只运行相关的回归

将下表的文件名放入 `-p` 参数。例如，只验证保存或退出的行为：

```powershell
uv run --locked python -m unittest discover -s tests -p test_save.py -v
```

| 改动 | 测试 | 核对内容 |
| --- | --- | --- |
| 配置或升级 | `test_config_migration.py` | 旧版手动模式、坐标、字号以及新旧字段同时出现的优先级 |
| 渲染 | `test_renderer.py` | 固定纯色的 RGB、背景居中裁剪、文字位置、输出 PNG 尺寸 |
| 保存和退出 | `test_save.py` | 两个入口都应用计划，取消或放弃、写盘失败、注册失败重试及源码模式退出 |
| Windows 调度 | `test_scheduler.py` | 每日和间隔任务的名称、触发器、exe 参数；登录项及取消计划 |
| 手动和计划换图 | `test_change_flow.py` | UI 读取当前样式、计划读取磁盘配置、桌面调用、归档和错误日志 |
| 文档导航 | `test_documentation.py` | 仓库 Markdown 的本地页面、代码链接、图片和标题锚点 |

要检查文字的实际外观，可在临时目录生成预览。此命令只在临时目录写入 `hope-preview.png`，打印图片路径：

```powershell
uv run --locked python -c "from pathlib import Path; from tempfile import gettempdir; from hopecasement.config import Config; from hopecasement.renderer import compose_wallpaper; p=Path(gettempdir())/'hope-preview.png'; compose_wallpaper('#2D3033','今天看见了新的风景。',Config(),(800,450)).save(p); print(p)"
```

## 什么时候需要实机

测试可以核对“计划如何注册”和“图像如何生成”。Windows 是否在当前用户登录或到点后执行、桌面是否可见更新，以及安装器覆盖升级的结果，需在专用测试账户或虚拟机按[安装版验收](release.md)观察。CI 使用同一条回归命令，并测试打包入口。
