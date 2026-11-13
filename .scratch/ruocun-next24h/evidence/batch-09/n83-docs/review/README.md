# 83 发布资料独立复核

文档候选 `c9cd0dd1` 复核通过。独立复跑核对 4 个发布相关页面的 31 个本地链接、真实 R3 wheel 与 sdist 的摘要、三份固定锁。观测锁的 Git LF 摘要和工作树 CRLF 摘要分别登记。读取实际离线 wheel，按 44 个锁定哈希再生成运行依赖许可清单，全部含许可成员，重生文件与登记文件 SHA-256 同为 `e84274b108c4b854cbc695302761a9b8c1ea69e186ebcd77e5eb47e3af952711`。 [文档与包回执](b09-review-n83-release/stdout.bin) · [许可清点回执](b09-review-n83-license/stdout.bin)

安装、升级、版本和恢复说明与 79、81 实测一致，Windows 的 4551 应用控制限制与模块入口也已注明。平台证据维持 Windows 本地实跑、Ubuntu WSL 源码检查、macOS 与托管 CI 待验。DAO MIT 版权与来源、随包 SQLite、终端嵌入帧及 E-02 缺少外部原图与独立授权的记录可定位。审查建议在收口显式注明无成套真实模型成绩和量化性能保证，并补明 Windows 桌面通知的交付边界。 [发布记录](../../../../../../docs/release/batch-09.md) · [安装和恢复](../../../../../../docs/install-and-recovery.md)
