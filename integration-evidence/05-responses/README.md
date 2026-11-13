# 任务 05 — 独立 merger 复核证据（通过 Responses 路由完成同一对话/工具回合）

- 角色：任务 05 **独立 merger**（未参与实现，独立上下文）。本文件只写**复核者亲自执行**的结论；实现者声称的 `256 passed / 3 deselected` 未经本次亲跑前不采信。
- 唯一工作根目录：`D:/java supplement/Firstcode/RuoCun/.worktrees/wb-m05`
- 分支：`merge/05-responses-verified`
- HEAD（合并提交）：`5e89e7580856f84d9ac93fe53f20a2587f6fe288`
- 候选：`2884cac8802cc349804f768821726026bd7dc294`（实现 worktree `.worktrees/wb-i05` **只读参照，未写入**）
- 集成 tip：`18f945a530eafc616150b247f4bf99a3a2d886a3`
- 冻结来源唯一参照：`.scratch/ruocun-discovery/reference/README.md`（`dao-f17e189-7ac654a0dc06`，源码树 SHA-256 `7ac654a0…`）与只读解包副本 `.worktrees/reference-dao-f17e189-7ac654a0dc06/source/`；重点读 `src/client/responses.ts`、`responses.test.ts`、`client.ts`、`types.ts`、`sse.ts`。活动 DAO 只读，未取其新版本。
- 严格程度参照：仓库根 `integration-evidence/04-chat/README.md` 及 `raw/{boundaries,commands,pytest-command}.json`；04 独立复核的做法（真实故障独立构造、owned 子进程真实 join、独立端口/线程检查、失败原始输出保留、分层如实记录）在本票逐项沿用。
- 未修改产品源码、任务票、`implementation.md`、`module-map.md`、`acceptance-matrix.md`；未推远程、未建 PR、未清理他人 worktree/进程。

> **前序会话产物说明（如实记录）**：本 worktree 已存在一份 `.venv`（含产品与支撑 wheel）与 26 个 `m05-*` run.py label，仓库外也存在 `C:/Users/PC/AppData/Local/Temp/ruocun m05 独立验证/`（含 venv 与边界脚本）。这些是此前两个被频率限制/会话中断打断的复核子代理留下的**未提交、非本复核亲自执行**的产物，本复核**未采信、未使用、未清理**。为保证独立性，本复核在忽略目录内新建 `.cache/m05r2-venv`，全部命令使用全新唯一 `m05r2-*` label，仓库外验证改用全新目录 `C:/Users/PC/AppData/Local/Temp/ruocun m05r2 独立验证/`。

## 1. 起点核对（第一条命令）

```
cd "D:/java supplement/Firstcode/RuoCun/.worktrees/wb-m05" && pwd && git branch --show-current && git rev-parse HEAD && git status --short && git merge-base --is-ancestor 2884cac8802cc349804f768821726026bd7dc294 HEAD; echo ancestor_exit=$?
```

真实输出：

```
/d/java supplement/Firstcode/RuoCun/.worktrees/wb-m05
merge/05-responses-verified
5e89e7580856f84d9ac93fe53f20a2587f6fe288
?? .ruocun-acceptance/
ancestor_exit=0
```

- 路径 / 分支 / HEAD / 候选为 HEAD 祖先（`ancestor_exit=0`）四项均符合；`git status --short` 仅有早前 offline 套件留下的未跟踪 `.ruocun-acceptance/`（用户授权删除后用新输出目录重跑）。
- `git show -s --format="%H%n%P%n%s" HEAD` 真实父节点：`18f945a530eafc616150b247f4bf99a3a2d886a3 2884cac8802cc349804f768821726026bd7dc294`，提交信息 `Merge commit '2884cac…' into merge/05-responses-verified`，确认是双父合并提交、候选完整历史已在 HEAD。
- **未重复 merge**（历史里已有合并提交）。删除残留 `.ruocun-acceptance/` 后 `git status --short` 为空。

## 2. 环境与闭包（亲自搭建）

