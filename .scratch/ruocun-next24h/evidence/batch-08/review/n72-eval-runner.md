# 72 评估运行器独立复核

本次候选为 `8ee4a9b992ee7a77759b3295708dda32bebbe68f`。基准为冻结 DAO `dao-f17e189-7ac654a0dc06` 的 `evals/run.mjs`、`score.mjs`、`score.test.mjs`、`materialize-trace.mjs` 和 `tasks/01-parse-query/`。在独立审查树以 Windows x64、Python 3.11 和显式 Node 路径运行。两次验证均由 `tools/run.py` 配置白名单与合成 HOME、TEMP。模型只有本机环回 SSE，外部仓库未克隆，真实和付费模型调用均为零。

## 已核结果

- 来源评分六项及冻结 01 真实普通 CLI 一项共 **7 passed，5.99 秒**。默认 pytest 首次仅执行六项并去选 oracle，随后用 `-o addopts=` 显式运行该用例。实际列出 16 题。01 基线 fail2pass 退出 1，合成模型三次请求，经过真实 Read、Write 后 fail2pass 与 pass2pass 都通过，完成度为 1。输出包含补丁、SQLite 投影、逐条消息、回合 JSONL 和 HTML，脚本闭合符安全编码，合成凭据未进入材料。混合配置和 keyRef 在启动 Agent 前被拒绝，零额外模型请求。未授权联网的 OSS 实例独立归类为 `environment_unavailable`。 [默认回执](raw/b08-review-n72-initial/) · [含 oracle 回执](raw/b08-review-n72-oracle/)
- 使用实际进程树运行 2.1 秒验证器超时。该验证器的孙进程留下 50 次心跳，返回后 250 毫秒内无继续写入。结果为退出 1、`environment_unavailable`，无 Agent 启动回执，合成临时工作区清除。两个 SWE 入口缺合成实例清单时分别退出 2 并返回 `environment_unavailable`。 [独立探针](n72-boundaries.py) · [原始回执](raw/b08-review-n72-boundaries/)
- 复核 Docker 路径使用唯一名称和完整容器 ID，读取真实容器终态后以删除和按名查询确认清理。Docker 生命周期只沿用实施者合成端口回执。Harbor、Terminal-Bench、SWE 数据集和外部实时模型没有运行。 [实施回执](../application/72.md)

## 最终候选

8ee4 的普通入口及本机证据如上。初审发现标准 Linux Harbor/SWE v2 的预检只做版本或导入，无法识别真实会话依赖 Windows SQLite，且保留未知工作区时可能留下额外的明文临时账户文件。另确认进程树自己报告收尾未确认时必须保留现场，输出超限不能作为完整基线或判分材料。

- `e1ca8df5` 新私有账户配置路径实跑原 01 普通入口 **1 passed，4.73 秒**。同候选的适配器探针在 Windows x64 实际加载受控 SQLite，模拟 Linux 在 Agent 前返回 2。验证 51 个复用资产逐字节相同。合成未知结果保留工作区，独立目录的临时内联账户已清理。权重 null 取 1，显式 0 保留，截断输出不能算基线失败。 [普通回执](raw/b08-review-n72-config-fix/) · [适配边界回执](raw/b08-review-n72-external-fix/)
- 最终 `00b810516e510c3daa071b31a896ec630e1102ac` 独立复跑 [既有合成端口探针](../application/n72/external-proof.py)。真实受管端口的错误类型通过合成注入触发 `outcome_unknown`，无 Agent 退出回执，保留隔离工作区并确认临时私有配置已清除。模拟 Agent 自然退出 0、输出超限时，运行器不评分并返回 `environment_unavailable`。 [最终回执](raw/b08-review-n72-process-final/)

第 72 票独立技术复核通过。真正 Windows 进程树的正常超时与临时工作区清理已实跑；退出确认丢失、截断和 Docker 终态由合成端口复核。标准 Linux 外部运行环境、真实 Docker、Harbor、SWE 数据集和外部实时模型仍未运行，无第三方成绩。最终候选相对 8ee4 的 `src/`、`tests/`、`tools/`、构建配置和开发锁无字节差异，本报告没有重新构包或扩大全量范围。
