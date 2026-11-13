# 81 手动升级独立复核

独立复核 `017dc16a` 的仓外升级证据和最终产品 `8e7760cea9ad7fa7b500fccd32984f5c9813f930`。使用同一 b08-r1 和 b09-r3 固定 wheel，重新复制仓外探针，在独立合成目录实际运行。两份包的版本均为 `0.1.0.dev0`，wheel 摘要及安装后的帮助差异确认完成实际替换。 [独立命令](b09-review-n81-upgrade/command.json) · [实际回执](b09-review-n81-upgrade/stdout.bin)

停止后的完整合成数据含四个文件，备份逐文件匹配，停后无 WAL/shm sidecar。替换包后原会话 ID 继续并提交新消息。未来版本及损坏数据库各自拒绝，四个坏账户配置经普通入口同样拒绝，原始字节与请求次数保持。卸载包后用户数据、备份和合成 DAO 材料均保留。两次模型请求发往本机合成服务，临时工作区已清除。

源码独审复现版本2账户映射为数组时原 `saveProfiles` 覆盖受保护内容。修复后同一真实私有文件写入拒绝、旧字节一致。有效版本 `2.0`、已知旧格式迁移、正常版本2写入重开和底层坏 JSON 的原只读行为通过定向核验。 [覆盖原件红证](b09-review-n81-damaged-red/stdout.bin) · [原字节保留绿证](b09-review-n81-damaged-green/stdout.bin) · [兼容回执](b09-review-n81-profile-compat/stdout.bin)

第 81 票技术复核通过。中文空格环境使用标准包的模块入口。该路径的生成式 console launcher 受本机应用控制的历史回执仍保留，应用控制策略未改动。 [环境边界](../README.md)
