# 来日窗笺开发约定

从 [README](README.md) 了解产品。从[功能与源码对照表](docs/architecture/overview.md#按改动定位)找到本次任务的实现、手册和测试。其他主题从[文档索引](docs/index.md)进入。

## 开始改动

- 在仓库根目录运行 `git status --short --branch`，保留已有的工作区修改。使用锁定的 Python 环境。首次运行见[本地开发](docs/development/local-setup.md)。
- 保留两个产品入口：打开程序显示配置窗口，`--change` 按磁盘配置执行一次换图。两条路径共用 `changer.change_wallpaper()`。样式和计划控件目前都在 `ui/tab_schedule.py`。
- 修改配置、模块位置或打包脚本前，核对[数据兼容约定](docs/architecture/configuration-and-data.md)。`userdata/` 是开发者本机内容；测试使用临时目录。构建的主题、图标和设置文件的位置由 [PyInstaller 配置](HopeCasement.spec) 和[安装脚本](setup/Hopecasement.iss)决定。

## 验证与交付

- 从[测试指南](docs/development/testing.md)选对应的测试。完整回归命令为 `uv run --locked python -m unittest discover -s tests -v`。测试用替身隔离设置桌面、注册表和任务计划程序的写操作。
- 涉及安装、升级、真实桌面或系统触发时，按[发布验收](docs/development/release.md)在专用 Windows 测试环境记录结果。报告中区分实际运行的检查和待验证项。
- 用户可见行为变更时，在同一次改动里更新功能手册和回归用例。新增或移动文档时更新 `docs/index.md` 及原链接；架构边界变动时更新功能与源码对照表。