| 项 | 值 |
| --- | --- |
| 固定解释器 | `C:/Users/PC/AppData/Local/Programs/Python/Python311/python.exe`（CPython 3.11.9，`-I -X utf8`，实跑确认） |
| 公开 wheel 闭包 | 只读复制 `../i03/.cache/wheels` 的 18 个已核验公开 wheel 到本 worktree `.cache/wheels`；**未读实现者私有缓存/日志/真实凭据**，未使用 `wb-i05` 的缓存 |
| 锁一致性 | 独立 `hashlib.sha256` 对 18 个 wheel 逐条比对 `requirements-dev-win311.lock` 的 18 个 `--hash=sha256`，输出 `wheel_count=18 lock_hash_count=18 ALL_MATCH=True` |
| 复核专属 venv | `D:/java supplement/Firstcode/RuoCun/.worktrees/wb-m05/.cache/m05r2-venv`（按锁自建；18 wheel `--require-hashes` 安装，产品 wheel 与 `tests/support` 支撑 wheel `--no-deps` 安装；均 exit 0） |
| 产品 wheel 来源 | `m05r2-install-product` 从**当前 HEAD 源码**构建：`ruocun-0.1.0.dev0-py3-none-any.whl size=84201 sha256=a48a710ccb7a732b486638460cf44fd358b52a64ac5d3b3833f01733623146f2` |
| 所有工程命令 | 逐条经 `tools/run.py` 从明确白名单环境启动：清空父环境、合成 HOME/AppData/TEMP、`-I -X utf8`、`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`、`PIP_CONFIG_FILE=os.devnull`、不设 PYTHONPATH；每次 `--label` 唯一（`m05r2-` 前缀）；回执见 `raw/commands.json` |
| 仓库外验证 venv | `C:/Users/PC/AppData/Local/Temp/ruocun m05r2 独立验证/venv`（中文空格路径，仓库外，只装本票 wheel） |

`raw/commands.json` 汇总 **23** 条 `m05r2-*` 回执：`any_sensitive_match=false`、`any_not_joined=false`，全部 `environment: explicit allowlist; synthetic home/config/temp; no PYTHONPATH`、`command_joined=true`。抽查 `m05r2-install-product/command.json`：argv 仅含解释器绝对路径与 `pip install --no-deps .`，`sensitive_match=false`。

## 3. 五项入口全量复验（亲自执行，逐条 label / 退出码 / 真实结果）

原始输出在 `.cache/boot/raw/<label>/stdout.bin`（忽略目录，不提交）；结果摘自由本人读取的 raw 全文。

| 入口 | label | 退出码 | 真实结果（读 raw stdout.bin） |
| --- | --- | --- | --- |
| `python -m pytest`（默认集） | `m05r2-pytest-full` | 0 | `collected 259 items / 3 deselected / 256 selected`；**`256 passed, 3 deselected in 17.55s`**（pytest 8.4.2 / CPython 3.11.9 / rootdir wb-m05）；新增 5 个 `test_responses_*.py` 共 48 条均在收集内 |
| `python -m ruff check .` | `m05r2-ruff-full` | 0 | `All checks passed!` |
| `python -m mypy` | `m05r2-mypy-full` | 0 | `Success: no issues found in 30 source files`（04 基线 28 + `responses.py` / `responses_demo.py`） |
| `python -m build`（`--wheelhouse .cache/wheels`） | `m05r2-build-final` | 0 | `Successfully built ruocun-0.1.0.dev0.tar.gz and ruocun-0.1.0.dev0-py3-none-any.whl`；`dist/` 实查 wheel 84201 字节、sdist 69470 字节 |
| `python -m ruocun_acceptance offline` | `m05r2-offline-final` | 0 | 4 case 全 `passed`、整体 `passed`、`logical_exit 0`：`ENT-01.version`(0)、`ENT-01.help`(0)、`ENT-01.resource`(0)、`ENT-01.unimplemented`(**exit 69**，`Agent 运行路径尚未实现`)，逐 case 有 owned `subprocess.Popen` / `command_joined` / `streams_closed` 回执 |

安装链 `m05r2-setup-venv` / `m05r2-install-tools` / `m05r2-install-product` / `m05r2-install-support` 全部 exit 0；`m05r2-imports-ok` 原始输出 `IMPORTS_OK …\.cache\m05r2-venv\Lib\site-packages\ruocun\__init__.py RESPONSES_ENDPOINT=https://api.openai.com/v1/responses`。

> 实现者声称 `256 passed / 3 deselected`（208 基线 + 48 新增）：本次由本人亲自跑 `m05r2-pytest-full` 并读 raw 原始输出核实**属实**，不是直接抄写声称值。

## 4. 共享 client 契约无破坏（本票重点）

### 4.1 `git diff bbf4aa9..2884cac -- src/ruocun/client/ src/ruocun/cli.py`

真实 diff 只触及：`cli.py` 新增 `--responses-demo` 分发（既有 `--version`/`--help`/`--chat-demo`/69 分支不变）、`client.py` 6 处（import `responses`；`buildRequestBody` 新增 `use_responses: bool = False` 并在 `messages` 行透传；`streamChat` 新增路由分支与 `chunks: Iterable[bytes]` 局部变量）、新增 `responses.py`。

