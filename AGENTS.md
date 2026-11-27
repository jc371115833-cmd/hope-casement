# 来日窗笺开发约定

在仓库根目录先运行 `git status --short --branch`，保留已有的工作区修改。第一次接手时，从 [README](README.md) 了解产品，再用[功能与源码对照表](docs/architecture/overview.md#按改动定位)找到本次改动的实现、手册和测试。

## 开始改动

- 按[本地开发](docs/development/local-setup.md)使用锁定的 uv 环境。保留无参数的配置窗口和按磁盘配置换图一次的 `--change`，两条路径共用换图流程。
- 移动模块、改动配置或安装脚本前，核对[数据兼容约定](docs/architecture/configuration-and-data.md)。`userdata/` 属于本机用户，测试素材写入临时目录。

## 验证与交付

- 按[测试指南](docs/development/testing.md)运行相关回归。用测试替身隔离桌面、注册表和任务计划程序的写操作。
- 涉及安装、升级、真实桌面或系统触发时，按[发布验收](docs/development/release.md)在专用 Windows 测试环境记录结果。报告中区分实际运行的检查和待验证项。
- 用户可见行为变更时，在同一次改动里更新功能手册和回归用例。新增或移动文档时更新[文档索引](docs/index.md)及原链接，架构边界变动时更新功能与源码对照表。
