# 手动能换，关闭窗口后没有按时换

先手动点一次「立即换壁纸」。如果也失败，先处理背景或渲染问题；手动正常再沿以下顺序检查。[手动换图排查](wallpaper-not-changing.md)

## 1. Windows 收到计划了吗？

从安装版打开「换壁纸设置」，核对勾选项和时间，点「保存设置」。看到「计划更新失败」表示配置已经写入磁盘，Windows 调度尚未全部更新。查看弹窗中的错误，修正后点「保存设置」重试。如果直接关闭窗口，选择「是」会重试并在成功后退出，选「否」则直接退出。下次仍可打开安装版重新保存。源码运行时也能保存配置，登记计划需要打包后的程序。

打开「任务计划程序 → 任务计划程序库 → HopeCasement」。每日任务为 `ChangeAtTime`，间隔任务为 `ChangeOnInterval`。核对「触发器」与「操作」中的 exe 路径及参数 `--change`。如果移动了安装目录，请从新位置打开程序、重新保存。只勾选「开机时换」时，到当前用户的启动应用查找 HopeCasement；它在登录时触发。

## 2. 到点后，系统触发了吗？

保存每日时间后，也可以在 PowerShell 中只读查询 Windows 登记的下次运行时间。核对 `NextRunTime` 的日期和时间是否符合预期。

```powershell
Get-ScheduledTaskInfo -TaskPath '\HopeCasement\' -TaskName 'ChangeAtTime' | Select-Object NextRunTime
```

为复查每日任务，临时选择几分钟后的时间并保存，让电脑保持唤醒、用户保持登录。到点后刷新任务计划程序，核对「上次运行时间」。若时间仍旧，核对任务是否启用、触发时间和当前账户。若已更新，继续检查生成文件。

## 3. 本次执行生成、应用壁纸了吗？

在任务计划程序中查看「上次运行结果」。换图程序运行失败时会返回 `1`，并尝试向数据目录中的 `error.log` 写入带时间的错误详情。再核对 `current_wallpaper.png` 的修改时间和画面。它在生成成功后写出，即使后续设置桌面失败也可能更新。若任务成功且桌面看似相同，可检查是否抽到了同样的素材。[找到数据目录](../user-guide/data/backup-and-restore.md)

仍需反馈时，请附应用版本、Windows 版本、选择的计划类型、预计与实际触发时间、界面错误提示，以及对应时段的日志摘录。可以把日志中的 Windows 用户名或私人图片路径隐去。[反馈问题](https://github.com/jc371115833-cmd/hope-casement/issues) · [设置与验证自动更换](../user-guide/scheduling/automatic-changes.md) · [文档索引](../index.md)
