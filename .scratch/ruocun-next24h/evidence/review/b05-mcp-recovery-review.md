# 批次 05 第 54 票最终独立复核

候选 `6842a3c4`（含 `51908a95` 关闭状态保护），另独立核入最终摘要接线 `c85b80d5`。使用根 `.venv` 已验 SDK 运行依赖，source-pytest 显式加载独审树源码；白名单合成 HOME、假凭据、真实 SQLite、独立 stdlib HTTP/SSE 与回环模型。未改产品或纯包环境。

实际文件 `tests/test_n54_mcp_recovery.py` 两参数独跑 **2 passed in 23.30s**。[HTTP/SSE 回执](raw/b05-review-http-sse-recovery/command.json)

两条均先收到确切 JSON-RPC error，错误正文脱敏，工具保存为 result_committed、返回模型并正常结束。随后显式继续原 session ID，远端 effect 写一后 HTTP503 或 SSE 断流、无 RPC 结果；普通 CLI 退出 **74**。原会话重开要求新工具调用 ID 时仍退出 74，不发新模型请求，effect 保持 **1**；实际工具 journal 中旧调用 outcome_unknown、新 ID 不存在。已确认旧错误结果没有被改成 unknown。

配置含明确合成 URL query/header 凭据，所有三进程 stdout/stderr 均没有该值；SDK 原始异常日志亦在断线分支被覆盖核验。源码的 manager 拥有日志 filter 在交 handler 前展开异常并统一脱敏，保留异常类别；已用过连接的秘密在 manager 生命周期内保留，不因同名 add 改声明而丢失。关闭后移除本 manager 的 filter。

连接拥有者异常退出/确切 transport exception/EOF 唤醒唯一串行请求；已收 RPC 结果/错误优先，普通通知和其它处理错误不冒充 transport 死亡。工具未知进入 journal 阻断，不自动重放。正常 close 失败仍报错；若会话已有 unknown，runtime finally 仅输出关闭未确认的异常类型，保留原 74，不以关闭异常覆盖业务未决，也不伪称关闭成功。

`executionConfigDigest` 规范化当前 `_holders` 的实际配置深副本，只返回 SHA256，不读取新声明来假定旧连接已经换配置。沿原 53 同名 add 用例独复：声明 URL 改为 replacement、旧 holder 未重连时实际配置摘要保持不变，实际 **1 passed in 1.88s**。[实际配置身份回执](raw/b05-review-active-mcp-identity/command.json)

最终 `c85b80d5` 仅窄改摘要消费：普通初始化、每次子代理准备以及 `/mcp` 变更成功后使用该实际摘要；专属子 MCP 仍绑定其独立 definition_digest，恢复前比较摘要并核精确目录。只读确认 Windows 工作树收尾增量在 journal 保存最终 live roster 后关闭专属 MCP，再执行 Git 清理，外层 finally 保持幂等；不将此代码阅读声称为额外 Git/MCP 组合已实测。

stdio 未重跑，沿用 [51](b05-mcp-cli-review.md)、[显式重开](b05-sessions-review.md) 与[普通子专属 MCP](b05-agent-mcp-review.md) 已绑定的独立证据。原来源 effect=2 反例与 ADR-0003 目标 effect=1 分开，未宣称远端 exactly-once。

两份新回执退出 0、敏感值扫描无命中。54 及本批相关高风险消费接缝已审范围无阻断，可在 `c85b80d5` 固定产品执行唯一里程碑出口。本次未全量、构包或代验真实终端体验。