- **`types.py`（MM-444）未改**：`ChatMessage` / `Usage` / `StreamChatOptions` / `StreamDelta` / `ApiTool` / `ToolCall` 全部沿用 04 宽松映射。
- **`buildWireMessages` 定义未出现在 diff 中**：独立 `git show bbf4aa9:src/ruocun/client/client.py` 确认 04 基线第 71-72 行本就有 `def buildWireMessages(messages, *, use_responses: bool = False)`，且第 90/99 行有 `if use_responses and response_items:`，即**冻结 `client.ts:72-91` 的 `useResponses` 分支是 04 已预留的语义**，05 只是让 `buildRequestBody` 把路由判据透传进去。共享契约未重定义。
- `Iterable` 由 `client.py:22 from collections.abc import Callable, Iterable, Mapping` 提供（04 基线已有，diff 未改）。
- `streamChat` 签名、`StreamResult`、`StreamChatOptions`、`StreamDelta`、`Usage`、统一事件类型、04 的 `buildWireMessages` / `normalizeUsage` / `ChatAccumulator` 语义未变。

### 4.2 独立动态对比（复核者自写 `contract.py`，36/36 通过）

`git show bbf4aa9:src/ruocun/client/client.py` 导出为独立基线，脚本把其相对导入改为绝对导入后 `exec` 到独立模块，与当前已安装产品**逐字段对比**：

| 核对 | 结果 |
| --- | --- |
| `inspect.signature(streamChat)` | `(opts, *, transport=None, env=None) -> StreamResult`，未变 |
| `StreamResult` 字段 | `status, deltas, message, usage, finish_reason, request_body`，未变 |
| `StreamChatOptions` 16 个键 | 与 04 一致，未变 |
| `buildRequestBody` / `buildWireMessages` 默认值 | 均为 `use_responses=False` |
| 04 基线 `buildRequestBody` 签名 | **无** `use_responses` 参数（证明 05 为兼容新增） |
| `default_chat_body_identical_to_04_baseline` | `base.buildRequestBody(o) == cur.buildRequestBody(o)` **True**（含 assistant null content→空串、工具轮 `reasoning_content` 带回、`responseItems` 不带入 wire） |
| `use_responses=False` == 默认 | True；`use_responses=True` 才加入 `responseItems`（冻结 `client.ts:80/84`） |
| 默认 Chat golden | `{"model":…, "messages":[…], "stream":true, "stream_options":{"include_usage":true}, "max_completion_tokens":128000}`，与 04 记录 / 冻结 `client.ts:104-120` 一致 |

### 4.3 路由成立 / 不成立时 URL 与请求体（`contract.py` 独立注入 transport）

| 场景 | URL | 请求体 |
| --- | --- | --- |
| 官方 v1 + `gpt-6.1-sol`（成立） | `https://api.openai.com/v1/responses` | `{"model","input","stream","store":false,"include":["reasoning.encrypted_content"],"max_output_tokens":128000,"reasoning":{"effort":"medium"}}`；**无** `messages` / `max_tokens` / `max_completion_tokens` / `stream_options` |
| 自定义网关 `https://gateway.example/v1` + `gpt-6.1-sol` | `https://gateway.example/v1/chat/completions` | Chat 形状（含 `messages` / `stream_options` / `max_completion_tokens`）；`responseItems` 不泄漏 |
| 官方 v1 + `gpt-5` | `https://api.openai.com/v1/chat/completions` | Chat 形状 |
| 尾部斜杠 + 大小写 `https://api.openai.com/v1///` + `GPT-6-LUNA` | 命中 Responses | — |

另核对冻结 `responses.test.ts:30-62` 两轮工具回合 golden（独立 fixture，硬编码，不复用测试代码）：第一轮 URL / `store` / `include` / `tools[0].strict=false` / `input[1].content[1]=input_image` / `reasoning.effort=low` / `tool_calls` / `responseItems` / usage `hit=80,miss=20` / `finish_reason=tool_calls`；第二轮 `input[2:] == [reasoning, function_call, function_call_output]`、`answer=完成`、content deltas 只 1 个。**全部逐项通过**。

`raw/contract.json`：`{"total":36,"passed":36,"failed":[]}`。

## 5. 最终安装产物（仓库外干净 venv，只装本票 wheel）

venv 绝对路径：`C:/Users/PC/AppData/Local/Temp/ruocun m05r2 独立验证/venv`；`pip install --no-index --no-deps <本票 wheel>`（`m05r2-clean-venv` / `m05r2-clean-install` 均 exit 0）。所有验证命令经 `run.py --cwd <仓库外验证根>` 启动（`-I` 隔离、无 PYTHONPATH、不借源码路径、不装支撑包/开发工具）。

