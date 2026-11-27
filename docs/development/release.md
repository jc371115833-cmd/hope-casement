# 构建与验证 Windows 安装包

在 Windows 仓库根目录执行，使用锁定的 Python 环境及 Inno Setup 6。若编译器缺少中文语言文件，将与编译器版本对应的 `ChineseSimplified.isl` 放入它的 `Languages` 目录。[Inno Setup 6.7.3 简体中文文件](https://github.com/jrsoftware/issrc/blob/is-6_7_3/Files/Languages/Unofficial/ChineseSimplified.isl)

发布新版本时，在 [pyproject.toml](../../pyproject.toml) 更新 `project.version`，同步 `uv.lock`。窗口和安装器从项目元数据取得版本。覆盖安装沿用[安装脚本](../../setup/Hopecasement.iss)中的 `AppId`，使 Windows 能识别原有安装。

```powershell
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked pyinstaller --noconfirm HopeCasement.spec
ISCC.exe setup\Hopecasement.iss
```

`ISCC.exe` 未加入 PATH 时，用 PowerShell 的 `&` 调用编译器完整路径。每一步成功后再运行下一步。两个同名 exe 的用途如下：

| 路径 | 用途 |
| --- | --- |
| `dist/HopeCasement.exe` | PyInstaller 产生的应用程序；支持无参配置窗口和 `--change` |
| `setup/HopeCasement.exe` | Inno Setup 生成的安装包，供用户下载 |

PyInstaller 的入口、主题、图标和 CustomTkinter 资源列在[打包配置](../../HopeCasement.spec)。安装器从 `dist/` 取应用程序，安装目录、语言选择、登录项和卸载清理在[安装脚本](../../setup/Hopecasement.iss)中维护。

## 安装版验收

在独立 Windows 测试用户或虚拟机中完成以下步骤。验收记录写到对应改动或发布记录中，注明构建版本、Windows 版本、实际观察与未覆盖项目。

1. **首次安装。** 从安装包启动应用。核对窗口可见、语言、图标、三个标签页，再按[首张壁纸教程](../user-guide/getting-started/first-wallpaper.md)生成指定的句子和背景。
2. **手动与计划。** 设置几分钟后的每日时间，点击保存并关闭。到点核对任务的上次运行时间、生成文件和桌面。在窗口中修改为另一个时间，通过关闭时确认保存，核对系统里的新触发时间。分别验证间隔和下次登录，再全部取消并保存。
3. **覆盖升级。** 用上一个发布版创建测试句库、纯色和自定义背景目录，启用登录换图并保存。[备份个人数据](../user-guide/data/backup-and-restore.md)后覆盖安装，先检查已有登录项是否保留，再打开程序核对设置、句库和图片。保存后核对登录项和计划任务都指向本次安装的程序。
4. **卸载与恢复。** 在测试环境卸载，确认预期清理的数据文件、注册项及两个任务已移除，外部图片目录与备份仍可读。重装，按备份手册恢复并生成壁纸。

如果安装器或语言文件有变动，分别用中、英文安装界面核对菜单与程序名称。发布 Release 时上传安装包，说明用户可见变化、升级和备份注意事项。
