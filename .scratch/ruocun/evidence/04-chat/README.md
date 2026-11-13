# 任务 04 — 用兼容账户配置完成首轮流式对话 · 实现与验证证据

- 分支：`impl/04-chat`；worktree：`.worktrees/wb-i04`（本票唯一工作根目录）
- 起点（已提交集成 tip）：`19b3c01eb2738937cdf3c8e3b17ae37f8b3e62de`
- 证据绝对路径：`D:/java supplement/Firstcode/RuoCun/.worktrees/wb-i04/.scratch/ruocun/evidence/04-chat/`
- 状态：本票路径已实现并通过自动验证；**母案例族未标全量通过**（按票「本票完成不表示整族或全量规格通过」）。

## 1. 环境与基准

| 项 | 值 |
| --- | --- |
| OS | Windows-10-10.0.26200-SP0（Windows 11 build 26200），AMD64 |
| Python | CPython 3.11.9（`-I -X utf8`） |
| 开发依赖 | `requirements-dev-win311.lock`（20 行，18 包固定闭包，wheel 逐 `--require-hashes` 校验）；主工作区无 `.cache/wheels`，复用 `i03/.cache/wheels` 的 18 个已核验公开 wheel（只读复制到本 worktree `.cache/wheels`，未改锁文件） |
| 工具 pin | Hatchling 1.33.0 / build 1.6.1 / pytest 8.4.2 / Ruff 0.17.3 / mypy 2.4.1 |
| 唯一冻结来源 | `dao-f17e189-7ac654a0dc06`，源码树 SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`（805 成员，02 已校验）；解包只读副本 `.worktrees/reference-dao-f17e189-7ac654a0dc06/source/` |
| 本票读取的冻结源码 | `src/config/{profiles,profiles_store,credential,env_file,model_selection,migrate_dirs,keychain}.ts` 及同名 `.test.ts`、`src/client/{client,sse,types}.ts` 及 `.test.ts`、`src/prompt/system_prompt.ts(.test.ts)`、`src/env_snapshot.ts`、`src/index.ts` 账户/环境/模型路由片段 |
| 提示词资源来源 | `system_prompt.ts` SHA-256 `44a78c41b4681ee89ea9e2133b49d086b41eb00da08690e765d04ed4dc1d6753`；提取为 `system_prompt.zh.txt`(333 行)/`system_prompt.en.txt`(344 行)，MIT 来源标注见 `system_prompt.py` 文档 |
| 契约来源 | `.scratch/ruocun-discovery/research/09-storage-extension-route.md`（StoragePort v1 / 三类 epoch / 原生路径、兼容 source map 与写回 / 环境别名与凭据范围）、`08-python-runtime-route.md`、ADR-0003/0004/0005、规格 R-05/R-06/R-07/R-12 |

> 本票**不实现** StoragePort / 会话持久化 / recovery，未发明第二套 schema 或 epoch 契约；未修改活动 DAO 目录（只读参照）。

## 2. 交付物与对应表登记请求

按对应表 MM-455/457/460/462/464/466/439/443/444/566/475 落地的模块：

| 模块 | MM | 职责 |
| --- | --- | --- |
| `src/ruocun/config/profiles.py` | 464 | 冻结 6 provider 目录、DEFAULTS、MODELS_BY_PROVIDER、supportsVision/contextWindowFor/outputLimitFor、migrateConfig、resolveActive |
| `src/ruocun/config/profiles_store.py` | 466 | loadProfiles/saveProfiles、增删改切换、整份选择、原生写回 |
| `src/ruocun/config/credential.py` | 455 | resolveCredential/persistKey、合成 KeychainPort、provenance、状态区分 |
| `src/ruocun/config/env_file.py` | 457 | parseDotenv/loadDotenv/applyDotenv 简化方言 |
| `src/ruocun/config/model_selection.py` | 462 | getAgentModel/defaultAuxiliaryModel |
| `src/ruocun/config/migrate_dirs.py` | 460 | migrateLegacyDir 纯函数（产品不自动调用接管旧目录） |
| `src/ruocun/client/client.py` | 439 | 请求组装、SSE 累积器、streamChat、注入式/真实 HTTP transport |
| `src/ruocun/client/sse.py` | 443 | parseSSEChunk + 增量 UTF-8 严格解码 SSEStreamParser |
| `src/ruocun/client/types.py` | 444 | Chat 协议类型（宽松映射保留来源宽容边界） |
| `src/ruocun/prompt/system_prompt.py` | 566 | buildSystemPrompt + 品牌/环境差异白名单 |
| `src/ruocun/env_snapshot.py` | 475 | formatEnvSnapshot/redactProxyCredentials/probeTopLevelDir/formatFastEnvFields/wrapDelayedEnvNotice |

**新增文件（请主代理登记对应表，本代理未改对应表/矩阵/任务票字段）**：

- `src/ruocun/config/compat.py`：D09 唯一兼容契约的 `compatibility.json` source map 解析 + RUOCUN_/DAO_ 环境别名与逐变量谓词（建议 NEW 条目）。
- `src/ruocun/chat_demo.py`：一次性 prompt 产品路径的组合根（合成配置 + 本地合成 SSE 服务，建议 NEW 条目）。
- `tools/extract_prompt.py`：从冻结快照提取提示词文本资源，可复现（建议 NEW 条目）。
- `src/ruocun/prompt/resources/system_prompt.{zh,en}.txt`：冻结提示词文本资源（MIT，内容而**非** TS 源码逻辑；Python 只做占位符/白名单替换）。

**测试**（`tests/`，全部经 `python -m pytest` 默认集合）：`test_config_pure.py`、`test_config_env.py`、`test_config_store.py`、`test_config_credential.py`、`test_client_sse.py`、`test_client_wire.py`、`test_prompt.py`、`test_chat_path.py`。

## 3. 可实际运行的产品路径

显式入口（任务票允许「扩展 cli.py 的一次性 prompt 路径」）：

```
python -m ruocun --chat-demo <合成配置目录> [--model <id>] [prompt...]
```

- 读取**仅显式传入**的合成配置目录：`config.json`（原生 profiles）、`compatibility.json`（可选只读 source map）、`.env`（cwd 简化方言）。
- 凭据只来自合成 profile 的内联 key（经合成内存 keychain，不接系统后端、不读真实密钥）；缺 key 明确失败，不靠 `OPENAI_API_KEY` 等通用环境变量挑账户。
- 组装冻结 system prompt（品牌/环境白名单替换）+ 请求参数（`max_tokens`、`reasoning_effort` extra 覆盖、请求 golden）。
- 启动**本次拥有的本地 loopback 合成 SSE 服务**（`127.0.0.1` 随机端口，按 3 字节分块写，制造中文/emoji 跨字节分片），用真实 `urllib` HTTP POST + 真实增量 UTF-8 严格解码 + SSE 分帧 + 按 index 累积 → 回答。
- 输出结构化 JSON（请求 golden、answer、usage、status、清理回执），**不含 secret**（合成 key 只在本地请求 header）。
- 服务在 `finally` 中 `shutdown()` + `server_close()` + `thread.join()`，`server_closed=true`。

不调用任何真实模型、不访问公网、不读取真实用户配置/凭据/密钥。既有 `--version`/`--help`/包资源/普通 prompt 退出码 69 行为不变（见 §7）。

手动演示原始输出：`raw/demo-output.json`（label `i04-demo-manual`，exit 0）。解析摘要：

```
status=complete  answer=你好，世界 😀  model=deepseek-v4-pro  provider=deepseek
selection=native  wire_request_validated=true  server_closed=true
usage={prompt_tokens:12,completion_tokens:5,total_tokens:17}
max_tokens=50000（dotenv RUOCUN_MAX_OUTPUT_TOKENS + 环境别名）
reasoning_effort=high（RUOCUN_REASONING_EFFORT extra 覆盖）
messages_roles=[system,user]  system_len=13544  secret_in_output=False
```

## 4. TDD 逐条 red → 最小实现 → green

所有测试/构建进程经 `tools/run.py` 逐条从白名单环境启动（清空父环境、合成 HOME/AppData/TEMP、`-I -X utf8`、禁用 pip 用户配置与 pytest 插件自动加载、每次 `--label` 唯一、`scan_hit=false`）。预期独立来源：冻结源码实际行为 + 既有 `.test.ts` 断言/fixture + 已确认规格/ADR；按 S/D/R 改写 TS 断言，**无「断言当前实现输出」的自证测试，未用 Python 输出回填期望**。原始输出在 `.cache/boot/raw/<label>/{stdout,stderr,command.json}.bin`（忽略目录，未提交；关键结果登记于本文与 `raw/summary.json`）。

| 组 | seam / 案例族 | red 命令（label）→ 输入 → 预期 → 实际 → 退出码 | 最小实现后 green（label）→ 实际 → 退出码 |
| --- | --- | --- | --- |
| 1 | config 纯数据层 CFG-01/02/03/05/06 | `i04-red-01`：`pytest -q tests/test_config_pure.py tests/test_config_env.py`；输入=冻结 profiles/model_selection/env_file 断言 + D09 环境别名；预期=模块存在且行为与冻结一致；实际=`ModuleNotFoundError: No module named 'ruocun.config'`；**exit 2** | 实现 `config/{profiles,model_selection,env_file,compat}.py` → `i04-install-01` → `i04-green-01b`：**58 passed**；**exit 0** |
| 1b | mypy strict | `i04-mypy-01`：`mypy`；实际=`dict(raw)` 无法从 `object` 收窄 `call-overload`；**exit 1** | 用 `TypeGuard[ProfilesConfig]` 收窄 → `i04-mypy-01b`：**Success，exit 0** |
| 2 | 存储/凭据层 CFG-01/04/09 | `i04-red-02`：`pytest -q tests/test_config_store.py tests/test_config_credential.py`；预期=整份选择/写回/兼容 source map/凭据状态区分；实际=`ImportError: cannot import name 'migrate_dirs'`；**exit 2** | 实现 `config/{profiles_store,migrate_dirs,credential}.py` → `i04-install-02` → `i04-green-02b`：**43 passed**；**exit 0** |
| 2b | 组2 首轮修正 | `i04-green-02`：2 failed（① `profiles 仅 user` 校验顺序被 workspace 校验抢先；② 测试自身逻辑矛盾：seed 了 secret 却期望 not-found）；**exit 1**。ruff `i04-ruff-02`：2 处（未用 import / import 排序）；**exit 1** | ① 把 `profiles 仅 user` 校验提前（D09:122 真值）；② 修正测试 not-found 用例为空 seed（**测试预期修正，非放宽断言**）；清理 import → `i04-green-02b` 43 passed / `i04-ruff-02b` exit 0 / `i04-mypy-02b` exit 0 |
| 3 | WIRE-03 SSE 层 | `i04-red-03`：`pytest -q tests/test_client_sse.py`；预期=冻结 sse.test.ts 分帧 + 跨字节严格 UTF-8；实际=`ModuleNotFoundError: No module named 'ruocun.client'`；**exit 2** | 实现 `client/{__init__,sse,types}.py` → `i04-install-03` → `i04-green-03`：**14 passed**；`i04-mypy-03`/`i04-ruff-03` exit 0 |
| 4 | WIRE-01/02/03/05 + 提示词 | `i04-red-04`：`pytest -q tests/test_client_wire.py tests/test_prompt.py`；预期=请求保真/参数/累积器/system_prompt.test.ts/env_snapshot 行为；实际=`ModuleNotFoundError`（client/prompt/env_snapshot 缺）；**exit 2** | 提取冻结模板资源（`i04-extract-01` exit 0）+ 实现 `client/client.py`、`prompt/system_prompt.py`、`env_snapshot.py` → `i04-install-04` → `i04-green-04b`：**55 passed**；`i04-mypy-04b`/`i04-ruff-04b` exit 0 |
| 4b | 组4 首轮修正 | `i04-green-04`：1 failed（Windows 禁止文件名含换行符，真实创建控制字符文件 `PermissionError`）；**exit 1**。ruff `i04-ruff-04`：2 处未用 import；**exit 1** | 用 `monkeypatch` 在**文件系统系统边界**注入合成条目（mocking.md 允许）；清理 import → `i04-green-04b` 55 passed / `i04-ruff-04b` exit 0 |
| 5 | 端到端产品路径 + 既有行为回归 | `i04-red-05`：`pytest -q tests/test_chat_path.py`；输入=`-m ruocun --chat-demo <合成配置>`；预期=完整路径 status=complete + answer + 请求 golden；实际=7 failed/2 passed，`--chat-demo` 仍走 69「Agent 运行路径尚未实现」；**exit 1** | 实现 `chat_demo.py`（本地合成 loopback 服务）、`cli.py` 扩展、`client.streamChat(env=...)` → `i04-install-05` → `i04-green-05`：**9 passed**；**exit 0** |
| 5b | mypy 收口 | `i04-mypy-05`：`client.StreamChatOptions` 未定义（在 `types.py`）；**exit 1** | 从 `.client.types` 导入 `StreamChatOptions` → `i04-mypy-05b`：**Success（28 files）exit 0** |

## 5. 回归（合入前，本 worktree 隔离环境）

| 入口 | label | 结果 | 退出码 |
| --- | --- | --- | --- |
| `python -m pytest`（默认全量） | `i04-pytest-full` | **208 passed, 3 deselected** | 0 |
| `python -m ruff check .` | `i04-ruff-full` | All checks passed | 0 |
| `python -m mypy` | `i04-mypy-05b` | Success: no issues found in 28 source files | 0 |
| `python -m build`（`--wheelhouse`） | `i04-build-final` | `Successfully built ruocun-0.1.0.dev0.tar.gz and ….whl` | 0 |
| `python -m ruocun_acceptance offline` | `i04-offline-final` | 4 cases 全部 `passed`，整体 `passed` | 0 |
| 手动产品演示 | `i04-demo-manual` | 完整路径 complete + answer + golden + 服务关闭 | 0 |
| 任务03 基线（起点复验） | `i04-baseline-*` | pytest 29 passed/3 deselected、ruff、mypy、offline 全 0 | 0 |

任务03 基线 29 → 本票新增 179（58+43+14+55+9）→ 全量 208。所有 run.py 子进程 `scan_hit=false`，命令均 `command_joined`。

**合入集成分支**：完成前执行 `git merge integration/ruocun-migration` → `Already up to date.`（exit 0，**无冲突**，HEAD 仍为起点 `19b3c01…`；集成分支 tip 与起点相同、无新增提交，如实记录）。merge 后重跑回归：`i04-postmerge-pytest` **208 passed/3 deselected**、`i04-postmerge-ruff` 0、`i04-postmerge-mypy` 0、`i04-postmerge-offline` 0（4 case passed）、`i04-postmerge-build` 0，全部 exit 0、`scan_hit=false`。

## 6. 覆盖的子案例与 red/green 结果

按票「跨票母案例按本票路径展开子 ID，母行不标全量通过」。下表为本票路径**实际覆盖**的子案例：

| 案例族 | 本票覆盖的子案例 | 测试文件 | red | green |
| --- | --- | --- | --- | --- |
| CFG-01 账户格式 | v2 原样/未知顶层字段、旧 `{apiKey}` 迁移、坏 JSON→空档案、增删/切换/同名拒绝、save 保留未知字段、整份选择（原生优先即使坏 JSON）、首次写回原生去旧 apiKey 保留 v2、兼容源零写入 | `test_config_pure.py`,`test_config_store.py` | exit 2 / 2 | 58+43 passed |
| CFG-02 模型目录 | 冻结 ID/endpoint/window/vision/maxOutputTokens、6 provider 默认、渠道窗口区分、outputLimitFor cap、自定义网关不猜便宜档 | `test_config_pure.py` | exit 2 | 58 passed |
| CFG-03 模型继承 | override > agent > parent、inherit 跳过、缺可继承主模型明确报错 | `test_config_pure.py` | exit 2 | 58 passed |
| CFG-04 凭据优先级 | inline 非空优先 keyRef、缺 key 不靠通用环境变量、旧兼容 keyRef 精确只读 `dao-api-key`、新写 `ruocun-api-key`/`ruocun/<profile>`、provenance、not-found/refused/timeout-unconfirmed 区分、fallback 不泄漏秘密、不删旧服务 secret | `test_config_credential.py`,`test_chat_path.py` | exit 2 / 1 | 43+9 passed |
| CFG-05 dotenv | 简化 KEY=VALUE/配对引号/注释、无 export/插值、已有 env（含空串）优先、只 cwd `.env` | `test_config_env.py` | exit 2 | 58 passed |
| CFG-06 环境开关 | RUOCUN_ 优先/DAO_ fallback、空值阻止 fallback、AUTO_APPROVE `"0"` 非空真、TRUST 只 `"1"`、USE_KEYCHAIN `0/off` 关闭、AUTO_APPROVE=0 与 TRUST=0 不混同、Number||default、第三方变量保留原名 | `test_config_env.py` | exit 2 | 58 passed |
| CFG-09 品牌/数据边界 | 默认空 source map、显式只读 source map 校验（坏 JSON/未知 version/重复 id/禁止资源/绝对路径不展开/profiles 唯一）、旧 DAO 目录并存不自动接管/移动/写回、RuoCun 原生根隔离 | `test_config_store.py`,`test_chat_path.py` | exit 2 / 1 | 43+9 passed |
| WIRE-01 请求保真 | 固定 system/messages/tool schema 顺序、角色/字段/空值、extra 覆盖、stream_options、Authorization/URL、品牌替换差异白名单与请求 golden（真实 HTTP 服务端校验 body 一致） | `test_client_wire.py`,`test_prompt.py`,`test_chat_path.py` | exit 2 / 1 | 55+9 passed |
| WIRE-02 输出上限/思考参数 | 128000 默认、256000 特殊空截断重试、模型 cap 裁剪、max_tokens/max_completion_tokens 选择、thinking/reasoning_effort/parallel_tool_calls/tool_choice 仅由 extra、不加未配置 temperature/top_p | `test_client_wire.py` | exit 2 | 55 passed |
| WIRE-03 Chat SSE 分帧 | 增量字节严格 UTF-8（中文/emoji 逐字节与多种块大小分片）、CR/LF、多帧、空行、`[DONE]`、末帧 flush、非法/不完整字节明确报错；文本/reasoning/工具参数按 index 完整累积、空 id 不冲掉真实 id、usage/finish_reason 只按有效数据确认、千帆 usage 归一化 | `test_client_sse.py`,`test_client_wire.py` | exit 2 | 14+55 passed |
| WIRE-05 历史 wire 清洗 | assistant null content→空串、工具轮 reasoning 带回、无工具轮不机械附带、imageData/responseItems 不泄漏到 wire | `test_client_wire.py` | exit 2 | 55 passed |

**未覆盖 / 未完成（明确写 not-run，不伪完成）**：

- 同族其它子案例与 WIRE-04/06/07/08/09/10/11/12（Responses 桥、usage/费用累计与多模型重启、client 重试与非流式 fallback、idle watchdog、loop 错误/限流、空响应/坏工具 JSON、预算轮数、取消迟到事件）→ 任务 05/06/28 等后续票；本票按 ADR-0003 精神**不引入自动重放语义**，SSE error 明确失败，重试/兜底不实现。
- CFG-07/08/10（设置分层、项目指令加载、信任/更新校验）不在本票案例族。
- 完整 Agent 运行路径（工具、会话、权限、恢复、StoragePort/三类 epoch）→ 后续票；普通 prompt 仍 exit 69。
- 系统凭据后端（Windows Credential Manager）→ 任务 58 / D10；本票只用合成内存 keychain 并明确区分状态。
- env_snapshot 的真实运行时探测命令（node/npm → Python/Windows）→ 平台端口后续替换；本票只保留格式化/脱敏/清洗纯函数。
- 来源 oracle 全量 215 文件 / 真实 Node 轨迹：本票**未重跑**（02 已验 6 文件 190 断言）；本票预期来自冻结源码与既有 TS 断言静态真值，不冒充 oracle 全量通过。
- 真实 Windows Terminal / 中文 IME / 缩放 / 安装产物 → 最终 77/78/85。

## 7. 既有行为回归（任务03，不得破坏）

| 行为 | 结果 |
| --- | --- |
| `--version` / `-v` | `RuoCun v0.1.0.dev0\n`，exit 0，stderr 空（`-m ruocun "synthetic" --version` 亦优先返回版本） |
| `--help` / `-h` | 帮助资源可读，exit 0 |
| 包资源 | `importlib.resources` 可读 `help.zh-CN.txt` 与新增提示词资源 |
| 普通一次性 prompt | exit **69** + `RuoCun：Agent 运行路径尚未实现。`（stderr） |
| `ruocun_acceptance offline` | 4 case 全 passed；其余 6 suite 仍 `not-run`（未改驱动，未触碰 `test_acceptance.py` 的 protocol not-run 断言） |

**INTENTIONAL-DELTA（CLI）**：新增显式 `--chat-demo` 演示入口（任务票明确允许「扩展 cli.py 的一次性 prompt 路径」）。理由：本票必须有一条可实际运行的产品路径，而完整 Agent 尚未实现；用显式标志隔离，普通 prompt 行为完全不变。退出码 71 用于无效配置/缺凭据的明确失败（不与既有 69/70 冲突）。已登记差异与理由。

## 8. 故障归因分类（分列）

- **SOURCE-DEFECT**：无。本票未复现来源故障；冻结源码只作行为真值来源。
- **PORT-REGRESSION**：无。任务03 基线 29 passed 与 offline 4 case 在全量回归中保持通过；`--version/--help/69` 逐项复验。
- **INTENTIONAL-DELTA**（均有 ADR/规格/契约依据）：
  1. `--chat-demo` 一次性 prompt 演示入口（任务票授权；见 §7）。
  2. 品牌/环境差异白名单：`.dao/settings.json→.ruocun/settings.json`、`DAO.md→RUOCUN.md`、`python/node→python`（R-05 / ADR-0001 / ADR-0005 / D09:101），明确可枚举（3 项），其它 prompt 正文不翻译/删节。
  3. 凭据新写服务 `ruocun-api-key` / 账户 `ruocun/<profile>`、旧 `keychain:<account>` 按原 account 精确只读 `dao-api-key`、`_ruocun.credentialOrigins` provenance（D09:152-156）。
  4. SSE 按增量字节严格解码 UTF-8，非法/不完整字节明确失败，不复制来源 `data.toString()` 的 Unicode/65536 缓冲瑕疵（D09:95 / 任务票 WIRE-03）。
  5. 本票不实现 SSE error 自动重放、client 重试层与非流式 fallback（ADR-0003 精神 + 任务「别引入新的重放语义」），改为明确失败；相关能力归任务 06。
  6. 系统凭据后端不实现，按 `stored=system/file`、`not-found/refused/timeout-unconfirmed` 明确区分（D09:152）；不读、不复制、不展示真实现存密钥。
  7. 提示词模板文本作为 MIT 资源随包，Python 只做占位符/白名单替换，不复制 TS 源码逻辑。
  8. env_snapshot 只保留纯函数，真实平台探测命令后续替换（R-14）。
- **ENV**：
  - Windows 不允许文件名含控制字符 → `test_probe_top_level_dir` 改用 `monkeypatch` 在文件系统系统边界注入合成条目；这是**测试隔离适配**，非产品行为差异（冻结 sanitizeEntryName 规则本身照常验证）。
  - 基线/全量 pytest 出现 `.pytest_cache` 目录创建 `WinError 5` 的 `PytestCacheWarning`（不影响结果、exit 0；任务03 同类环境约束）。
  - 主工作区无 `.cache/wheels`，复用 `i03/.cache/wheels` 的 18 包已核验闭包（只读复制，未改锁）。
- **UNVERIFIED**：真实模型调用 **0**；人工体验 HITL 未验（ADR-0004 集中最终 77/78/85，本票不逐票请求用户操作、不代填）；其它平台实机未验；来源 oracle 全量未重跑（见 §6）。

## 9. 真实模型 / HITL / 分层状态声明

| 层 | 状态 |
| --- | --- |
| 产品自动测试 | **本票 path 已通过**（208 passed 全量，含 179 新增；5 入口全 0） |
| 来源 oracle | 本票未重跑 Node oracle（02 已验部分驱动）；预期来自冻结源码与既有 TS 断言 |
| 真实模型 | **调用 0 次**（无授权凭据与费用范围；合成 SSE 服务 + 合成账户配置） |
| 终端体验 / HITL | **未验**，按 ADR-0004 集中最终 77/78/85；本票不请求用户键盘/窗口操作、不代填人工验收 |
| Windows 全功能 / 安装产物 | 后续票；本票 not-run |

## 10. 资源清理回执

- 本地合成 loopback SSE 服务：每个 e2e case 与手动演示均在 `finally` 中 `shutdown()` + `server_close()` + `thread.join(timeout=5)`，报告 `server_closed=true`；无监听端口/后台线程遗留。
- 合成配置目录 `.cache/i04-demo/`、wheel 闭包 `.cache/wheels/`、`.venv/`、`dist/`、`build/`、`.cache/boot/raw/` 全部位于 `.gitignore` 忽略目录；未清理他人 worktree，未清理共享缓存。
- 所有测试/构建命令经 `tools/run.py` 以 `subprocess.run(..., capture_output=True)` 同步等待（`command_joined=true`），无游离自有进程。
- 合成凭据 `sk-synthetic-NOT-A-REAL-KEY`、合成环境值（`RUOCUN_MAX_OUTPUT_TOKENS=50000` 等）均为非真实值；所有 run.py `scan_hit=false`；`raw/demo-output.json` 经检查 `secret_in_output=False`；未读取真实用户 HOME/AppData/凭据/密钥（白名单 + 合成根）。
- 若发现敏感材料将先隔离脱敏并说明；本票未发现真实秘密进入日志。

## 11. 未改公共文件声明

未修改：`.scratch/ruocun/implementation.md`、`.scratch/ruocun/module-map.md`、`.scratch/ruocun/acceptance-matrix.md`，以及任务票 `04-chat.md` 的 Status/Assignee/Branch/Worktree 字段。对应表、矩阵与任务状态由主协调代理统一维护；新增模块登记请求见 §2。