| 验证 | label | 退出码 | 真实结果 |
| --- | --- | --- | --- |
| `--version` | `m05r2-clean-version` | 0 | `RuoCun v0.1.0.dev0` |
| `-v` | `m05r2-clean-v` | 0 | `RuoCun v0.1.0.dev0` |
| `--help` | `m05r2-clean-help` | 0 | 帮助资源可读，含 `用法：ruocun [选项] [提示词]`、`--version, -v` |
| `-h` | `m05r2-clean-h` | 0 | 帮助资源可读 |
| 普通一次性 prompt | `m05r2-clean-prompt69` | **69** | stderr `RuoCun：Agent 运行路径尚未实现。`，stdout 空 |
| 包资源 / 来源 / 隔离 | `m05r2-clean-resource` | 0 | `ORIGIN=…\ruocun m05r2 独立验证\venv\Lib\site-packages\ruocun\__init__.py`；`HELP_LEN=187`、`ZH_LEN=13271`、`EN_LEN=38430`、`HELP_HAS_VERSION_FLAG=True`、`NO_SRC_PATH=True`、`NO_DEV_TOOLS=True`、`NO_SUPPORT_PKG=True` |
| 04 `--chat-demo` 端到端 | `m05r2-clean-chat-demo` | 0 | `status=complete`、`answer=你好，世界 😀`、三段流式 deltas、usage 有效，stderr 空 |
| 05 `--responses-demo` 端到端 | `m05r2-clean-responses-demo` | 0 | 结构化 JSON 140885 字节，含两轮请求 golden / 原始 Responses 事件 golden / 统一 Chat 事件 golden / 清理回执；完整输出存 `raw/clean-responses-demo.json` |

`raw/clean-demo-verification.json`（复核者自写 `verify_demo.py`）**28/28 通过**：`status=complete`、`route=responses`、`answer=完成`、`wire_request_validated=true`、`server_closed=true`、`server_socket_fileno=-1`、`port_not_listening=true`；两轮 request/responses-event/event golden 长度均为 2、`server_captured` 两个 path 均 `/responses`；`max_output_tokens=50000`（dotenv）、`reasoning.effort=low`、`input_image`、第二轮 `input[2:]` 冻结值、`finish_reason=tool_calls`、usage `80/20`、第二轮仅 1 个 content delta；`local_endpoint=http://127.0.0.1:60232/responses`、`configured_base_url` 为官方端点但未连公网。

**独立端口探测（不只看产品自报字段）**：对报告 port `60232` 用 `socket.create_connection` 实测 `listening=false`（NOT_LISTENING）。

## 6. 失败 / 取消 / 资源退出边界（独立构造，`boundaries.py`）

`raw/boundaries.json`：`summary={"failures":[],"passed":true}`。复核者自写脚本，不改产品、不放宽测试。

### 6.1 协议与流失败（注入 transport 直接调公开 `client.streamChat`）

| 场景 | 实际结果 |
| --- | --- |
| `response.failed` 事件 | `SseError: SSE error from API: {'message': 'bad request'}`（明确失败） |
| `error` 事件 | `SseError: …{'message': 'boom'}` |
| 无完成事件、EOF 干净结束（只有 `output_text.delta`） | `ResponsesStreamError: Responses stream closed unexpectedly`（忠实冻结 `responses.ts:85`；与 04 Chat 路径 O-1 的语义不同，本票按冻结 Responses 桥明确报错） |
| 空流（0 chunk） | `ResponsesStreamError: Responses stream closed unexpectedly` |
| `function_call_arguments.delta` 缺对应调用 | `ResponsesStreamError: Responses 工具参数缺少对应调用` |
| `output_item.done` 后 EOF | `ResponsesStreamError: Responses stream closed unexpectedly` |
| 坏 JSON 事件 | `JSONDecodeError`（明确失败，不静默跳过） |
| 非 2xx(401) | `ApiError: API error 401` |
| `response.incomplete` | `status=complete`、`finish_reason=length`（明确，不伪成功） |
| 中途断流 / 取消且尚无产出 | `StreamError: SSE 中途断流且尚无产出` |
| 中途断流 / 取消且已有部分产出 | `status=partial`、`answer=部分`（保留部分、明确标记，**不伪报成功**） |

11 个场景 `fake_success` 全为 `false`。

### 6.2 CLI 坏配置 / 非法参数（真实 `-m ruocun --responses-demo` 子进程，合成配置）

| 场景 | exit | 诊断 | secret 泄漏 | 伪成功 |
| --- | --- | --- | --- | --- |
| 缺配置目录 | 71 | `缺少有效凭据：激活 profile 无内联 key，且未配置可用的合成 keyRef` | false | false |
| `config.json` 坏 JSON | 71 | 同上（坏档案→缺凭据） | false | false |
| 缺 key + 通用环境变量 `OPENAI_API_KEY=sk-env-NOT-REAL-M05R2` | 71 | `缺少有效凭据`（未靠通用变量挑账户） | false | false |
| 路由不命中（`--model gpt-5`） | 71 | `配置未命中 Responses 路由判据：需 https://api.openai.com/v1 + gpt-6 模型` | false | false |
| `--responses-demo` 无参数 | 71 | `--responses-demo 需要合成配置目录。` | false | false |
| `compatibility.json` 坏 JSON | 71 | `CompatibilityError：…compatibility.json: 坏 JSON` | false | false |

