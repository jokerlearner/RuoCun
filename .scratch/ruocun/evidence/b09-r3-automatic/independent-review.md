# 批次09最终包自动出口独立复核

固定产品 `8e7760cea9ad7fa7b500fccd32984f5c9813f930`，证据基线 `f7b5413d`。独立比对实际 b09-r1 与 b09-r3 wheel。309 个产品成员中仅账户配置存储和普通入口两项改变，三份锁与原 Git 字节相同。b09-r3 的全部成员与固定 Git 归档、sdist、wheel、纯安装及 QA 安装一致。 [包与差异](carryover.json) · [新包绑定](../../../ruocun-next24h/evidence/batch-09/package-r3/artifacts.json)

- 14 份受控回执的 stdout 字节与原始回执相同，命令均正常结束且秘密扫描无命中。相同 wheel 的 QA 安装实际 **110 passed，43.70 秒**，覆盖配置、账户、向导、终端、启动和相关平台。 [安装加载](../../../ruocun-next24h/evidence/batch-09/package-r3/raw/b09-r3-qa-import/stdout.bin) · [定向测试](../../../ruocun-next24h/evidence/batch-09/package-r3/raw/b09-r3-qa-affected/stdout.bin)
- 纯安装实际拒绝未来账户版本、损坏的账户映射与激活项。三个普通入口均退出 71，写入同样拒绝，原配置字节一致。实际 Credential Manager 两个大小写区分的合成目标均读取匹配，删除确认均为 1168。独占控制台输入模式 503 → 1008 → 503，输出模式为 3，无补救，退出 0。 [配置](../../../ruocun-next24h/evidence/batch-09/package-r3/raw/b09-r3-profile/stdout.bin) · [凭据](../../../ruocun-next24h/evidence/batch-09/package-r3/raw/b09-r3-credential/stdout.bin) · [控制台](../../../ruocun-next24h/evidence/batch-09/package-r3/raw/b09-r3-console/stdout.bin)
- 逐行核对 19 个母族子案例、当前受影响验证指针及 b09-r1、b08 两级原始案例摘要和独立复核。按 [ADR-0015](../../../../docs/adr/0015-batch-validation-and-packaging.md) 复用未受影响结果，两票自动技术出口通过。完整 Windows Terminal 操作、登录与重启等仍待人工验收。 [77](77-wtaccept-review.json) · [78](78-wincaps-review.json)
