**简体中文** | [English](CONTRIBUTING.en.md)

# 贡献指南

感谢你对「来日窗笺 HopeCasement」的关注！本指南会帮助你了解如何参与项目开发。

## 开始开发

在 Windows 上使用 Python 3.12 和 uv。从仓库根目录执行：

```powershell
uv sync --locked
uv run hopecasement
```

本地开发、回归测试与打包步骤可从[文档索引](docs/index.md#维护软件)进入。修改用户可见行为时，请在同一个 PR 中更新对应功能手册和测试，并说明哪些结果经过实机验证。

## 分支与提交规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 风格：`<类型>: <简述>`。常用类型：

| 类型         | 含义          |
| ---------- | ----------- |
| `feat`     | 新功能         |
| `fix`      | 修复 Bug      |
| `docs`     | 文档          |
| `style`    | 不影响逻辑的格式调整  |
| `refactor` | 重构（非新增、非修复） |
| `perf`     | 性能优化        |
| `chore`    | 构建、依赖、杂项    |

例如，`feat: 支持选择字体` 或 `fix: 保存后退出时更新每日计划`。

## Pull Request 流程

1. 先在 [Issues](https://github.com/jc371115833-cmd/hope-casement/issues) / [Pull Requests](https://github.com/jc371115833-cmd/hope-casement/pulls) 搜一下，避免重复劳动。
2. Fork 仓库，从 `main` 切出分支。
3. 完成修改，确保本地运行正常、符合代码规范。
4. 提交 PR，标题遵循上面的提交规范，正文简述改动目的与影响。
5. 等待维护者 Review；较大的改动建议先开 Issue 讨论方向。

## 问题反馈

报告问题或提出功能建议时，说明使用场景及预期行为。[Issues](https://github.com/jc371115833-cmd/hope-casement/issues)

一般讨论可前往 [Discussions](https://github.com/jc371115833-cmd/hope-casement/discussions)。

