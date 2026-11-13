# 01 — 修复记忆来源标签与文件校验冲突

Type: task
Status: resolved
Assignee: Codex /root；独立复核 /root/compact_audit
Branch: integration/ruocun-migration（既有脏工作区，保留其它改动）
Blocked by: none
用户体验验收：not-required（合成偏好、真实产品入口自动验证）

## 授权和范围

用户于 2026-11-13 明确要求核实并修复记忆来源字段冲突，验证用户偏好下次启动能正常召回。
沿现有五类型、三域、Markdown 格式作局部兼容修复，不改变存储结构、反思开关、来源文件校验或其它记忆机制。
直接执行依据：需求和验收已明确，修复精确的来源标签判断，无需引入新的公共数据模型。

## 文件归属

- root：`src/ruocun/memory/validate.py`、`tests/test_n4_memory_format.py`、本任务记录和验证启动脚本。
- 独立验证代理：仅新增 `tests/test_memory_source_recall.py`，不修改产品代码。
- 已有未提交改动不覆盖、不整体暂存或提交。

## 验收

- [x] 修改前复现 `user_stated` / `inferred` 被当成不存在的文件而漏召回。
- [x] 两种精确来源标签不再进行文件存在性/哈希校验；有效期仍适用。
- [x] 显式文件路径仍检测内容变化和删除，标签同名文件可用 `./` 路径区分。
- [x] 第一独立产品进程反思写入合成偏好；第二全新产品进程磁盘重读，并在真实 HTTP 模型请求中注入偏好。
- [x] 受影响记忆/反思回归、定向 Ruff/Mypy 和独立复核通过。

## 验证边界

所有产品和测试子进程从明确白名单环境启动，HOME、配置、会话和临时目录使用合成值。
只使用本地合成 HTTP 服务，不调用真实模型，不读取或修改真实用户记忆。自动召回验证不等于真实模型遵循偏好的质量测量。

## 证据

[修复与完整回执](../README.md)。原格式回归 4 failed / 15 passed、普通入口 1 failed；修复后受影响回归 146 passed、跨进程普通入口 1 passed、Ruff/Mypy 通过。
[独立复核](../evidence/review.md)另亲跑格式 19 passed、普通入口 1 passed、Ruff 与 diff 检查，无本范围阻断。
产品改动仅 `memory/validate.py`，精确识别两个非文件来源标签。没有迁移或重写既有记忆，没有真实模型调用；工作区改动未提交。
