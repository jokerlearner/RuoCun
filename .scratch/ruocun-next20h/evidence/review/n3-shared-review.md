# 35 的 Read 通知和工具批发布边界

固定 `0682221a36b35b9cde810ba55dc176b7df3514aa` 的可选 Read 通知和 `0f0f0b820b49b506215f1fefa2535fef9211c97f` 的工具批边界。冻结 `read_file.ts:130` 在成功构造文本分页后通知绝对路径。产品 worker 只返回展示文本及成功标志，业务线程应用读基线、图槽和成功路径通知。越界 offset 保留读取基线，只有成功文本报告访问。

loop 在工具结果配对保存及图片投影确认后检查当前 Event，然后进入工具批回调。后续 scheduler 边界消费下一轮输入。冻结回调异步发现的失败隔离与实际动态发布仍由 35 入口接线复核。

仅复原绝对 Read 和 scheduler boundary 两个受影响用例，**2 passed in 0.23s**，exit 0，敏感扫描 false，真实及付费模型 API 0。回执见 `raw/n3-review-file-boundary-01`。两项为共享接缝的源码验收，35 的普通入口和整票出口另行验证。