6 个场景全部 exit 71、具体文件/字段诊断、`secret_leak=false`、`diag_hit=true`、无伪成功。

### 6.3 资源退出（复核者自己持有服务对象，独立端口/线程检查，不只看产品自报）

真实 `ThreadingHTTPServer` + 真实 `urllib` HTTP POST，`finally` 中 `shutdown()` → `server_close()` → `thread.join(timeout=5)`，之后**独立**用 `socket.create_connection` 探测、`server.socket.fileno()`、`thread.is_alive()`、`threading.enumerate()`：

| 场景 | port | listening_before → after | thread_alive | socket.fileno（关闭后） | owned 线程仍枚举 | 结果 |
| --- | --- | --- | --- | --- | --- | --- |
| 成功路径（真实 HTTP，合法 Responses SSE） | 63461 | true → **false** | false | **-1** | false | `answer=完成` |
| 失败路径（非法 UTF-8 使 `UnicodeDecodeError`） | 63465 | true → **false** | false | **-1** | false | 错误明确，服务仍被关闭 |
| 产品 `run_responses_demo` 成功报告 | 63475 | 独立探测 **NOT_LISTENING**（`independent_port_listening=false`） | — | 自报 -1（另由 6.3 自建服务独立证实 -1） | — | `wire_request_validated=true`、`answer=完成` |

脚本结束 `thread_summary.alive_threads=["MainThread"]`（无遗留线程）。加上 §5 的 clean demo 端口 `60232`，四个端口均经独立探测确认无监听遗留。

## 7. 输入 / 预期独立来源抽查

逐项对照冻结源码与既有 TS 断言（只读解包副本）：

| Python 文件 / 函数 | 对照的独立来源 | 结论 |
| --- | --- | --- |
| `src/ruocun/client/responses.py::usesResponses` | 冻结 `responses.ts:5-7`（`baseUrl.replace(/\/+$/,"")` + `/^gpt-6(?:[.-]|$)/i`）；`responses.test.ts:87-96` 网关反例 | `rstrip("/")` + `_GPT6` 正则忠实；测试 `test_responses_route.py:34-52` 三档/尾部斜杠/大小写命中、gpt-5/gpt-6x/gpt-60/网关不命中来自冻结判据 |
| `responses.py::inputMessages` | 冻结 `responses.ts:11-32`；`responses.test.ts:51/56-59` | tool→`function_call_output`、assistant→reasoning items + content + `function_call`、图片 `input_image`/`input_text`、内部字段不泄漏；期望值硬编码 |
| `responses.py::buildResponsesRequest` | 冻结 `responses.ts:53-65`；`responses.test.ts:48-50/64-69/51` | `store=false`、`include=["reasoning.encrypted_content"]`、`min(max_completion_tokens??max_tokens,128000)`、effort 映射（`effort==="minimal" \|\| effort==="none" && /astra\|6\.1-sol/.test(model)`，JS `&&` 优先于 `\|\|`，Python 忠实写成 `or`/`and`）、tools 展开 `strict:false`、可选字段仅定义时透传；`test_responses_request.py:72-97` 显式覆盖 `&&` 优先、luna→none、minimal→low、thinking disabled→low、默认 medium |
| `responses.py::responsesUsage` + 04 `normalizeUsage` | 冻结 `responses.ts:34-39`、`client.ts:50-55`；`responses.test.ts:10-13` usage fixture 与 `:54` 断言 | `input_tokens`→`prompt_tokens` 等；`input_tokens_details.cached_tokens=80` 经 04 `normalizeUsage` 补齐 `hit=80/miss=20` |
| `responses.py::responsesMessage` | 冻结 `responses.ts:41-49` | text/refusal 拼接、`function_call`→`tool_calls`、reasoning→`responseItems`、空文本 `null` |
| `responses.py::ResponsesToChat` / `iterChatFrames` | 冻结 `responses.ts:73-131`；`responses.test.ts:9-20`（event/data CRLF、17 字节分块、中文跨字节）、`:34-39`（两次 arguments delta）、`:52-54`、`:98-104` | completed/incomplete 终止帧、error/failed→error 帧、各 delta、function_call 增量（缺对应调用报错）、`[DONE]` 跳过、未知事件忽略、flush 无完成事件明确抛错 |
| `client.streamChat` 路由 / `buildWireMessages(use_responses=)` | 冻结 `client.ts:65-66/72-91` | 官方 GPT-6 走 Responses、自定义网关/其它模型保持 Chat；`responseItems` 仅在 `useResponses` 时带回 |
| `tests/test_responses_*.py` 的 `REASONING`/`CALL`/`ANSWER`/`USAGE`/`_TOOLS` | 冻结 `responses.test.ts:6-13/45-46` 字面量 | 独立复刻、硬编码，**不是**从 Python 当前实现输出回填 |

