**简体中文** | [English](CONTRIBUTING.en.md)

# 贡献指南

在 Windows 上按[本地开发](docs/development/local-setup.md)安装依赖并启动程序。从[功能与源码对照表](docs/architecture/overview.md#按改动定位)找到对应模块、用户手册和测试。

## 提交改动

1. 先查找已有的 [Issues](https://github.com/jc371115833-cmd/hope-casement/issues) 和 [Pull Requests](https://github.com/jc371115833-cmd/hope-casement/pulls)。较大的改动建议先开 Issue 讨论。在自己的 fork 中从 `main` 创建工作分支。
2. 按[测试指南](docs/development/testing.md)运行回归。用户可见行为有变化时，一并更新对应手册和用例。安装、升级和系统计划触发的检查方法见[发布验收](docs/development/release.md#安装版验收)。
3. 提交信息和 PR 标题采用 [Conventional Commits](https://www.conventionalcommits.org/)，例如 `fix: 保存后退出时更新每日计划`。常用类型还有 `feat`、`docs`、`style`、`refactor`、`perf` 和 `chore`。
4. 在 PR 正文说明改动目的和影响，列出实际运行的测试、实机观察以及仍待验证的部分。

## 反馈问题

报告问题时请附上应用和 Windows 版本、复现步骤、预期与实际结果。功能建议请描述使用场景。一般讨论可前往 [Discussions](https://github.com/jc371115833-cmd/hope-casement/discussions)。
