# 05 — 通过Responses路由完成同一对话/工具回合

Type: task
Mode: AFK
Status: resolved
Assignee: /workbuddy/implement_05_responses
Branch: impl/05-responses
Worktree: .worktrees/wb-i05
Parent: [完整迁移规格](../spec.md)
Blocked by: [04 — 用兼容账户配置完成首轮流式对话](04-chat.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

现有桥路由、function输入输出/reasoning items和结束事件可回放。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-441](../module-map.md#mm-441)、[MM-444](../module-map.md#mm-444)。

## 共享接口与并行

接口领域：模型。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIRE-04](../acceptance-matrix.md#wire-04) — Responses 桥：本票路径覆盖的子案例满足“路由判据、store/include、effort 映射及统一事件回传与冻结桥等价”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

**实现**：`2884cac8802cc349804f768821726026bd7dc294`（`feat(05-responses): 通过Responses路由完成同一对话/工具回合`，12 文件 / +1933 行），分支 `impl/05-responses`、worktree `.worktrees/wb-i05`，起点 `bbf4aa9`。实现者证据见[本票证据](evidence/05-responses/README.md)及 `raw/demo-output.json`、`raw/demo-command.json`。
**独立复核**：未参与实现的 merger 在 `.worktrees/wb-m05`（`merge/05-responses-verified`）先由前序会话完成合入 `5e89e75`（候选+集成 tip 双父合并），本轮复核补完后提交 `b0b5052d8a54fee9b91f2dfceaff6bb015fcb115`，证据见[05独立复核](../../integration-evidence/05-responses/README.md)及 `contract.py`、`boundaries.py`、`verify_demo.py`、`raw/*.json`。主工作区已 `--ff-only` 快进至 `b0b5052`。

- 可运行路径：`python -m ruocun --responses-demo <合成配置目录>`；合成配置 → Responses 路由判据 → 冻结桥请求（store/include、effort 映射、tools/strict、function_call/function_call_output、reasoning items）→ 本地合成 HTTP/SSE 服务 → 统一 Chat 事件 → 两轮工具回合答案；输出结构化 JSON 含请求/事件 golden、不含 secret。新增显式 `--responses-demo` 为 INTENTIONAL-DELTA，既有 `--version`/`--help`/包资源/普通 prompt exit 69/04 的 `--chat-demo` 行为不变。
- 实现者回归：5 组 TDD、48 条新增测试逐组 red→green；合入后全量 pytest **256 passed / 3 deselected**（208 基线 + 48）、Ruff 0、mypy 30 文件、offline 4 case、build sdist+wheel 全 0。
- 独立复核亲跑（读 raw 原始输出，不采信实现者声称）：五项入口全部亲自执行，pytest `256 passed, 3 deselected`、ruff `All checks passed!`、mypy `30 source files`、build 产出 sdist+wheel、offline 4 case 全 passed，均 exit 0；`contract.py` **36/36**（把 04 基线 `buildRequestBody` 动态加载逐字段对比，默认 Chat 输出与 04 一致；路由成立→`/responses`+Responses 形状、不成立→`/chat/completions`+Chat 形状；冻结两轮工具回合 golden 逐项匹配）；`verify_demo.py` **28/28**（仓库外中文空格路径干净 venv 只装本票 wheel，请求/事件 golden、effort、50000、input_image、usage 80/20、清理回执）；`boundaries.py` 11 个流场景明确抛错或 `status=partial`、6 个 CLI 场景全部 exit 71 带具体诊断、无 secret、无伪成功。
- 共享 client 契约：`git diff bbf4aa9..2884cac` 确认 `types.py` 未改、`buildWireMessages(use_responses=False)` 是 04 基线已预留参数，`streamChat` 签名、`StreamResult`、`StreamChatOptions`、`StreamDelta`、`Usage`、事件类型、04 的 `buildWireMessages`/`normalizeUsage`/`ChatAccumulator` 语义未变；`buildRequestBody` 新增可选 `use_responses` 默认值下输出与 04 一致。**无破坏性变更**，仅兼容扩展（新增 `responses.py` 公开接口、`cli.py` 分发、新增局部变量 `chunks`，提示 06 重试层在此基础上组织）。
- 资源退出：自建服务成功/失败两条路径独立证实 `listening_before=true→after=false`、`socket_fileno=-1`、线程死亡、端口 NOT_LISTENING；仓库外自建目录与 `.ruocun-acceptance/` 已删除，4 个本地端口无监听遗留。
- 来源真实性抽查：预期来自冻结 `responses.ts`/`responses.test.ts`/`client.ts`/`types.ts` 断言与 fixture 及已确认规格，未发现从 Python 实现输出回填的自证断言。
- 分层状态：产品自动测试本票路径通过；来源 oracle **not-run**（未重跑 Node oracle）；真实模型 **0 次**；终端/HITL **未验**（ADR-0004 集中最终 77/78/85）；Windows 全功能/安装产物仅仓库外 wheel-only CLI 子集；其它平台 not-run。故障归因：SOURCE-DEFECT 无、PORT-REGRESSION 无、INTENTIONAL-DELTA 8 项、ENV 3 项、UNVERIFIED 4 类，详见实现证据 §8。
- 覆盖：WIRE-04 **本票路径子案例**（路由判据、store/include、effort 映射、128000 cap、tools/strict、可选字段透传、function_call_output 配对、reasoning items、assistant null content、input_image/input_text、内部字段不泄漏、completed/incomplete/error/text/refusal/reasoning/tool-call 增量、`[DONE]`、无完成事件断流、usage 归一化、finish_reason、两轮工具回合、请求/事件 golden）。**母案例族 WIRE-04 未标全量通过**。
- 明确未完成：冻结 `responses.test.ts:76-86`「流式失败后非流式兜底」属 06/WIRE-07 重试层，本票不引入重放（ADR-0003）；client 重试/idle 240秒/429/529/background/费用累计 → 06/07/28；无 `response.output` 时 `[...output.values()]` 回退、incomplete 的 usage/items 组合、多并行 function_call 跨 index、错误事件各形状、`output_item.done` 非 function_call 类型 → 有分支但未单独建独立来源断言，登记为后续子案例；完整 Agent/StoragePort/三类 epoch/系统凭据后端(58) → 后续票；来源 oracle 全量 215 文件 / 真实 Node 轨迹 not-run。

**主代理对独立复核观察项的处理**：
- O-1：6 处弱/自证强度断言（`tests/test_responses_client.py:120`、`test_responses_path.py:107-113/183-214/237`、`test_responses_request.py:158/166`、`test_responses_stream.py:107`）均为结构自洽或产品自报字段，非输出回填；登记为后续补独立 oracle 时的加强项，不阻断本票路径结论，不私改产品掩盖。
- O-2：产品自带失败边界测试粒度粗，独立复核已用 `boundaries.py` 补强并保留证据；后续票按同一严格程度复验。
- OBS：前序会话在复核 worktree 留下的 `.venv`/label 与仓库外旧目录未被本轮采信或使用；ENV 复用 `i03/.cache/wheels` 公开闭包，均如实记录。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：主代理确认前置 [04](04-chat.md) 已 resolved 并集成至 `dbdd0bc`，按 `issue_graph.py` 真实 frontier 将本票由 blocked 释放为 ready-for-agent。接口领域与共享 client/session 契约由主代理统筹；05/06 均涉及 `src/ruocun/client/client.py`，并行时须按主代理分派的边界避免各自重定义。

- 2026-11-05：04 结题并集成至 `7623e7d` 后，主代理按真实 frontier 领取本票，分支 `impl/05-responses`、worktree `.worktrees/wb-i05`，起点为含本领取记录的集成 tip。按隔离要求派发独立实现子代理，独立 merger 另派。共享接口边界：本票只在 `src/ruocun/client/` 内扩展 Responses 路由与 `responses.py`，复用 04 已建立的 `client.py`/`types.py`/`sse.py` 契约；如需改变 04 的公共 client 契约，先向主代理报告具体差异，不自行重定义。06 因同改 client 重试层，待本票接口稳定后再派；07/58 保持 ready-for-agent。

- 2026-11-10：实现候选 `2884cac` 交回后，前两个独立复核子代理分别受频率限制与会话中断影响，只完成合入 `5e89e75`、未留下复核证据；主代理核实真实状态后重新派发独立 merger，补完全部复验并提交 `b0b5052`（9 个证据文件，工作区干净）。两次 merge 历史、候选祖先关系、五项入口亲跑、共享契约 36/36、仓库外安装 28/28、失败/取消边界与资源清理均核实，无阻断缺陷，建议接收。主工作区 fast-forward 至 `b0b5052`，本票 resolved，正式完成 4/84。05 的直接后继 28（还需 07）与 64（还需 18）仍未满足，frontier 保持 06/07/58。