**总体**：路由判据、store/include、effort 映射、`function_call`/`function_call_output` 配对、reasoning items、usage 归一化、请求/事件 golden 的预期均来自冻结 `responses.ts`/`responses.test.ts` 的断言与 fixture 及已确认规格（R-06/R-07、ADR-0003/0004/0005），**未发现"从 Python 当前实现输出回填期望值"的自证断言**。

**如实记录的弱 / 自证断言（与 04 复核 O-2 同类，交主代理/后续票加强，不阻断本票路径结论，本复核不私改产品、不放宽测试）**：

1. `tests/test_responses_client.py:120`：`assert captured[0]["body"] == result.request_body` —— 同一 `body` 对象经 `json.dumps`→`json.loads` 后的两次自比较（恒真），不构成独立请求 golden 校验；与 04 O-2 的 `test_client_wire.py:309` 同类。
2. `tests/test_responses_path.py:107-113`：`wire_request_validated` / `server_closed` / `server_socket_fileno` / `port_not_listening` 全是**产品自报字段**的 `is True` / `== -1` 断言，测试自身无独立端口/线程检查（04 O-2 已指出 `wire_request_validated` 属产品自报）。本复核已用 `boundaries.py`（自建服务独立 `socket.create_connection` / `fileno()` / 线程枚举）与 `verify_demo.py`（独立端口探测）补强，不依赖这些断言。
3. `tests/test_responses_path.py:237`：`chat_report["answer"] == "你好，世界 😀"` 的值来自产品内合成夹具 `src/ruocun/chat_demo.py:36-44` 的 `_SYNTHETIC_FRAMES`，属端到端演示合成数据，非冻结来源/TS 断言的独立 oracle；值在测试中硬编码，非运行时从产品输出回填（与 04 O-2 的 `test_chat_path.py:74/87` 同类）。
4. `tests/test_responses_path.py:183-214`：6 个失败边界测试只断言 `returncode != 0` 与模糊 stderr 关键词（"失败"/"缺少"/"判据"），未校验具体退出码 71、具体诊断、secret 泄漏、无伪成功。本复核 `boundaries.py` 的 6 个 CLI 场景已独立构造并逐项核实 exit 71 / 诊断 / 无泄漏 / 无伪成功。
5. `tests/test_responses_request.py:158`、`:166`：`assert client.normalizeUsage(out) == out` / `== native` —— 以产品自身函数输出为断言对象的结构自洽检查，独立 oracle 强度有限；但期望为硬编码常量，非输出回填。
6. `tests/test_responses_stream.py:107`：`assert any("tool_calls" in … for f in frames)` —— 仅检查存在性，弱断言（非恒真）。

**实现者与冻结来源的已登记差异（非缺陷，实现者证据 §8 亦登记）**：`responses.test.ts:76-86` 非流式兜底归 06（本票 not-run，不引入自动重放）；`responses.ts:120` 的 `data.output ?? [...output.values()]` 回退、`response.incomplete` 的 usage/response_items 组合、多并行 function_call 跨 `output_index`、非 function_call 的 `output_item.done` 累积等分支实现有对应代码但未单独建立独立来源断言，登记为 WIRE-04 后续子案例。

## 8. 任务 03/04 既有行为回归（逐项复验）

| 行为 | 复验位置 | 实际结果 |
| --- | --- | --- |
| `--version` / `-v` | `m05r2-clean-version` / `m05r2-clean-v`；`m05r2-offline-final` ENT-01.version | `RuoCun v0.1.0.dev0`，exit 0，stderr 空 |
| `--help` / `-h` | `m05r2-clean-help` / `m05r2-clean-h`；offline ENT-01.help | 帮助资源可读，exit 0 |
| 包资源 | `m05r2-clean-resource`；offline ENT-01.resource | `help.zh-CN.txt`(187)、`system_prompt.zh.txt`(13271)、`system_prompt.en.txt`(38430) 随 wheel 可读，ORIGIN 在仓库外 site-packages |
| 普通一次性 prompt | `m05r2-clean-prompt69`；offline ENT-01.unimplemented | exit **69**，stderr `RuoCun：Agent 运行路径尚未实现。` |
| `--chat-demo` 首轮流式路径 | `m05r2-clean-chat-demo`；`test_responses_path.py::test_existing_version_help_agent_and_chat_demo_preserved`（在 256 passed 内） | `status=complete`、`answer=你好，世界 😀`、三段 deltas，未被破坏 |
| `ruocun_acceptance offline` 4 case | `m05r2-offline-final` | 4 case 逐项全 passed（其余 6 suite 仍 not-run，未改驱动） |

