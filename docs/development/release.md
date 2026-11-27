# 发布 Windows 安装包

## 从发布 PR 到草稿 Release

1. 在发布分支更新 [pyproject.toml](../../pyproject.toml) 的 `project.version`，运行 `uv lock` 并提交锁文件。在 `docs/releases/v<版本>.md` 写入用户能观察到的变化、升级方法和待验项，从[文档索引](../index.md)加上入口。正文会进入 GitHub Release，其中的手册链接应指向本次标签。[v0.1.1 说明示例](../releases/v0.1.1.md)
2. 向 `main` 提交 PR。打开该 PR 的 Checks，等待最新提交的 Windows CI 全部通过，然后合并。修复导致检查失败的问题后，把改动推到同一 PR，等待新的检查结果。
3. 在 PR 页面记下合并提交的 SHA，然后打开 [GitHub Actions](https://github.com/jc371115833-cmd/hope-casement/actions)。当 `main` 上该提交的 **Windows checks** 通过且版本递增时，工作流会为该提交创建标签，例如 `v0.1.1`，并以同一标签启动发布。已有同名标签必须指向同一提交。
4. 在 Actions 核对发布运行的标签和提交 SHA。工作流从标签构建安装包，通过 Windows 验收后生成 SHA-256 和发布说明，将附件上传到草稿 Release。
5. 在草稿中核对标签、提交、安装包和校验值。下载附件后，在 PowerShell 执行下列命令，将输出的 Hash 与该文件名对应的 SHA-256 核对。公开发布前在草稿中补上实机验收结果。[GitHub Releases](https://github.com/jc371115833-cmd/hope-casement/releases)

   ```powershell
   Get-FileHash .\HopeCasement-Setup-v0.1.1.exe -Algorithm SHA256
   ```

### 触发与恢复

自动流程用 `GITHUB_TOKEN` 建标签，再显式调用 `workflow_dispatch` 启动该标签的发布。这样即使 GitHub 屏蔽由该令牌产生的递归 `push` 事件，构建仍会运行。维护者手工推送指向已通过 Windows 检查的版本标签，也可触发同一发布流程。[GitHub 的令牌触发规则](https://docs.github.com/en/actions/concepts/security/github_token)

临时故障可在对应的 Actions 运行中选择 **Re-run failed jobs**。标签已建立或同一版本已创建草稿时，也从失败作业重试。若标签所指的源码需要修改，另开 PR 并递增版本，用新标签发布修复。

## 在 Windows 上构建

在仓库根目录用 PowerShell 7 运行以下命令。[PyInstaller 配置](../../HopeCasement.spec)将应用入口、主题、图标和 CustomTkinter 资源打成 `dist/HopeCasement.exe`。[构建脚本](../../.github/scripts/build-installer.ps1)下载并校验固定版本的 Inno Setup 和简体中文语言文件，然后生成安装包 `setup/HopeCasement.exe`。应用窗口与安装器共用 `project.version`，覆盖升级沿用[安装脚本](../../setup/Hopecasement.iss)中的 `AppId`。

```powershell
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked pyinstaller --noconfirm HopeCasement.spec
./.github/scripts/build-installer.ps1
```

## 安装版验收

### CI 自动检查

在独立 Windows runner 上，[Windows CI](../../.github/workflows/ci.yml)执行打包版 `--change`，检查生成的 PNG、失败退出码和错误日志。[安装器验收脚本](../../.github/scripts/test-installer.ps1)先验证新版能全新安装和卸载，再用已发布的 v0.1.0 安装包建立旧版环境，执行覆盖升级，核对版本、个人数据、登录项和计划任务。卸载后还要核对注册项和安装数据已清理，外部图片和备份仍可读取。实际结果见该次 Actions 日志。后续发布若要验证从较新版本升级，在发布 PR 中更新旧版安装包基线和校验值。

### 实机检查

使用草稿中的安装包，在独立 Windows 测试账户或虚拟机中完成以下交互检查。把安装包 SHA-256、Windows 版本、实测结果和待验项写入草稿。

1. 用中、英文安装界面核对程序名称和菜单。打开配置窗口，按[首张壁纸教程](../user-guide/getting-started/first-wallpaper.md)生成指定的句子和背景，确认真实桌面显示正确。
2. 只启用每日计划并设置接下来几分钟的时间，保存并关闭窗口。到点核对任务的上次运行时间、图片文件和桌面。改成另一时间，通过关闭窗口时确认保存，再核对新时间。用同样方式检查间隔触发。[验证自动计划](../user-guide/scheduling/automatic-changes.md)
3. 只启用「开机时换」，保存，注销并重新登录测试账户，核对壁纸和生成时间。验完后取消测试计划并保存。
4. 如需验证从备份恢复，在安装目录外备份测试数据，卸载后重装，恢复配置、句库和图片，再用恢复的素材生成壁纸。[备份与恢复](../user-guide/data/backup-and-restore.md)
