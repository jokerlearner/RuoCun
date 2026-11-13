# 83 · 本地技术交付文档

完成中文入口、安装与恢复手册、更新日志和固定候选发布记录。核对 31 个本地链接、两份实际产物的摘要、三份锁和 44 个运行 wheel 的许可材料。此前校验发现可选观测锁在工作树被 Git 转为 CRLF，已按 Git 的 LF 摘要与本机 CRLF 摘要分别注明。原始 E-02 缺口保留。[发布记录](../../../../../docs/release/batch-09.md) · [安装手册](../../../../../docs/install-and-recovery.md) · [核对回执](raw/b09-n83-release-final/stdout.bin)

本地运行依赖清单读取实际锁定 wheel，核对版本、SHA-256、METADATA 许可声明与 wheel 内许可成员摘要。44 个 wheel 均有随分发的许可文件。[运行依赖许可清单](../../../../../docs/release/runtime-licenses-win311.json) · [原始清点回执](raw/b09-license-inventory/stdout.bin)

依照同批 79/81 的实证记录仓外运行、换包、恢复和已知应用控制约束。托管工作流与 macOS 实跑均保持待验。此批的实际候选可通过独立重建流程检查。