03/04 行为无回归。默认 Chat 请求体与 04 基线逐字段一致（§4.2）。

## 9. 环境白名单与脱敏

- 23 条 `m05r2-*` 命令全部经 `tools/run.py` 逐条启动，label 唯一；`raw/commands.json` 汇总 `any_sensitive_match=false`、`any_not_joined=false`，所有回执 `environment: explicit allowlist; synthetic home/config/temp; no PYTHONPATH`、`command_joined=true`。
- argv 仅含解释器绝对路径与模块/脚本参数；抽查 `m05r2-install-product/command.json` 无真实 HOME/凭据；仓库外验证命令 `--cwd` 为仓库外中文空格路径，不借源码路径。
- `raw/demo-output.json`（实现者证据，140904 字节）全量 secret 扫描：`sk-[A-Za-z0-9_-]{6,}`、`Bearer `、`Authorization`、`api_key`、`SECRET`、`PASSWORD`、`TOKEN` **全部 0 命中**（`raw/clean-demo-verification.json`）。
- 复核者自己生成的 `raw/clean-responses-demo.json`（140885 字节）同样 **全部 0 命中**。
- 合成值仅：`sk-synthetic-NOT-A-REAL-KEY`、`sk-env-NOT-REAL-M05R2`、`RUOCUN_MAX_OUTPUT_TOKENS=50000`、`RUOCUN_REASONING_EFFORT=none`、本地 `127.0.0.1` 随机端口；未读取真实用户 HOME/AppData/凭据/密钥，未读实现者私有缓存/日志。

## 10. 分层状态与未验项（分别记录）

| 层 | 状态 |
| --- | --- |
| 产品自动测试 | **本票路径已亲自通过**：五项入口全 exit 0（pytest 256 passed/3 deselected、ruff、mypy 30 files、build、offline 4 case）；仓库外 wheel-only 安装产物验证通过；共享契约 36/36、demo 结构化 28/28、失败/取消/资源退出边界独立构造全部通过。不扩为母案例族或全量规格通过 |
| 来源 oracle | **not-run**：本票未重跑 Node oracle / 全量 215 来源文件（02 已验部分驱动，不冒充本票通过）；预期真值来自冻结 `responses.ts`/`responses.test.ts`/`client.ts`/`types.ts` 与既有 TS 断言/fixture 的静态对照 + 已确认规格/ADR |
| 真实模型 | **0 次**（合成账户配置 + 本地 `127.0.0.1` 合成 HTTP/SSE 服务，无授权凭据与费用范围，未访问公网、未调用真实模型） |
| 终端体验 / HITL | **not-run**：按 ADR-0004 集中最终 77/78/85；未请求用户键盘/窗口操作、未代填人工验收 |
| Windows 全功能 / 安装产物 | **部分执行**：仅覆盖仓库外中文空格路径干净 venv 只装产品 wheel 的 CLI 子集（版本/帮助/资源/exit 69/`--chat-demo`/`--responses-demo` 端到端）；onedir/onefile 独立产物、升级/卸载、真实 Windows Terminal、中文 IME/连续缩放、WT-01..09、系统凭据后端(58)、IPC/ACL/Job/OS 沙箱均为 **not-run** |
| 其它平台实机 | **not-run**（Linux/macOS 保留设计，未实机验收） |
| 完整 Agent / StoragePort / 会话恢复 / 六 suite 其余 | **not-run**（后续票；普通 prompt 仍 exit 69） |

**本票路径未覆盖 / 未验（不伪完成）**：WIRE-04 母案例族其余子案例（非流式兜底 `responses.test.ts:76-86` 归 06；client 重试/idle watchdog/429/529/background 归 06/07；`responses.ts:120` output 回退、多并行 function_call 跨 `output_index`、非 function_call 的 `output_item.done` 累积、错误事件各形状等未单独建独立来源断言）、WIRE-06..12、完整 Agent/StoragePort/三类 epoch、真实模型、终端/HITL、其它平台、Windows 全功能与独立发布产物。母案例族与全量规格不因本票标通过。

## 11. 发现的问题清单

**无阻断缺陷**（五项入口、共享契约、安装产物、失败/取消/资源退出边界、独立来源抽查、03/04 回归、白名单脱敏均亲自复验通过）。如实记录以下观察项，交主代理/实现者判断，本复核不私改产品、不放宽测试：

