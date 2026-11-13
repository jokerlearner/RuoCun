# 自动出口工具独立复核

候选`e9c779816e30df55de2792edd4f0c98a22ab9918`，实施者/root/workflow_tooling；独立复核由未参与实现的主协调/root在另一worktree sprint-tooling-review执行。基于30897bb合入候选及最新596a7c4，产品/工具代码与候选一致；后续文档仅来源优先和测试收口，不重跑无关完整套件。

规格来源：ADR-0006及工程票01；测试投入按用户新ADR-0009。容量约束下Standards与Spec两轴由同一独立审查者分别核对，未宣称并行双代理审查；产品07另由独立审查代理执行，不共享候选实施角色。

## Standards

未发现阻断。实现范围限依赖查询、既有开发测试、格式文档和独有证据；未改产品src、依赖或公共状态。证据仅数据解析，路径/JSON/schema/hash/commit均校验；Git固定argv、环境白名单、禁外部diff/textconv/fsmonitor/replace与交互，全局配置不继承。角色与真实独立上下文仍需主协调核实，字符串不同不等于自动证明身份。

## Spec

未发现未解决阻断。仅显式79→78及84→77的automatic边允许消费证据；验证产品→review→集成→HEAD完整提交链、已提交且未漂移的证据及权威矩阵逐项集合。普通/D依赖保持整票门禁，85不接受单改resolved而人工pending，claimed票不重新派发。

独立亲跑复用已存在用例，不新增测试：

- review-tooling-existing-core：8 passed / 48 deselected，涵盖79正例、证据篡改、85人工门禁/缺边/覆盖及claimed不重派。
- review-tooling-existing84：1 passed，84消费77自动出口正例。
- review-tooling-live-graph：真实84票为5 resolved / 2 claimed / 77 blocked，frontier为空；77/78仍pending/none，不产生产品通过。

全部通过白名单外层启动器及tools/run.py，独立新venv、合成HOME/配置/临时目录；原始回执见[raw](raw/)，scan_hit=false。实现者已有56工具用例、375全量及五入口结果作为其证据保留，独立者未重跑或冒充亲跑它们。Git缺失、证据漂移或产品输入变化保持阻塞；完整矩阵hash变化会保守使旧出口失效，限制已在格式说明明确。

本工程适配可集成并结题，不意味着77/78自动/人工已通过。自有命令均已退出，venv和合成状态保留，无真实模型、密钥或用户终端操作。产品图当前真实前置仍按各票维护。
