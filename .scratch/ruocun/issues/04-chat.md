# 04 — 用兼容账户配置完成首轮流式对话

Type: task
Mode: AFK
Status: resolved
Assignee: /workbuddy/implement_04_chat
Branch: impl/04-chat
Worktree: .worktrees/wb-i04
Parent: [完整迁移规格](../spec.md)
Blocked by: [03 — 安装开发包并从仓库外调用ruocun](03-boot.md), [02 — 隔离运行冻结参考并生成一条可比对轨迹](02-oracle.md), [D08 — 确定 Python 并发、任务与恢复技术路线](../../ruocun-discovery/issues/08-python-runtime-decision.md), [D09 — 确定持久化与外部扩展的兼容边界](../../ruocun-discovery/issues/09-storage-extension-decision.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

从profile/dotenv及模型覆盖→冻结提示/参数→Chat SSE→回答；无效配置、UTF8分片与请求golden可验。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-455](../module-map.md#mm-455)、[MM-457](../module-map.md#mm-457)、[MM-460](../module-map.md#mm-460)、[MM-462](../module-map.md#mm-462)、[MM-464](../module-map.md#mm-464)、[MM-466](../module-map.md#mm-466)、[MM-439](../module-map.md#mm-439)、[MM-443](../module-map.md#mm-443)、[MM-444](../module-map.md#mm-444)、[MM-566](../module-map.md#mm-566)、[MM-475](../module-map.md#mm-475)。

## 共享接口与并行

接口领域：模型/配置。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [CFG-01](../acceptance-matrix.md#cfg-01) — 账户格式：本票路径覆盖的子案例满足“v2 格式和宽容边界沿用源；新增/删除/切换及保存不丢其它顶层数据”。
- [x] [CFG-02](../acceptance-matrix.md#cfg-02) — 模型目录：本票路径覆盖的子案例满足“保持冻结 ID/endpoint/window/vision/output cap；自定义网关不猜便宜档”。
- [x] [CFG-03](../acceptance-matrix.md#cfg-03) — 模型继承：本票路径覆盖的子案例满足“override > agent > parent；缺 parent 明确报错，不暗换 provider”。
- [x] [CFG-04](../acceptance-matrix.md#cfg-04) — 凭据优先级：本票路径覆盖的子案例满足“inline 优先；缺 key 不靠通用环境变量自动挑账户；fallback 准确显示且不泄漏”。
- [x] [CFG-05](../acceptance-matrix.md#cfg-05) — dotenv：本票路径覆盖的子案例满足“只用参考简化方言；已有环境含空值优先，不增加 export/插值语义”。
- [x] [CFG-06](../acceptance-matrix.md#cfg-06) — 环境开关：本票路径覆盖的子案例满足“逐变量复刻取值判据；AUTO_APPROVE=0 与 TRUST=0 不混同”。
- [x] [CFG-09](../acceptance-matrix.md#cfg-09) — 品牌/数据边界：本票路径覆盖的子案例满足“RuoCun 自身会话隔离；不自动移动/接管旧 DAO 会话；配置别名写回策略依决策票”。
- [x] [WIRE-01](../acceptance-matrix.md#wire-01) — 请求保真：本票路径覆盖的子案例满足“固定 system/messages/tool schema 顺序、角色/字段/空值和 extra 覆盖与冻结 oracle 一致；品牌替换差异白名单”。
- [x] [WIRE-02](../acceptance-matrix.md#wire-02) — 输出上限/思考参数：本票路径覆盖的子案例满足“128000 默认、256000 特殊重试并裁 cap；max_tokens/max_completion_tokens 选择、thinking/effort/parallel/tool_choice 原规则；不加未配置采样参数”。
- [x] [WIRE-03](../acceptance-matrix.md#wire-03) — Chat SSE 分帧：本票路径覆盖的子案例满足“文本/reasoning/工具参数按 index 完整累积；usage/finish_reason 只按有效数据确认”。
- [x] [WIRE-05](../acceptance-matrix.md#wire-05) — 历史 wire 清洗：本票路径覆盖的子案例满足“null 转空串；工具轮 reasoning 按原规则带回；内部字段不泄漏”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

**实现链**（`impl/04-chat`，起点 `19b3c01`）：`9c7c43e` 主体实现 → `2b896f1` 冻结提示词资源按原始字节保真 → `df552f4` 收尾验证证据；实现者证据见[本票证据](evidence/04-chat/README.md)、[收尾核验](evidence/04-chat/final-check.md)及 `raw/summary.json`、`raw/demo-output.json`。
**独立复核**：未参与实现的独立 merger 在 `.worktrees/wb-m04`（`merge/04-chat-verified`）合入候选与集成 tip，亲自复验后提交 `dbdd0bc`，证据见[04独立复核](../../integration-evidence/04-chat/README.md)及 `raw/boundaries.json`、`raw/commands.json`、`raw/pytest-command.json`。主工作区已 `--ff-only` 快进至 `dbdd0bc`。

- 可运行路径：`python -m ruocun --chat-demo <合成配置目录>`；合成 config/compatibility/.env → 冻结提示词与请求参数 → 本地合成 loopback SSE（3 字节分块，中文/emoji 跨字节分片）→ 真实 HTTP POST + 增量严格 UTF-8 解码 + 按 index 累积 → 回答；输出结构化 JSON 含请求 golden、不含 secret。新增显式 `--chat-demo` 为 INTENTIONAL-DELTA（任务票授权一次性 prompt 路径），既有 `--version`/`--help`/包资源/普通 prompt exit 69 行为不变。
- 实现者回归：五项入口全 0（默认 pytest **208 passed / 3 deselected**，任务03 基线 29 + 新增 179；Ruff、mypy 28 文件、build、`ruocun_acceptance offline` 4 case）；merge 集成 tip 后重跑同样全绿；逐组 red→green 记录在证据 README §4。
- 独立复核亲跑：五项入口全部亲自执行并读原始输出（pytest 208 passed / 3 deselected、ruff、mypy 28 文件、build sdist+wheel、offline 4 case）；仓库外中文空格路径干净 venv 只装 wheel 验证提示词资源随包可读、版本/帮助、exit 69 与 `--chat-demo` 跑通；7 类配置失败（缺目录/坏 JSON/未知 version/缺 id/缺 path/缺 key+通用环境变量）全部 exit 71 且无泄漏；非法/不完整 UTF-8、SSE error、401、无产出断流明确抛错，有产出断流标 `partial` 不伪成功；成功与失败路径均独立核实 loopback 服务 `listening_before=true→after=false`、`socket_fileno=-1`、线程死亡、端口 `NOT_LISTENING`，不只看产品自报字段。
- 来源真实性抽查：请求 golden、模型目录、环境谓词、SSE 分帧预期与冻结 `client.test.ts`/`sse.test.ts`/`system_prompt.test.ts`/`profiles.test.ts`/`model_selection.test.ts`/`env_file.test.ts` 及 D09/R-05~07 一致，未发现从 Python 实现输出回填期望的自证断言。
- 分层状态：产品自动测试本票路径通过；来源 oracle 本票 **not-run**（02 已验部分驱动，不冒充全量）；真实模型 **0 次**；终端/HITL **未验**（ADR-0004 集中最终 77/78/85）；Windows 全功能/安装产物仅仓库外 wheel-only CLI 子集部分执行；其它平台实机 not-run。故障归因：SOURCE-DEFECT 无、PORT-REGRESSION 无、INTENTIONAL-DELTA 8 项、ENV 3 项、UNVERIFIED 4 类，详见证据 README §8。
- 覆盖：CFG-01/02/03/04/05/06/09 与 WIRE-01/02/03/05 的**本票路径子案例**；Responses 桥、client 重试与非流式 fallback、idle watchdog、429/529、费用累计、系统凭据后端、完整 Agent/StoragePort、真实终端与安装产物留给 05/06/28/58/77/78/85 等票，**母案例族与全量规格未标通过**。

**主代理对独立复核两项观察的处理**：
- O-1：`[DONE]` 缺失但数据帧完整、EOF 干净结束时返回 `status=complete` + 完整答案（`finish_reason=null`）。核对冻结 `client.ts:210/313-337`，来源以传输 EOF 为终止、`[DONE]` 仅作被跳过哨兵；本票属忠实迁移，**不改变既定行为、不新增差异决定**，作为 WIRE-03 后续子案例的终止标记语义观察登记，留待后续票按 oracle 展开。
- O-2：独立复核指出 `tests/test_client_wire.py:309`、`tests/test_chat_path.py:74/87`、`tests/test_config_pure.py:114-120`、`tests/test_prompt.py:154-160` 存在结构自洽/产品自报字段的弱断言，独立 oracle 强度有限（非输出回填）。登记为后续补独立 oracle 时的加强项，不阻断本票路径结论，不私改产品掩盖。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：工程入口03解耦完整发布前置后，将本票真正需要的兼容/平台决定显式列为依赖；未关闭前不得调度本票，不减少已确认验收范围。

- 2026-11-05：02/03/D08/D09全部resolved，本票已就绪但未领取。用户要求在03后换WorkBuddy；接手主代理先核验新工具能力，读取既定契约及冻结源码后调度，不重复搭建03。

- 2026-11-05：WorkBuddy主协调会话接手。核对实际HEAD `98154de9f6ab095cd7e66adffdfbd93c6dedd0d6`、干净工作区与两个frontier；实现图仅本票就绪。已实际创建能力核验worktree `.worktrees/wb-capcheck` 并派发两次独立上下文只读子代理，核实其cwd/分支/HEAD；本客户端子代理无原生cwd参数，工作目录由绝对路径prompt指定并自行核验，后台结果随调用同步返回。按既定隔离要求领取本票，分支 `impl/04-chat`、worktree `.worktrees/wb-i04`，起点为含本领取记录的集成tip；实现与独立merger分别派发。沿用已确认五项入口、ADR0003/0004/0005与唯一StoragePort契约，活动DAO只读、冻结快照为唯一来源，真实模型调用无授权不执行。

- 2026-11-05：实现主体 `9c7c43e` 完成（31文件/+4703行），收尾资源字节保真 `2b896f1` 与补证 `df552f4` 后候选干净；独立 merger `dbdd0bc` 两次merge、五项入口、仓库外wheel安装、失败/取消/资源退出边界与来源抽查全部亲自复验通过，无阻断缺陷，建议接收。主工作区 fast-forward 至 `dbdd0bc`，本票 resolved，正式完成 3/84。O-1/O-2 按上文记录，不扩为全量规格通过。前置释放后 05/06/07 已由主代理标记 ready-for-agent。
