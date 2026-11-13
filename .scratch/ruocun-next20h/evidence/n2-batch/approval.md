# 12 批审批接缝

冻结 DAO `src/tools/execute.ts:161–212` 逐调用裁决，以一次 `requestBatch` 提交全部待询问项。`src/tools/execute.test.ts:59–93` 覆盖自动放行、询问、拒绝、批次调用标识及硬拒绝。`PermissionRuntime.authorizeBatch` 沿用现有 gate 和规则，按同一最终参数串裁决并提交请求。`callScope` 只为实际派发设置 ContextVar，结束后恢复外层作用域。

`tests/test_n2_tool_batch.py::test_source_requests_one_batch_for_asks_keeps_order_and_excludes_hard_deny` 从真实 PermissionGate 捕获批次，校验硬拒绝、批准和拒绝以及最终原始 JSON。复用 09 的区外许可场景验证父任务已有一次性许可时，兄弟任务仍需询问。

- `n2-batch-approval-red01` 缺批次模块，1 failed。
- `n2-batch-approval-green01` 批审批与原三个 Runtime 用例，4 passed。
- `n2-batch-approval-ruff01` 和 `n2-batch-approval-mypy01` 通过，mypy 2 个源文件。

白名单环境、私有 Python 3.11 venv、显式源码导入，无真实模型调用。原始记录见 `raw/`。普通入口与 12 整票另行验收。