- **O-1（弱/自证断言，非回归）**：见 §7 六条（`test_responses_client.py:120`、`test_responses_path.py:107-113/183-214/237`、`test_responses_request.py:158/166`、`test_responses_stream.py:107`）。均为"以产品自身输出/常量/自报字段为断言对象"的结构性自证、演示合成夹具或存在性弱断言，独立 oracle 强度有限，但**不是**从 Python 当前实现输出回填期望值。建议后续补独立 oracle 时加强；本复核已用独立脚本（`contract.py` / `verify_demo.py` / `boundaries.py`）另行补强，不依赖这些断言。
- **O-2（失败边界测试粒度，非缺陷）**：产品自带 `test_responses_path.py` 的失败边界只断言非零退出与模糊关键词；本复核 `boundaries.py` 已独立构造 6 类配置失败并核实 exit 71 / 具体诊断 / 无 secret 泄漏 / 无伪成功，结论不受影响。
- **OBS（前序会话残留，非产品缺陷）**：本 worktree 的 `.venv` / `m05-*` label、仓库外 `ruocun m05 独立验证/`、未跟踪 `.ruocun-acceptance/` 均为早前被打断的子代理/会话产物。本复核未采信、未使用、未清理他人资源；`.ruocun-acceptance/` 按用户授权删除后以新输出目录重跑 offline。所有自有命令使用 `m05r2-` 前缀与独立 venv/目录。
- **ENV（非缺陷）**：主工作区无 `.cache/wheels`，复用 `i03/.cache/wheels` 的 18 包已核验公开闭包（只读复制、未改锁）；Windows 中文空格路径与 `-I -X utf8` 按 `docs/development.md` 处理。

## 12. 自有进程 / venv / 临时资源清理

- 本 worktree 自建 `.cache/m05r2-venv/`、`.cache/wheels/`、`.cache/boot/raw/`、`dist/`、`build/`、`.pytest_cache/`、`.cache/m05r2-baseline-client.py` 均在 `.gitignore` 忽略目录内，保留（不提交、不清理他人资源）。
- 仓库外验证 venv 绝对路径 `C:/Users/PC/AppData/Local/Temp/ruocun m05r2 独立验证/venv`，**收尾由复核者删除该自建目录树**（含 `venv/`、`respcfg/`、`chatcfg/`、`m05r2_resource_check.py`）；该目录在仓库外、非他人 worktree、非共享缓存。
- 本复核启动的本地 loopback 服务端口：自建服务 `63461`(成功) / `63465`(失败)、产品 `run_responses_demo` `63475`、clean venv CLI demo `60232`；四者均 `shutdown()`+`server_close()`+`thread.join()`，独立端口探测确认 NOT_LISTENING，线程枚举只剩 `MainThread`，无自有遗留进程/线程。
- 所有 `run.py` 子进程 `command_joined=true`（同步等待），边界脚本内 `subprocess.run` 全部同步 join；未清理/未杀其它 worktree/会话的进程。
- 未跟踪 `.ruocun-acceptance/`（offline 临时产物）在提交前删除，`git status --short` 为空。

## 13. 结论与建议

- merge 状态（双父合并提交、候选完整历史在 HEAD、`ancestor_exit=0`）与干净工作区核对通过；**未重复 merge**。
- 五项入口、共享 client 契约无破坏（含与 04 基线逐字段对比）、仓库外 wheel-only 安装产物、失败/取消/资源退出边界、独立来源真实性抽查、03/04 回归、白名单脱敏均**亲自复验通过**，无阻断缺陷。
- 建议主代理按**本票路径范围**接收 / 集成；O-1/O-2 弱断言建议后续补独立 oracle 时加强，本复核不私改产品、不放宽测试。
- 母案例族 WIRE-04 与全量规格不因本票标全量通过；来源 oracle not-run、真实模型 0 次、终端/HITL not-run（ADR-0004 → 最终 77/78/85）、Windows 全功能/安装产物仅按 §10 实际范围执行、其它平台 not-run。

---

## 附：本复核提交的证据文件

| 文件 | 内容 |
| --- | --- |
| `README.md` | 本文件 |
| `contract.py` | 共享契约 / 04 基线动态对比 / 路由 URL 与请求体 / 冻结两轮 golden 独立脚本 |
| `verify_demo.py` | clean demo 结构化结果、独立端口探测、secret 扫描独立脚本 |
| `boundaries.py` | 失败 / 取消 / 资源退出边界独立构造脚本 |
| `raw/contract.json` | 36/36 契约核对原始结果 |
| `raw/clean-demo-verification.json` | 28/28 demo 结构化核实与 secret 扫描 |
| `raw/boundaries.json` | 11 流场景 + 6 CLI 场景 + 3 资源场景原始结果 |
| `raw/clean-responses-demo.json` | 复核者亲自生成、仓库外 wheel-only venv 的 `--responses-demo` 完整结构化输出 |
| `raw/commands.json` | 23 条 `m05r2-*` run.py 白名单回执汇总 |
