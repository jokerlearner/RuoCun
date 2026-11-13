# 12 前台批执行独审

审查候选 `1daa1f0fda884f9d91502753df00f4640d37b42c`。独立运行固定合入源 `77dc33b7277c25793273e79e4c475bc5f9a0111b`，批执行器、loop 和两个对应测试文件与原候选逐字节一致。缺陷回修固定 `d1841034370a42c860105b5068f6cd97fd2669d6`。

- 冻结 `tools/execute.ts` 的安全批八路上限、在途收齐、write/exec 独占和返回原序已核。RuoCun 在实际执行 Task 中进入每调用的审批 Scope。assistant tool_calls 先持久化，再逐调用确认 intent 和 result。DurableStore 保持身份校验、同操作结果不可覆盖及结果回执事务。批结果按调用顺序入历史，图片各用独立槽并在已配对检查点后集中投影。plan 变更即时影响后续写屏障。
- 固定合入源的八路并发与原序、allSettled、真实多图、Bash 后续屏障和实时 plan 五项独立通过，`5 passed in 0.33s`。回执 `raw/review-12-executor-subset01`。
- S-05 直接核对冻结 `execute.ts:37` 与 `exec_shell.ts:406` 及原 Node 回执。冻结判定可认旧用例 `[exit 1]`，实际 formatter 的 `[exit 1,运行 0s]` 和 `[已中断,运行 0s]` 会漏判。RuoCun 判失败并停止后续写/exec，`[exit 0,运行 0s]` 仍正常。见 [源回执](../n2-batch/raw/n2-batch-s05-oracle01/stdout.bin)。

## 已关闭的 P2

旧 `authorize` 回调兼容路径允许两个 Read 并发。第一个审批异常在结果数组排前时，原候选会吞掉第二个已执行 Read 的结果回执 `StoreError`，将它保存为“此调用未执行”，并报告“现场已保存”。固定源的独立 run_turn 探针实际看到该派发、intent 和错误检查点，预期失败回执 `raw/review-12-receipt-precedence-red01`。

回修仍等所有已开始的调用收尾，先传播真实工具或存储异常，仅有审批异常时才按原路径补齐未执行消息。固定回修的同一探针确认 `StoreError` 传播且检查点停在原 assistant，`raw/review-12-receipt-precedence-green01`。复用原 allSettled 用例确认第三个在途工具可写完可信结果，后续写屏障未启动，`1 passed in 0.44s`，`raw/review-12-receipt-affected01`。

定向运行使用私有 Python 3.11 环境、合成 HOME/config/temp 和注入模型回复。四组回执均未命中秘密扫描，真实或付费模型调用 0。REC-05 原五切点采用作者回归证据。本片剩余审查阻断 0。

## 普通入口

固定 `aed4a003fff1b2a166ce165c825ab674a76ffd05` 的实际普通入口传入 `authorizeBatch` 和 `callScope`。Gate 只把待询项发进一次批请求。每实际派发 Task 在 scope 内等待 intent、派发和结果回执，再恢复其 ContextVar。

独立复用原混合 CLI 用例 `test_seven_tools_approval_and_normal_reopen`，`1 passed in 11.76s`。实际合成 HTTP 请求 `parallel_tool_calls=True`，十二条工具结果保持模型提交顺序。普通启动、审批/拒绝、真实文件副作用和重开断言保留。回执 `raw/review-12-entry-cli01`，秘密扫描未命中，模型调用仅合成 loopback。

静态核对原受控 TTY 用例仍校验模型 Skill 正文加载、真实用量与 trace。加载从待关闭审批的回合移到可执行的 plan 回合，计划写拒绝、关闭后未写、配对和可信 usage 原断言保留。该 TTY 回归由 root 执行。本次剩余入口审查阻断 0，固定安装及整票验收待集成。
