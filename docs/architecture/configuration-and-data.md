# 配置与数据兼容

[config.py](../../src/hopecasement/config.py) 定义 `Config` 默认值、配置迁移和数据目录。界面收集控件值后写入配置；计划启动的新进程从磁盘重新加载。要了解用户如何备份和恢复文件，见[数据手册](../user-guide/data/backup-and-restore.md)。

## 两种数据目录

源码检出模式从 `config.py` 的位置向上定位仓库根目录，在 `userdata/` 下读写。PyInstaller 打包后使用 `sys.executable` 的父目录，使计划启动时也能找到窗口先前保存的设置。移动模块、入口或 exe 时应验证两种路径。图片目录可自定义，空字符串使用数据目录下的 `backgrounds/`。

## 旧配置如何读取

`load_config()` 以默认值补齐缺失字段，过滤未知键。文件缺失或 JSON 无法解析时使用默认值。现有迁移包括：

| 旧输入 | 加载后的行为 |
| --- | --- |
| `schedule_mode: "manual"` | 转成空的 `schedule_modes`，保留手动模式 |
| 单个旧计划（如 `"daily"`） | 转成只含该项的数组。已有新字段时以新字段为准 |
| `text_position` 命名位置 | 映射到百分比坐标；已有 `text_x` 时保留现行坐标 |
| 旧的大字号值、`text_padding` | 大于 15 的旧字号按迁移公式换算，弃用的边距字段被忽略 |

迁移在内存中完成，下次保存时以现行字段写出。添加字段时同步检查默认值、缺省加载、界面收集/回填和旧配置回归。句子由 [quotes.py](../../src/hopecasement/quotes.py) 读写为 UTF-8 文本，独立于配置 JSON。

## 修改后的验证

用[迁移测试](../../tests/test_config_migration.py)从临时目录加载旧字段并检查结果。移动数据位置或调整安装器时，按[发布手册](../development/release.md)验证旧句库、配置和图片在覆盖安装后仍可被读取。
