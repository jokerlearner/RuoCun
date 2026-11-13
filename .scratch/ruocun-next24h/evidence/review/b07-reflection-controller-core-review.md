# 42 controller 首轮独审

候选：`281e921afd5821f85e2e006ac60c55887f01657d`，含 `1a8d3e78` MemoryStore 窄端口及 `eb349877` 秘密词边界适配。此为首轮切片记录，不是 42 整票通过。普通 runtime 尚待 MemoryAuditSink.reflected 接口及下面已报修正，未绕过缺失接口启动普通入口。

独立原定向用例 `tests/test_b07_reflection_runtime.py` 与 `tests/test_mvp_loop.py::test_source_health_failure_is_not_pardoned_by_a_write_and_child_nudges_locally`，实际 `2 passed in 0.26s`。白名单/合成环境，`sensitive_match=false`，原回执 `raw/b07-review-reflection-controller-core/`。存储真实 SQLite 恢复证明沿本目录 `b07-reflection-store-review.md`，不重复运行。

已核防重放与消息边界：analysis 接收已发送前缀的深拷贝，只产生数据，不执行模型返回工具，也不直接改主消息；drain 才在 paired 边界持久化 ready。memory apply 位于既有工具串行锁内，稳定非 main scope intent 在全部写之前，result 确认后与 applied 状态一起提交 advisory。旧 ready 配已确认 journal 结果时不再调用 apply；写/结果不确定会 stopped+blocked，不产生新身份掩盖旧 pending。原紧凑 controller 用例实测后台分析完成时主工具仍未配对不发布，配对后才写一次，既有确认结果复用、未知后拒绝继续。

关闭源码顺序为 memory_stop.set → scheduler/tool 清理 → reflector.close；close 只保存分析结果而 `apply_writes=False`，不在关闭阶段新启记忆写入。该点为代码核对，不冒称普通 CLI 取消闭环已运行。轮内健康用例同时核对写入不能抵消连续工具失败，子代理只注入本地 self-challenge，不增加模型 fork。

已向主协调报告的两项未收口差异：

- `reflect_persist.applyConfirmed` 尚调用 publishExpected，新增 touchConfirmed 未被消费；原生 locked 记忆仅刷新日期的来源行为因此仍缺接线。主协调确认 A 正修。
- 反思沿共享 request 的 cache 记录固定 agent=main；冷模式因无 tools 不记 cache。冻结来源应按实际反思模型/usage 记录 distill，challenger 也需用途归因。主协调确认正与 57 统一上下文端口修复，避免复制审计系统。

`eb349877` 对带词边界的秘密模式使用 ASCII 边界，符合冻结 JavaScript 在中文相邻文本中的匹配；未输出任何真实凭据。后续沿现有来源 pipeline 单例与修后普通入口核对，不扩秘密或持久恢复矩阵。

本轮只改独立证据；无全量、构包、付费调用或任务状态修改。最终 42 结论待固定修复与普通入口候选。
