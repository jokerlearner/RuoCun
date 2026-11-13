# 任务 05 — 通过Responses路由完成同一对话/工具回合 · 实现与验证证据

- 分支：`impl/05-responses`；worktree：`.worktrees/wb-i05`（本票唯一工作根目录）
- 起点（已提交集成 tip）：`bbf4aa966a17b972324cff069ca88a7d328ec4c1`（`docs: 领取任务05并修正58前置状态`）
- 证据绝对路径：`D:/java supplement/Firstcode/RuoCun/.worktrees/wb-i05/.scratch/ruocun/evidence/05-responses/`
- 状态：本票路径已实现并通过自动验证；**母案例族 WIRE-04 未标全量通过**（按票「本票完成不表示整族或全量规格通过」）。

## 1. 环境与基准

| 项 | 值 |
| --- | --- |
| OS | Windows-10-10.0.26200-SP0（Windows 11 build 26200），AMD64 |
| Python | CPython 3.11.9（`-I -X utf8`；`.venv` 建在本 worktree 内） |
| 开发依赖 | `requirements-dev-win311.lock`（18 包固定闭包，wheel 逐 `--require-hashes` 校验）；主工作区无 `.cache/wheels`，复用 `i03/.cache/wheels` 的 18 个已核验公开 wheel（只读复制到本 worktree `.cache/wheels`，**未改锁文件**） |
| 工具 pin | Hatchling 1.33.0 / build 1.6.1 / pytest 8.4.2 / Ruff 0.17.3 / mypy 2.4.1 |
| 唯一冻结来源 | `dao-f17e189-7ac654a0dc06`，源码树 SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`（805 成员，02 已校验）；解包只读副本 `.worktrees/reference-dao-f17e189-7ac654a0dc06/source/`；活动 DAO `dao-code` 保持只读且不作来源 |
| 本票读取的冻结源码 | `src/client/responses.ts`（133 行）、`src/client/responses.test.ts`（105 行）、`src/client/types.ts`、`src/client/client.ts`（416 行，路由调用点/usages/wireMessages）、`src/client/sse.ts` |
| 契约来源 | `.scratch/ruocun-discovery/research/09-storage-extension-route.md`（StoragePort v1 / 三类 epoch；Grep 确认无 client 相关契约，本票不重造）、`08-python-runtime-route.md`（:193 确认 WIRE-04 归本票且不改变 D09 模型路由所有权）、ADR-0003/0004/0005、规格 R-05/R-06/R-07 与 T-01..T-04 |
| 04 已建立契约（复用） | `src/ruocun/client/{client,sse,types}.py`、`src/ruocun/config/*`、`src/ruocun/prompt/system_prompt.py`、`src/ruocun/chat_demo.py`、`cli.py` |
| 起点基线 | 默认 pytest **208 passed / 3 deselected**；offline 4 case 全 passed；ruff/mypy(28 文件)/build 全 0（label `i05-base-*`） |

> 本票**不实现** StoragePort / 会话持久化 / recovery / 三类 epoch；未发明第二套 schema 或 epoch 契约；未修改活动 DAO 目录。

## 2. 交付物与对应表登记请求

| 模块 | MM | 职责 / 本票动作 |
| --- | --- | --- |
| `src/ruocun/client/responses.py` | **MM-441** | 新增：`usesResponses` 路由判据、`inputMessages` 消息转换、`buildResponsesRequest` 请求体、`responsesUsage`/`responsesMessage` 归一化、`ResponsesToChat`/`iterChatFrames` 统一事件回传、`ResponsesStreamError`、`RESPONSES_ENDPOINT` |
| `src/ruocun/client/types.py` | **MM-444** | **本票未改**：04 已建立的宽松 `dict[str, Any]` 映射（`ChatMessage`/`Usage`/`StreamChatOptions`/`StreamDelta`）已能承载 `responseItems`/reasoning items/工具调用，不重定义公共类型契约 |
| `src/ruocun/client/client.py` | MM-439（04 已实现） | 最小改动：导入 `responses`；`buildRequestBody` 增可选 `use_responses=False`；`streamChat` 内部增 Responses 路由分支（URL/请求体/chunks 转换），签名/事件/累积器不变 |
| `src/ruocun/responses_demo.py` | NEW（建议登记） | 新增：可运行产品路径（合成账户配置 + 本地合成 HTTP/SSE 服务 + 注入式 transport 重写端点 + 两轮工具回合 + 请求/事件 golden + 清理回执） |
| `src/ruocun/cli.py` | 04 已实现 | 最小改动：新增 `--responses-demo` 显式分发与 `_responses_demo`；既有分支完全不变 |

**测试**（`tests/`，全部经默认 `python -m pytest` 收集）：`test_responses_route.py`（9）、`test_responses_request.py`（11）、`test_responses_stream.py`（10）、`test_responses_client.py`（8）、`test_responses_path.py`（10），共 **48 条新增**。

**证据原始产物**：`raw/demo-output.json`（手动演示完整结构化报告）、`raw/demo-command.json`（run.py 回执）。命令原始输出在忽略目录 `.cache/boot/raw/<label>/{stdout,stderr,command.json}.bin`，未提交；关键结果登记于本文。

## 3. 可实际运行的产品路径

显式入口（任务票允许「扩展一次性 prompt 路径」，与 04 的 `--chat-demo` 同构）：

```
python -m ruocun --responses-demo <合成配置目录> [--model <id>] [prompt...]
```

- 读取**仅显式传入**的合成配置目录：`config.json`（原生 profiles，provider=openai / baseUrl=`https://api.openai.com/v1` / model=`gpt-6.1-sol` / 内联合成 key）、`compatibility.json`（可选只读）、`.env`（cwd 简化方言：`RUOCUN_MAX_OUTPUT_TOKENS=50000`、`RUOCUN_REASONING_EFFORT=none`）。凭据只来自合成 profile 的内联 key（合成内存 keychain），缺 key / 坏 JSON / 缺目录明确失败，不靠通用环境变量挑账户。
- **路由判据成立**：`usesResponses("https://api.openai.com/v1","gpt-6.1-sol")==True`（冻结 `responses.ts:5-7`）。配置不命中判据（如 `--model gpt-5` 或非官方 baseUrl）时**明确失败 exit 71**，不静默用 Chat 冒充 Responses 演示（R-06）。
- 启动**本次拥有的本地 loopback 合成 HTTP/SSE 服务**（`127.0.0.1` 随机端口，按 17 字节分块写 Responses SSE 帧，制造中文/emoji 跨字节分片）；注入式 `Transport` 把官方端点 URL 重写到本地服务 `/responses`（**真实 HTTP POST，不访问公网、不调用真实模型**）。两轮 `streamChat` 复现冻结 `responses.test.ts:30-62`：第一轮返回 reasoning item + function_call（工具参数分两次 delta）、第二轮回灌 assistant（`responseItems`/`tool_calls`）+ tool 结果得到最终回答。
- 输出结构化 JSON：`request_golden`（两轮 Responses 请求体，与服务端捕获 body 逐项核对 `wire_request_validated`）、`responses_events_golden`（服务端原始 Responses 事件序列）、`event_golden`（统一 Chat 事件：deltas/finish_reason/usage/message）、`route_criteria`、`server_captured`、清理回执；**不含 secret**（合成 key 只在本地请求 header）。
- 服务在 `finally` 中 `shutdown()` + `server_close()` + `thread.join(timeout=5)`；报告 `server_closed` / `server_socket_fileno=-1` / `port_not_listening` 三项回执。

手动演示原始输出：`raw/demo-output.json`（label `i05-demo-manual-b`，exit 0，`scan_hit=false`）。解析摘要：

```
status=complete  route=responses  answer=完成
wire_request_validated=true  server_closed=true  server_socket_fileno=-1  port_not_listening=true
route_criteria={base_url:https://api.openai.com/v1, model:gpt-6.1-sol, uses_responses:true,
                endpoint:https://api.openai.com/v1/responses}
local_endpoint=http://127.0.0.1:<随机端口>/responses（仅本地）
request_golden[0]: store=false  include=["reasoning.encrypted_content"]
                   reasoning.effort=low（none+6.1-sol 映射）  max_output_tokens=50000（dotenv）
                   tools=[{type:function,name:Read,strict:false,...}]  input[1].content[1]=input_image
request_golden[1].input[2:]=[reasoning, function_call, function_call_output]（冻结 :57-59）
event_golden[0]: finish_reason=tool_calls  prompt_cache_hit_tokens=80  prompt_cache_miss_tokens=20
                 tool_calls=[call_1/Read/{"path":"中文.ts"}]  responseItems=[rs_1]
event_golden[1]: deltas=[{kind:content,text:完成}]（只 1 个，不重复补发）
SECRET_IN_OUTPUT=False
```

## 4. TDD 逐条 red → 最小实现 → green

所有测试/构建进程经 `tools/run.py` 逐条从白名单环境启动（清空父环境、合成 HOME/AppData/TEMP、`-I -X utf8`、禁用 pip 用户配置与 pytest 插件自动加载、每次 `--label` 唯一、`scan_hit=false`）。命令统一形式：
`bootPy -I -X utf8 tools/run.py --label <label> -- devPy -I -X utf8 -m <pytest|ruff|mypy> ...`（安装/构建另带 `--wheelhouse .cache/wheels`）。
预期独立来源：冻结 `responses.ts`/`responses.test.ts` 实际行为与断言/fixture + 已确认规格/ADR；按 S/D/R 改写 TS 断言，**无「断言当前实现输出」的自证测试，未用 Python 输出回填期望**。

| 组 | seam / 案例族 | red（label → 输入 → 预期 → 实际 → 退出码） | 最小实现 | green（label → 实际 → 退出码） + 收口 |
| --- | --- | --- | --- | --- |
| 1 | 路由判据 + 消息转换（WIRE-04） | `i05-red-01`：`pytest -q tests/test_responses_route.py`；输入=冻结 `responses.ts:5-32` + `responses.test.ts:41-59/87-96/63-75` 断言与 fixture；预期=官方 gpt-6 三档/尾部斜杠/大小写命中、网关与 gpt-5/gpt-6x 不命中、tool→function_call_output、assistant reasoning/function_call、图片 input_image/input_text、内部字段不泄漏；实际=`ImportError: cannot import name 'responses'`；**exit 2** | 新增 `responses.py`：`usesResponses` + `inputMessages` + `_GPT6` 正则；`i05-install-g1` 重装 | `i05-green-01`：**9 passed**；**exit 0**。`i05-ruff-01` 0、`i05-mypy-01` 0 |
| 2 | 请求体 + usage/message 构造 | `i05-red-02`：`pytest -q tests/test_responses_request.py`；输入=冻结 `responses.ts:34-65` + `responses.test.ts:48-50/63-75/10-13/54/51`；预期=store/include/effort 映射/128000 cap/tools+strict/可选字段/usage 归一化；实际=`AttributeError: buildResponsesRequest`（10 failed / 1 passed）；**exit 1** | 追加 `responsesUsage`/`responsesMessage`/`buildResponsesRequest` 与 `_ASTRA_SOL`/`_MAX_OUTPUT_TOKENS`/`_INCLUDE` | `i05-green-02`：11 passed；`i05-mypy-02` 报 `min` 的 `int|Any|None`（**exit 1**，类型收口）。显式收窄 `int(limit_value)` 后 `i05-install-g2b` → `i05-green-02b` **11 passed**、`i05-ruff-02b` 0、`i05-mypy-02b` 0 |
| 3 | Responses SSE → 统一 Chat 事件回传 | `i05-red-03`：`pytest -q tests/test_responses_stream.py`；输入=冻结 `responses.ts:73-131` + `responses.test.ts:9-20/34-39/98-104`；预期=completed/incomplete/error/failed、text/refusal/reasoning delta、function_call 增量、[DONE]、无完成事件断流、17 字节中文跨字节；实际=`AttributeError: iterChatFrames`（10 failed）；**exit 1** | 追加 `ResponsesToChat`/`iterChatFrames`/`ResponsesStreamError`/`_chatFrame`，复用 04 `SSEStreamParser` | `i05-green-03`：**10 passed**；`i05-ruff-03` 0、`i05-mypy-03` 0（`i05-install-g3`） |
| 4 | `client.streamChat` Responses 集成 / 两轮工具回合 | `i05-red-04`：`pytest -q tests/test_responses_client.py`；输入=冻结 `client.ts:65-66/72-91` + `responses.test.ts:30-62/87-96/98-104`；预期=URL=`/responses`、请求 golden、两轮 input 配对、usage 归一化、网关/gpt-5 仍 Chat、错误/断流明确失败；实际=URL 仍 `…/chat/completions`（5 failed / 3 passed）；**exit 1** | `client.py` 最小改动：导入 `responses`、`buildRequestBody(use_responses=)`、`streamChat` 路由分支（签名/事件/累积器不变） | `i05-green-04`：**8 passed**；`i05-ruff-04` 0、`i05-mypy-04` 0（`i05-install-g4`） |
| 5 | 可运行产品路径 + 失败边界 + 回归 | `i05-red-05`：`pytest -q tests/test_responses_path.py`；输入=真实 `-m ruocun --responses-demo <合成配置>` 子进程 + 冻结 fixture/断言；预期=完整两轮路径 + 请求/事件 golden + 清理回执 + 既有行为不变；实际=`--responses-demo` 仍走 69「Agent 运行路径尚未实现」（8 failed / 2 passed）；**exit 1** | 新增 `responses_demo.py`（本地合成服务 + 注入 transport + 两轮回合 + golden），`cli.py` 加 `--responses-demo` | 首轮 `i05-green-05`：2 failed（端点重写得到 `/v1/responses`，与本地 `/responses` 不符，**exit 1**）；修正为固定本地路径 + 显式 URL 校验后 `i05-install-g5b` → `i05-green-05b` **10 passed**、`i05-ruff-05b` 0、`i05-mypy-05b` 0；端口回执补强 `i05-install-g5c` → `i05-green-05c` **10 passed**、`i05-ruff-05c` 0、`i05-mypy-05c` 0 |

环境/基线 label：`i05-setup-venv`、`i05-install-tools`、`i05-install-product`、`i05-install-support`、`i05-base-pytest/offline/ruff/mypy/build`；手动演示 label：`i05-demo-manual`（初版）、`i05-demo-manual-b`（含端口回执）。所有 run.py 子进程 `scan_hit=false`、`command_joined=true`。

## 5. 回归（合入前基线 / 合入后全量）

`git merge --no-edit integration/ruocun-migration` → **`Already up to date.`（exit 0，无冲突，HEAD 仍为起点 `bbf4aa9`；集成分支 tip 与起点相同、无新增提交，如实记录）**。

| 入口 | 起点基线（label） | 合入后全量（label） | 结果 | 退出码 |
| --- | --- | --- | --- | --- |
| `python -m pytest` | `i05-base-pytest`：208 passed / 3 deselected | `i05-postmerge-pytest` | **256 passed / 3 deselected**（208 + 48 新增） | 0 |
| `python -m ruff check .` | `i05-base-ruff`：All checks passed | `i05-postmerge-ruff` | All checks passed | 0 |
| `python -m mypy` | `i05-base-mypy`：Success（28 files） | `i05-postmerge-mypy` | Success（30 files，+responses.py/+responses_demo.py） | 0 |
| `python -m ruocun_acceptance offline` | `i05-base-offline`：4 case passed | `i05-postmerge-offline` | 4 case 全 passed，整体 passed | 0 |
| `python -m build`（`--wheelhouse`） | `i05-base-build`：sdist+wheel | `i05-postmerge-build` | sdist+wheel | 0 |
| 手动产品演示 | — | `i05-demo-manual-b` | complete + answer + golden + 三项清理回执 | 0 |

任务 03/04 既有行为逐项回归（`test_responses_path.py::test_existing_version_help_agent_and_chat_demo_preserved` 与全量 208 基线）：`--version`（`RuoCun v0.1.0.dev0\n`）、`--help`、包资源、普通 prompt **exit 69**、`--chat-demo` 首轮流式路径（`answer=你好，世界 😀`）全部保持。

## 6. 覆盖的 WIRE-04 子案例与 red/green 结果

| WIRE-04 子案例 | 测试文件 | red | green |
| --- | --- | --- | --- |
| 路由判据：官方 v1 + gpt-6 三档 / 尾部斜杠 / 大小写命中；自定义网关、gpt-5、gpt-6x、gpt-60、非官方 baseUrl 保持 Chat Completions（不推定原生另一套 provider 协议） | `test_responses_route.py`, `test_responses_client.py`, `test_responses_path.py` | exit 2 / 1 | 9+8+10 passed |
| store=false、include=`["reasoning.encrypted_content"]`、端点 `https://api.openai.com/v1/responses` | `test_responses_request.py`, `test_responses_client.py`, `test_responses_path.py` | exit 1 | 11+8+10 passed |
| effort 映射：reasoning_effort 优先、thinking disabled→low、默认 medium、minimal→low、none+astra/6.1-sol→low、none+luna→none、`&&` 优先于 `\|\|` 的真实运算顺序 | `test_responses_request.py` | exit 1 | 11 passed |
| max_output_tokens：`min(max_completion_tokens ?? max_tokens, 128000)`、256000 经 cap、dotenv 50000、无 `max_tokens`/`messages` Chat 专有字段 | `test_responses_request.py`, `test_responses_client.py`, `test_responses_path.py` | exit 1 | 11+8+10 passed |
| tools 展开 `{type:function, ...function, strict:false}`；parallel_tool_calls/tool_choice/service_tier 仅定义时透传 | `test_responses_request.py`, `test_responses_client.py` | exit 1 | 11+8 passed |
| 消息转换：tool→function_call_output 配对（call_id/output）、assistant reasoning items 携带、assistant null content 不生成 content item、图片 input_image/input_text、内部字段（responseItems/reasoningContent/imageData）不泄漏到最终 wire | `test_responses_route.py`, `test_responses_client.py`, `test_responses_path.py` | exit 2 / 1 | 9+8+10 passed |
| 统一事件回传：completed/incomplete 终止帧（response_items/usage/finish_reason）、error/response.failed→error 帧、output_text/refusal/reasoning delta、function_call arguments 增量（added/done/缺对应调用报错）、[DONE] 跳过、未知事件忽略、无完成事件断流明确抛错 | `test_responses_stream.py`, `test_responses_client.py` | exit 1 | 10+8 passed |
| 结束/错误事件：finish_reason=stop/tool_calls/length、SSE error→`SseError`、非 2xx→`ApiError`、断流不伪成功空回复；ADR-0003 精神不引入自动重放 | `test_responses_stream.py`, `test_responses_client.py` | exit 1 | 10+8 passed |
| usage 归一化：input_tokens→prompt_tokens 等，原生 cache 字段优先、`cached_tokens` 补齐 hit/miss（80/20）；只按有效数据确认 | `test_responses_request.py`, `test_responses_stream.py`, `test_responses_path.py` | exit 1 | 11+10+10 passed |
| 同一对话/工具回合：两轮请求、第二轮 input 携带 reasoning/function_call/function_call_output、回答与 deltas 只 1 个 content | `test_responses_client.py`, `test_responses_path.py` | exit 1 | 8+10 passed |
| 失败/取消边界：坏参数（缺目录/坏 JSON/缺 key/路由不命中）、协议错误、中途断流/取消明确失败或保留部分、不伪报成功 | `test_responses_client.py`, `test_responses_path.py` | exit 1 | 8+10 passed |
| 资源清理：服务关闭/线程/port/socket/端口不监听回执 | `test_responses_path.py` | exit 1 | 10 passed |

**未覆盖 / 未完成（明确 not-run，不伪完成）**：

- 冻结 `responses.test.ts:76-86`「流式失败后复用非流式兜底，仍保留工具调用与推理项」→ 属 client 重试/非流式 fallback（**WIRE-07 / 任务 06**），04 未建立该契约、本票不另起第二套 client 或重放语义（ADR-0003）；**未迁移、not-run**。
- 非流式 Responses 响应（`chat.stream=false`）、`data.status==="failed"` 非流式错误、client 重试层、idle watchdog、429/529/Retry-After、background、max_tokens 续写、费用累计与分模型重启 → 06/07/28 等后续票。
- 冻结 `responses.ts:120` `data.output ?? [...output.values()]` 的 output 回退路径、`response.incomplete` 的 usage/response_items 组合、多并行 function_call 跨 output_index、错误事件各形状（只测 `response.failed`+`response.error` 一种）、`response.output_item.done` 非 function_call 类型的 output 累积 → 实现有对应分支，但**未单独建立独立来源断言**，登记为 WIRE-04 后续子案例。
- WIRE-04 母案例族其余子案例与 WIRE-06/07/08/09/10/11/12、完整 Agent / StoragePort / 三类 epoch / 系统凭据后端（58）→ 后续票；本票按 ADR-0003 不引入自动重放。
- 来源 oracle 全量 215 文件 / 真实 Node 轨迹：本票**未重跑**（02 已验部分驱动）；本票预期来自冻结源码与既有 TS 断言/fixture 静态真值，不冒充 oracle 全量通过。
- 真实 Windows Terminal / 中文 IME / 缩放 / 安装产物 / 其它平台实机 → 最终 77/78/85。

## 7. 请求 / 事件 golden 的独立来源

| golden | 独立来源 | 核对方式 |
| --- | --- | --- |
| 请求 golden（两轮 Responses body） | 冻结 `responses.test.ts:48-50`（store/include/tools）、`:51`（input_image）、`:57-59`（第二轮 input.slice(2)）、`:64-69`（128000/无 max_tokens/effort）；`responses.ts:53-65` 转换逻辑；`client.ts:72-91` wireMessages | 本地合成 HTTP 服务端捕获的真实 POST body 与 `client.streamChat` 的 `request_body` 逐项相等（`wire_request_validated=true`）；测试断言具体字面量 |
| 原始 Responses 事件 golden | 冻结 `responses.test.ts:9-20`（`event:`+`data:` CRLF 帧、17 字节分块、中文跨字节）、`:10-13`（usage fixture）、`:30-39`（两轮事件序列与两次 arguments delta） | 服务端按冻结 fixture 逐事件发送并原样输出为 `responses_events_golden`；测试断言末帧 `response.completed` 与 usage 字面量 |
| 统一 Chat 事件 golden | 冻结 `responses.ts:88-129` 事件分发 + `responses.test.ts:52-54/60-61`（tool_calls/responseItems/usage/仅 1 个 content delta）；04 `ChatAccumulator` 统一事件契约 | 转换后的 deltas/finish_reason/usage/message 与冻结断言字面量比对；未用当前 Python 输出回填期望 |

所有 TS 断言按 S/D/R 改写为 Python；测试里的 fixture（`REASONING`/`CALL`/`ANSWER`/`USAGE`）是冻结 `.test.ts` 字面量的独立复刻，不从产品实现读取。请求/事件 golden 与 `raw/demo-output.json` 可复跑核对。

## 8. 故障归因分类（分列）

- **SOURCE-DEFECT**：无。本票未复现来源故障；冻结 `responses.ts:59` 的 `effort === "minimal" \|\| effort === "none" && /astra\|6\.1-sol/.test(model)` 按 JS 真实优先级（`&&` > `\|\|`）忠实迁移，且冻结 `responses.test.ts:64-69` 断言与此一致，不作为缺陷。
- **PORT-REGRESSION**：无。起点 208 passed / 3 deselected 与 offline 4 case 在合入后全量回归保持通过；`--version`/`--help`/69/`--chat-demo` 逐项复验；新增 48 条在本票路径全绿。组 2 的 mypy 类型报错、组 5 首轮端点路径不符、端口回执补强均为**本票新增实现在 green 阶段的自我修正**（记录在 §4），不影响任何既有行为。
- **INTENTIONAL-DELTA**（均有 ADR/规格/契约依据）：
  1. 新增显式 `--responses-demo` 演示入口（任务票授权「必须有一条可实际运行的产品路径」；用显式标志隔离，既有入口完全不变；失败 exit 71）。
  2. 演示路径用注入式 `Transport` 把官方端点 URL 重写到本次拥有的本地合成服务 `/responses`：路由判据成立而请求不访问公网、不调用真实模型（合成账户配置 + 合成 SSE）。
  3. 不实现 client 重试层 / 非流式 fallback / SSE error 自动重放（04 未建立该契约，归 06/WIRE-07；ADR-0003 精神），错误与未知结果如实报告。
  4. Responses SSE → 标准 Chat SSE 帧的转换复用 04 `SSEStreamParser`（双重分帧，忠实冻结 `responsesFetch` 包装语义），不另起第二套 client 或事件类型。
  5. `buildRequestBody(use_responses=False)` 为兼容扩展（默认行为与 04 完全一致）；`types.py`（MM-444）本票不改，04 宽松映射已足够。
  6. `output_index` 缺失按 0 处理、`max_output_tokens` 非数值防御性兜底 128000：内部契约边界，04 请求体总带上限字段，产品路径不触发。
  7. 冻结 `responses.test.ts:76-86` 非流式兜底断言未迁移（归 06，见 §6）。
  8. 提示词/配置/凭据契约复用 04，未重定义；品牌/环境差异白名单沿用 04 已登记项。
- **ENV**：
  - 主工作区无 `.cache/wheels`，复用 `i03/.cache/wheels` 的 18 包已核验闭包（只读复制，未改锁）。
  - 全量 pytest 可能出现 `.pytest_cache` 目录创建 `WinError 5` 的 `PytestCacheWarning`（不影响结果、exit 0；任务 03 同类环境约束）。
  - Windows 中文空格路径与 `-I -X utf8` 显式设置按 `docs/development.md` 处理。
- **UNVERIFIED**：真实模型调用 **0**；人工体验 HITL 未验（ADR-0004 集中最终 77/78/85）；来源 oracle 全量未重跑；其它平台实机、Windows 全功能/安装产物、完整 Agent/StoragePort 未验。

## 9. 真实模型 / HITL / 分层状态声明

| 层 | 状态 |
| --- | --- |
| 产品自动测试 | **本票 path 已通过**（全量 256 passed / 3 deselected；5 入口全 0；48 条新增逐组 red→green） |
| 来源 oracle | 本票未重跑 Node oracle（02 已验部分驱动）；预期来自冻结源码与既有 TS 断言/fixture 静态真值 |
| 真实模型 | **调用 0 次**（无授权凭据与费用范围；合成账户配置 + 本地合成 HTTP/SSE 服务） |
| 终端体验 / HITL | **未验**，按 ADR-0004 集中最终 77/78/85；本票不请求用户键盘/窗口操作、不代填人工验收 |
| Windows 全功能 / 安装产物 | 后续票；本票 not-run |

## 10. 资源清理回执

- 本地合成 loopback Responses SSE 服务：每个 e2e case 与手动演示均在 `finally` 中 `shutdown()` + `server_close()` + `thread.join(timeout=5)`；报告 `server_closed=true`（线程死亡）、`server_socket_fileno=-1`（监听 socket 关闭）、`port_not_listening=true`（关闭后 `socket.create_connection` 实测拒绝）；随机端口每次演示不同，无监听端口遗留。
- 注入式 transport 只连接 `127.0.0.1` 本次拥有的合成服务；无外部连接、无后台线程/进程遗留。
- 所有测试/构建/演示命令经 `tools/run.py` 以 `subprocess.run(..., capture_output=True)` 同步等待（`command_joined=true`），无游离自有进程；未清理他人 worktree、未清理共享缓存。
- 合成凭据 `sk-synthetic-NOT-A-REAL-KEY`、合成环境值（`RUOCUN_MAX_OUTPUT_TOKENS=50000`、`RUOCUN_REASONING_EFFORT=none`）均为非真实值；所有 run.py `scan_hit=false`；`raw/demo-output.json` 经检查 `SECRET_IN_OUTPUT=False`；未读取真实用户 HOME/AppData/凭据/密钥（白名单 + 合成根）。
- 合成配置目录 `.cache/i05-demo/`、wheel 闭包 `.cache/wheels/`、`.venv/`、`dist/`、`build/`、`.cache/boot/raw/` 均位于忽略目录；offline 套件临时工作区 `.ruocun-acceptance/`（本次自有、纯合成、可重新生成）已在提交前清理；证据只提交 README 与两份 raw JSON。

## 11. 共享 client 契约变更说明（供主代理统筹）

**无破坏性共享契约变更**：`streamChat` 签名、`StreamResult`、`StreamChatOptions`、`StreamDelta`、`Usage`、统一事件类型、请求字段语义、04 的 `buildWireMessages`/`normalizeUsage`/`ChatAccumulator` 全部保持不变。具体兼容扩展：

1. `client.buildRequestBody` 新增可选关键字参数 `use_responses: bool = False`（默认输出与 04 逐字节一致；仅透传给 04 已预留的 `buildWireMessages(use_responses=)`）。
2. `client.streamChat` 内部新增路由分支：仅当 `responses.usesResponses(opts.baseUrl, opts.model)` 为真时，URL 改为 `RESPONSES_ENDPOINT`、请求体改为 `buildResponsesRequest(chat_body)`、`response.chunks` 经 `iterChatFrames` 转换；`StreamResult.request_body` 在该分支返回最终 Responses 请求体（golden 可核对）。04 Chat 分支行为完全不变。
3. `client.streamChat` 引入 `chunks: Iterable[bytes]` 局部变量包装 `response.chunks` —— **提示 06 票（client 重试层）**：重试/非流式兜底需在此之上组织，不要重定义 chunks 消费逻辑或另起第二套 client。
4. 新增 `responses.py` 公开接口：`usesResponses` / `inputMessages` / `buildResponsesRequest` / `responsesUsage` / `responsesMessage` / `ResponsesToChat` / `iterChatFrames` / `ResponsesStreamError` / `RESPONSES_ENDPOINT`。
5. `cli.py` 新增 `--responses-demo` 分发（既有 `--version`/`--help`/`--chat-demo`/69 分支不变）。
6. `types.py`（MM-444）**未改**。

建议主代理登记 NEW 条目：`src/ruocun/responses_demo.py`、5 个 `tests/test_responses_*.py`；MM-441 状态由「未开始」更新为「05 本票路径已实现」，MM-444 保持 04 状态。

## 12. 未改公共文件声明

未修改：`.scratch/ruocun/implementation.md`、`.scratch/ruocun/module-map.md`、`.scratch/ruocun/acceptance-matrix.md`，以及任务票 `05-responses.md` 的 Status/Assignee/Branch/Worktree 字段。对应表、矩阵与任务状态由主协调代理统一维护；新增模块登记请求见 §2、§11。本票未推远程、未建 PR、未清理他人 worktree。
