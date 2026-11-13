# 权限分类与普通入口独审

受审候选为 `59bfd7f`（集成同补丁 `96263e3`）、普通入口 `118a6c6` 及能力说明修复 `7c2daf6`，独审树为 `cb5b457`。当前模块与普通入口接缝剩余阻断 0。

对照冻结分类器、模型回退、gate 与审计源码，两阶段 XML 裁决、500 UTF16 单位转录片段、12 条近期记录、用户规则注入、模型回退成功后缓存及原 context/rate-limit 例外均沿既有来源。既有 gate 继续保留显式 deny、危险调用人工确认、熔断与逐批审批来源。D10 的待判 Windows Shell 通过单独 canClassify 回调维持人工，没有伪标为 dangerous。原 gate 子模式复制保留该回调与各自转录来源。

生产入口沿原 request 与当前 ctx.signal 发送分类请求，响应 usage 按实际分类模型计入会话，cache 审计标明 classifier。失败响应保留原异常供模型回退辨认，取消后不自动放行。最终审批来源由 PermissionRuntime 写入会话审计，工作区写入/执行摘要经过原秘密规则与会话已知密钥脱敏。审计写入失败延用来源 best-effort。发现的能力提示仍称分类器后置已由 `7c2daf6` 同步。

独立运行新分类器/审计/权限接线来源测试与已有 gate/runtime/approval/engine/settings/preserve/trust，以及普通受控 TTY 原测试，**118 passed in 5.03s**。权限与 runtime 共 23 源文件 mypy 通过，定向 Ruff 通过。实际回执为 `raw/n24-review-permissions*`，均 exit 0、scan_hit=false。

另外复用 `test_n1_runtime_tty` 的合成配置、InputBroker、DummyOutput 和注入式 streamChatResilient，保存单一普通入口脚本 [classifier-runtime.py](classifier-runtime.py)。明确设置 auto 与普通 Write 的 ask 规则，证实分类器 allow 无人工即可真实写入。另一 Write 的 Stage 1 与 Stage 2 都返回不可解析内容，转同一 broker 询问，人工 n 后零写入；显式 deny 的第三个 Write 不进入分类器也未写入。会话 trace 分别记录 classifier、human、rule，三次分类请求的实际模型与 token 回执为 synthetic-main、prompt 3/completion 1。拒绝路径中含合成账号 key 的摘要被脱敏，执行实参保持原值。

脚本首次未发送 final on_delta，等待可见结束文字时超时，属于独审合成请求接线缺口，原失败完整保留。补与既有 TTY fixture 相同的 on_delta 回调后，r2 同一场景通过。未据首次失败归因产品，也未增加测试框架或故障矩阵。

所有过程使用 tools/run.py 明确白名单、合成 HOME/config/TEMP，显式加载独审源码，根 venv 只提供锁定依赖。真实模型、费用和 Windows Terminal 体验均未执行。此模块复核不替代整个发布候选的工程门禁及安装确认。
