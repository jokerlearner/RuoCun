# N1 排队正文与权限装配独审

## 已确认的排队正文

固定 `5088228c357360180de599006512c6253ec84e20`。queue_user 仅兼容追加可选 model_content，AcceptedInput.payload 的普通旧 str／list JSON 保持；仅有独立正文投影时使用带 kind 版本的 original／model envelope，拒绝未知 envelope／无效内容而保留记录。没有新 DB／Checkpoint 字段或新的日志／恢复框架。

接纳时原文与正文同时冻结、同一 checkpoint 确认后返回身份；两者任一会被当前凭据脱敏改写均在 ack 前拒绝。恢复直接消费确认的正文，不重读可已改变或消失的 Skill。hasQueued 与标题读取 original，不把 envelope 当用户文字。模型正文、consumed 与账本恢复为原文在同一事务确认后交换；已消费正文留在模型消息，账本不长期再重复一份。Hook rejected／pause discarded 保留未消费材料，不混入模型历史；override 正文也再次经过可完整保存检查。

独立只复原保存／重开账本 fixture **1 passed in 2.95s**，其中确认手动 Skill 原文／正文经重开后一次消费，checkpoint 消息使用正文而 consumed 账本只留原命令。原字符串、单调身份、重复文本、拒绝及暂停断言仍保留。回执 `raw/n1-review-input-projection-01`。不重复原 scheduler 七项／全量，不扩矩阵或构建；剩余模块阻断 0，可供 root 消费。

## PermissionRuntime 初审

固定初候选 `79c21039e198a5cf2a27c72e87a83b2d6f50466a`，独立新模块 permissions/runtime.py，未把 root 普通入口接线当作已经验证。

独立核对冻结 index 的装配／getMode／模式命令／区外审批、D09 单一兼容契约及本模块原三个装配 fixture：user 兼容→native user→可信 project 兼容/native→可信 local 兼容/native→CLI→managed 兼容/native；数组并集、默认模式后者覆盖，项目兼容 settings/local 同样受当前项目本产品信任控制。root 必须传经 loadCompatibility(userRoot,cwd) 验证 workspace 的 map，此组件不取代该唯一声明验证器。managed 原生路径按明确合成 ProgramData 测试，兼容及 managed 规则只读。

remember／add 只写原生 local，remove 仅写实际来源的 native user／project／local，重载时保留另一层同名规则。区外目录用 canonical realpath／commonpath，技能资源根只自动允许读，写仍需明确批准。once 存在该调用 ContextVar 的路径集中，不升格 session／always；下一 authorize 重置。组合根必须在实际工具 Task 内 authorize→dispatch，不得父 Task 预裁后让并发子调用继承最后许可；本模块通过不证明后续并发接线已正确。

查询和 mutating 命令有显式区分；是否 pause→真正 settled 仍由 root 负责。真实默认 B 已连接，未创建或注入模型分类器。schema 校验、最终参数同一性、plan API／派发硬门也仍属于组合入口。

原三个来源／D09 装配 fixture 独立 **3 passed in 0.16s**，mypy 对 runtime **1 源通过**，见 `raw/n1-review-permission-runtime-01`／`raw/n1-review-permission-runtime-mypy-01`。

初审发现一处待回修的来源差异：setMode(normal) 未像冻结 index.ts:1134–1137 清除临时权限模式 override；例如 /mode default→EnterPlanMode→ExitPlanMode，初候选仍保留 default，源退出 plan 清覆盖回 settings 默认。已交单文件作者最小修正并复原模式 fixture；不会因此擅改来源默认配置 plan 的其它行为。该发现修正／独立复验记录在后续收口段。

## 收口

作者以 `832eeea199b3192fcd1ce106de303a1df98ad42c` 仅在 setMode(normal) 清 `_override`，原 /plan 命令 toggle 不变；复用原模式 fixture 明确 red→green。独立只复该受影响项 **1 passed in 0.13s**，同一 mypy 对 runtime **1 源通过**，见 `raw/n1-review-runtime-mode-02`／`raw/n1-review-runtime-mode-mypy-02`。来源差异关闭，PermissionRuntime 与排队快照两个模块剩余规格／工程阻断 **0**，均可供 root 消费。

固定源及最终 SHA256 见 `n1-runtime-projection-binding.json`；独审未写任何产品修正、未重复原全部权限／调度测试或构建。普通入口的最终参数同一裁决、same-task once、query／pause 边界和新版固定产物仍须最后确认。

全部验证沿私有既有 venv、外层白名单启动器／tools.run、合成 HOME／config／TEMP，原始命令 joined、scan_hit=false；API 0。普通入口、新版 wheel／安装及 09／11 整票仍待最终候选，不由模块结论推定通过。
