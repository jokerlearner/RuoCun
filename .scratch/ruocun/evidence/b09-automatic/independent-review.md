# 批次09自动出口换绑独立复核

原产品 `8ee4a9b992ee7a77759b3295708dda32bebbe68f`，新产品 `0252fe7f3d51a89e166a716bc1991929cb8d9a09`，证据基线 `a0e32b1523d60b2e6a48473bb8483cf380121be0`。

- 比对实际两版 wheel、固定 Git 归档、新 sdist 和安装目录。新包 309 个产品成员严格同字节，原包至新包 308 个成员保持同字节，变化为中文帮助资源与其 wheel RECORD 摘要。三份锁及测试、工具和构建输入仍与原候选一致。 [变更与摘要](carryover.json) · [包绑定](../../../ruocun-next24h/evidence/batch-09/package/artifacts.json)
- 同一新包的仓外 `python -I -m ruocun --help` 实际退出 0，输出确认 Deck 回环接口、Linux bubblewrap、macOS Seatbelt、Windows 显式启用时拒绝。 [实际帮助回执](../../../ruocun-next24h/evidence/batch-09/package/raw/b09-final-clean-launch/stdout.bin)
- 权威矩阵的 19 个子案例逐项匹配原候选子案例、摘要和独立复核名单，原生执行仍绑定批次08原候选。按 [ADR-0015](../../../../docs/adr/0015-batch-validation-and-packaging.md) 复用这些实际结果，换绑通过。人工体验、真实终端整体操作及用户条件仍待最终验收。 [原复核](../b08-automatic/independent-review.md) · [77 复核](77-wtaccept-review.json) · [78 复核](78-wincaps-review.json)
