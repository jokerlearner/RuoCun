# 17 普通同步代理续跑独立核验

固定候选 `1f64ecc`，独审树 `src` 与 `tests` 与候选一致。依据 17 的 REC-08/CMD-recovery、41 的普通/特殊现场边界，以及 ADR-0009/0010/0013/0015。使用白名单和合成 HOME，SQLite 为受控 Windows 运行库，模型响应来自夹具。

`b02-review-sync-recovery` 实际 2 passed in 7.88s，退出码 0、敏感扫描未命中。原同步子代理实际 Write 完成后强制退出，新 owner 核实父未决记录后才允许续跑。同一决定只创建一个新 run，原工具配对、原同步专有工具、剩余轮数及文件字节和修改时间均保持预期。旧 format 1 后台快照没有 `toolPolicy` 时，只在真实背景身份与 run/task/owner 字段匹配后识别后台裁剪，继续执行也只一次。

普通入口会在恢复授权事务之前准备执行。核对原角色版本、模型和端点、项目根与工作目录身份、内外权限、API 工具名和 schema 摘要、剩余轮数及原系统提示。新 run 的 SQLite 决定先于派发，重复同 ID 只读已有决定。完整 CLI 强杀 → resolve → continue → 重复回执沿用主协调证据。

增量审查确认一条普通现场差异。非 headless 子代理可经 EnterPlanMode 改为实际 plan，已有检查点保存了有效 plan 与已激活工具。初始候选续跑按初次请求模式重建，完整现场也会安全拒绝。既有动态激活的工具同样需恢复精确 schema。

修复 `88806d3` 已独立复跑同一真实 SQLite 同步用例。`b02-review-sync-plan-recovery` 为 1 passed in 5.09s，退出码 0、敏感扫描未命中。场景实际执行原 Write、ToolSearch 激活、EnterPlanMode 和原拥有者强制退出。续跑恢复私有子会话的原有效 plan，按原目录中的确切名字恢复延迟工具，仍验证目录顺序、完整 schema 摘要、权限和工作目录等。原子代理的退出模式端口仍在，恢复后的实际读取通过，模型要求的 Write 被只读门禁拒绝，目标文件未创建。原 Write 和新 run 均只执行一次。17 该续跑接缝通过独立审查。
