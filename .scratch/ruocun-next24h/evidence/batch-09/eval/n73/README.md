# 73 · 记忆与缓存评估

冻结依据为 DAO evals/memory 的 extract、recall、injection_ab、report 与 lib 评分，及 scripts/accept-memory.sh、scripts/accept-cache.sh。六个合成记忆 fixture 文件原样复用。历史完整 fixture 保存在冻结源归档，通过审核过的外部 fixture 目录按需读取。

- 8项来源评分断言覆盖提取与画像召回、空抽取 N/A、stale 泄漏、人工相关性锚、A/B 候选身份与报告。普通入口用真实 RuoCun CLI 及本地 SSE，实际第一进程反思写入1条合成 pnpm 记忆，第二进程启动注入1条且根据该前缀回答，输出工具标记0。
- 缓存沿冻结三轮与两次 /cost 的顺序验证实际 cache.jsonl。合成主回合 hit/ratio 为 0、50%、95%。这是工程采集结果，不是供应商真实缓存保证。
- 首次普通记忆运行按旧版 DeepSeek 配置走异步反思，单轮退出前没有确认写入，正确记录 not_observed。真实产品支持同步的非 DeepSeek 路由，以受控 Zhipu 合成账户复验，仍运行同一真实 CLI。
- 提取候选确含合成密钥，传给独立语义评审前已脱敏。测试核对所有本地模型消息正文和报告均无该明文。账户沿72的私有目录规则清理；未知结果保留工作区，未调用外部模型。
- 最终 73 与 74 定向合计15项通过。72的实际 CLI 与冻结任务合并接线回归1项通过。Ruff 和 Mypy 通过。样例报告位于 sample 目录。

独审回修使普通评估 CLI 与直接评分共用离线网络策略。离线 urllib opener 禁用代理、拒绝重定向和非环回目标，保留产品自身的观察型 HTTP/HTTPS 连接处理器。合成双服务中首端点收到请求，重定向端点零请求。73/74 合计16项通过，72普通入口回归1项通过。显式 live 入口仍采用普通产品传输。

按批次09更新后的产品配置规则，评估账户复用产品 loadProfiles。合成 version=3 配置在调用 Agent 之前报告环境不可用，红绿回执见 eval-account-version-red 和 eval-account-version-green。
