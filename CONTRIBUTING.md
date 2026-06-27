# 贡献指南

感谢你对「来日窗笺 HopeCasement」的关注！本指南会帮助你了解如何参与项目开发。

## 开发环境

本项目暂时仅面向 **Windows 10 / 11**，需要 **Python 3.12+** 和 [uv](https://github.com/astral-sh/uv)。

```shell
git clone https://github.com/jc371115833-cmd/hope-casement.git
cd hope-casement
uv sync                              # 安装依赖
uv run python -m hopecasement        # 运行配置窗口
```

只测试换壁纸核心流程（不启动 UI）：

```shell
uv run python -c "from hopecasement.changer import change_wallpaper; change_wallpaper()"
```

入口逻辑：`HopeCasement.exe` 打开配置窗口；`HopeCasement.exe --change` 直接换壁纸（供 Windows 任务计划程序调用）。

> 定时调度（`scheduler.py`）依赖打包后的 exe 路径，**仅在打包版中生效**，开发模式下无法测试。

## 项目结构

**技术栈**：Python · [customtkinter](https://github.com/TomSchimansky/CustomTkinter)（界面）· [Pillow](https://python-pillow.org/)（文字渲染）· Windows `schtasks.exe`（定时调度）· ctypes（设置壁纸）。

**用户数据位置**：打包后存在 exe 同目录，开发模式下存在项目根目录的 `userdata\`。

| 文件 / 目录                 | 用途                |
| ----------------------- | ----------------- |
| `config.json`           | 所有设置              |
| `quotes.txt`            | 句子库，一行一句          |
| `backgrounds\`          | 用户自定义背景图          |
| `current_wallpaper.png` | 当前壁纸（程序自动覆盖）      |
| `history\`              | 历史壁纸归档（开启「保存历史」后） |

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

示例：`feat: 新功能 `/ `fix: 修复XX问题`

## Pull Request流程

1. 先在 [Issues](../../issues) / [Pull Requests](../../pulls) 搜一下，避免重复劳动。
2. Fork 仓库，从 `main` 切出分支。
3. 完成修改，确保本地运行正常、符合代码规范。
4. 提交 PR，标题遵循上面的提交规范，正文简述改动目的与影响。
5. 等待维护者 Review；较大的改动建议先开 Issue 讨论方向。

## 问题反馈
- 🐛 **Bug 反馈**： 提交[Issues](../../issues)&#x20;
- 💡 **功能建议**：提交[Issues](../../issues)&#x20;
- 💬 **一般讨论**：前往 [Discussions](../../discussions)

