# 09 普通入口权限装配候选

唯一新产品文件 `permissions/runtime.py`；已合 root 稳定 `96ec0bf`，未修改 root 的
loop/runtime/CLI、Session 或公共状态。函数入口：

`await createPermissionRuntime(cwd, userRoot, compatibility, session, cliConfig, ask,
interactive=..., env=..., yolo=False, readOnlyRoots=()) -> PermissionRuntime`

公开 `getMode/getRules/setMode(normal|plan)`、`authorize(tool, finalRawJson)->bool`、
`approveExternalRead/Write`、`command`、`isMutatingCommand`、`sourceStates`。
`ask` 是 `async(str)->str`，经本批的 makeApprovalPrompt 处理一次/始终允许；不构建分类器。
工具 schema 校验、最终参数选择、plan API 裁剪及派发硬门仍由 root 执行器负责。

从冻结 index 直接抽取权限装配/模式命令/区外审批逻辑，D09 调整为：
user 兼容→native user→可信 project 兼容/native→可信 local 兼容/native→CLI→
managed 兼容/native；数组去重并集、默认模式后者覆盖。trust receipt 仅原生 user；
project 兼容 settings/local 的存在也进入信任门，不自动读旧 DAO。Windows 原生 managed
按显式 env 中 ProgramData 解析（缺失用来源路径默认），测试用合成 ProgramData。
sourceStates 区分未信任、缺失/不可读、坏 JSON、规则来源归属和默认模式覆盖。

always/add 仅写 native local settings；remove 只写实际规则所属的 native user/project/local，
兼容及 managed 始终只读。删除后重新合并原层级，另一来源同一 deny 不会凭空消失。
用户本次显式 add 的规则保留当前进程效力，即使启动时尚未信任项目；下次启动仍受信任门约束。
坏现有 JSON 沿 ADR-0013 抛错、保留原字节。`/mode auto` 的提示明确分类器后置。

区外许可只读 native `<cwd>/.ruocun/approvals.json`，兼容来源不提供审批收据。
additionalDirectories 可读写，root 显式传的技能资源根只读；once 在同一次工具调用上下文
中复用，下一次 authorize 重置。root 必须在该工具实际派发任务内调用 authorize，使
ContextVar 与 preflight/handler 使用同一调用上下文；不能先在父任务批量 authorize
再让所有并行工具继承最后一个调用的许可集。普通查询命令不要求暂停，mutating 命令由 root
先 pause→settled 再调用 command。

验证 `n1-runtime-red`→`n1-runtime-green`，3 个最小来源/D09 装配 fixture 通过：
层级与信任/只读源，最终 raw 参数与 native remember/区外 once，来源 plan/mode 命令。
这些是必要 Python 装配确认，不宣称冻结另有 index 测试文件。Ruff、mypy 1 源文件通过，
原始类型失败仍保留。未为本片重复 162/392 项、未调用真实模型或改变系统策略。
产品/来源/测试 hash 与 raw 见 `runtime/manifest.json`；固定 wheel、入口集成、独审和整票出口后续。
