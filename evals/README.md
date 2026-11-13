# RuoCun 评估入口

以已安装标准包的 Python 从仓库根运行。冻结 DAO 快照为 dao-f17e189-7ac654a0dc06。16 份任务、能直接执行的测试、容器配方和 HTML 模板按原始字节保留。任务工程按本轮范围交付，成套真实模型成绩后置。

## 确定性评估

- 查看任务用 `python -m evals.run --list`。
- 有本地合成模型端点时，运行 `python -m evals.run --config <合成配置.json> --output <新目录> --runs 1 --node <Node路径> 01-parse-query`。
- Runner 从空临时目录启动普通 CLI。对双轨任务先检查基线确实失败，再运行 RuoCun，最后运行冻结的 fail2pass 和 pass2pass。测试资产位于代理工作目录外。评估模式没有额外的 OS 沙箱保证。
- 每次运行写入 agent 输出、补丁、验证器输出和结构化 meta。轨迹通过产品 SQLite 只读投影生成逐条消息、turns.jsonl、索引和自包含 HTML。输出目录已存在时拒绝覆盖。重复次数默认 3，超时默认 180000ms。环回模型的分数只代表合成工程回路。
- 报告区分 Agent 超时、运行错误、任务基线无效、环境不可用和判定失败。查找失败记录时以 meta.json 为准。

## 外部资源

- OSS 和 Docker 任务显式使用 `--allow-network` 后才尝试拉取及准备验证环境。外部模型还需 `--allow-live`。对 Docker 测试保留断网、降权和限额参数。实际镜像、远程任务和供应商分数仍待验。
- SWE 本地实例清单检查用 `python -m evals.swebench.adapter --instances <instances.jsonl> --list`。启用配置、输出和联网后会生成官方 JSONL 补丁输入。官方验证另行运行。容器路线使用 python -m evals.swebench.adapter_v2，并提供已准备的容器、实例基线、容器内可用标准包与配置。容器客户端若超时，保持现场供核对。
- Terminal-Bench 从 `evals/terminal-bench` 使用 Harbor 的 `--agent-import-path agent.harbor_ruocun_agent:RuoCunAgent`。调用者提供可用的 Harbor、任务环境、容器内 Python 安装及显式账户。缺少组件时报告环境不可用。官方容器版尚无本项目验证结果。历史任务难度覆盖与元数据按冻结资产留存，新适配器不修改任务数据。

## 记忆、缓存和反思

- 记忆提取与召回用 python -m evals.memory.run both --config <账户.json> --output <新目录>。可选 extract、recall 或 injection-ab。A/B 的 pull 轴按标题由 judge 模拟是否读取，记录比较结果。默认只读随仓冻结的合成记忆样本。其余历史样本保存在冻结 DAO 归档中，复现时以 --fixtures 指向已审核的来源目录。
- 缓存与跨会话验收用 python -m evals.memory.accept cache 或 memory，同样提供 --config 和 --output。缓存取普通 CLI 的主回合审计；记忆在合成工作区实际写入后用新进程召回。首会话显式启用产品的反思。若该供应商的异步反思在退出前尚未完成，报告按实际记为未观察到持久化。
- 反思用 python -m evals.reflect.run --config <账户.json> --output <新目录>。六个冻结用例含报警和在轨正控。无效回包单列，advisory 由独立语义 judge 判分。
- 评估子命令默认使用显式环回端点，本地合成回执与 --allow-live 的真实模型结果分别记录。报告目录须为新目录。真实模型结果仍待授权验证。
