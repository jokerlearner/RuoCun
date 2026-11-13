# 41 子代理隔离入口候选

对照冻结 DAO `src/tools/agent.ts` 及 `agent.test.ts` 的真实派发参数、隔离目录与清理语义。`AgentRequest` 传递 fork 和 isolation，显式模式覆盖旧 isolate 参数。fork 与模型、权限模式覆盖及显式工作区隔离互斥。fork 使用自己的派发身份，普通定义的强制后台设置不影响 fork。Agent 保留来源工具描述及 schema。

`openAgentWorktree` 复用 27 的 Git 创建口，worktree 和 remote 都创建同机工作树。Git 已知前置失败与写入结果未知分别返回既有异常类型，组合入口决定如何反馈。`finishAgentWorktree` 仅对本实例创建且确认干净的工作树清理目录和分支，有未提交文件或独有提交就保留并返回定位。普通代理继续使用只读 `verifyAgentWorktree` 核同一 Git common dir、私有根、登记分支与 HEAD。该检查不会取得清理所有权。

首次来源测试红为缺接口。深层 Windows 合成仓库首次运行还发现 Git `rev-list` 会把未分隔的提交范围当作候选文件探测，出现 Filename too long。添加 `--` 分隔 revision 与路径后，原深度下的真实 Git 测试通过，核对未提交文件、独有提交保留、干净工作树清理以及 detached 后拒绝恢复绑定。另一定向用例覆盖参数冲突、定义不覆盖 fork 路由、已知失败及未知错误传递。两项定向与 Ruff、mypy 通过，均用白名单、合成 HOME 和临时仓库。普通入口、真实子模型请求及 fork 核心由对应负责人接续集成。
