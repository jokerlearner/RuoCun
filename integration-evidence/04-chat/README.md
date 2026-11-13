# 任务 04 — 独立 merger 复核证据

- 角色：任务 04 独立 merger（未参与本票实现，独立上下文）。
- 唯一工作根目录：`D:/java supplement/Firstcode/RuoCun/.worktrees/wb-m04`
- 分支：`merge/04-chat-verified`；起点 `19b3c01eb2738937cdf3c8e3b17ae37f8b3e62de`
- 候选：`impl/04-chat` / `df552f47c09b0fdc94992a98219f4bfb8a1a9dc4`（实现 worktree `.worktrees/wb-i04`，只读参照，未写入）
- 冻结来源唯一参照：`.scratch/ruocun-discovery/reference/README.md` 与已解包只读副本 `.worktrees/reference-dao-f17e189-7ac654a0dc06/source/`；活动 DAO 目录未取其新版本。
- 本文件只写**复核者亲自执行**的结论；实现者报告的 `208 passed` 未经复验前不采信，复验实际结果见 §4。
- 未修改产品源码、任务票、`implementation.md`、`module-map.md`、`acceptance-matrix.md`；未推远程、未建 PR、未清理他人 worktree/进程。

## 1. 起点核对（第一条命令）

```
cd "D:/java supplement/Firstcode/RuoCun/.worktrees/wb-m04" && pwd && git branch --show-current && git rev-parse HEAD && git status --short
```

真实输出：`/d/java supplement/Firstcode/RuoCun/.worktrees/wb-m04`、`merge/04-chat-verified`、`19b3c01eb2738937cdf3c8e3b17ae37f8b3e62de`，`git status --short` 为空（干净），exit 0。确认路径/分支/起点/干净四项均符合。

## 2. 两次 merge 的真实输出与退出码

命令（同一 `bash -c` 内顺序执行，各自捕获退出码）：

```
git merge --no-edit df552f47c09b0fdc94992a98219f4bfb8a1a9dc4; E1=$?; echo "MERGE1_EXIT=$E1";
git merge --no-edit integration/ruocun-migration; E2=$?; echo "MERGE2_EXIT=$E2";
git merge-base --is-ancestor df552f47c09b0fdc94992a98219f4bfb8a1a9dc4 HEAD; echo "ANCESTOR_EXIT=$?";
git log --oneline -8; git status --short
```

真实输出（原文要点）：

```
=== MERGE 1: impl/04-chat df552f4 ===
Updating 19b3c01..df552f4
Fast-forward
 33 files changed, 4877 insertions(+), 2 deletions(-)
 (新增 src/ruocun/{chat_demo,cli,client/*,config/*,env_snapshot,prompt/*}、tests/*、tools/extract_prompt.py、
  .scratch/ruocun/evidence/04-chat/* 等；均为 create mode 100644，cli.py 为 modify)
MERGE1_EXIT=0
=== MERGE 2: integration/ruocun-migration ===
Already up to date.
MERGE2_EXIT=0
=== ANCESTOR CHECK (candidate in HEAD) ===
ANCESTOR_EXIT=0
=== HEAD LOG ===
df552f4 docs(04-chat): 补充收尾验证证据 final-check.md
2b896f1 fix(04-chat): 冻结提示词资源按原始字节保真
9c7c43e feat(04-chat): 用兼容账户配置完成首轮流式对话
19b3c01 docs: 领取任务04并记录WorkBuddy接手能力核验
98154de docs: 关闭任务03并保存WorkBuddy接续工作流
...
=== STATUS ===
(空)
```

- MERGE1：Fast-forward `19b3c01..df552f4`，exit **0**。
- MERGE2：`Already up to date.`，exit **0**。
- `merge-base --is-ancestor df552f4 HEAD`：exit **0**，HEAD 包含候选完整历史；`git log` 显示候选 3 个提交（`9c7c43e`→`2b896f1`→`df552f4`）依次叠在起点 `19b3c01` 之上。
- 合入后 `git status --short` 为空（干净）。

## 3. 环境与闭包（亲自搭建）

| 项 | 值 |
| --- | --- |
| 固定解释器 | `C:/Users/PC/AppData/Local/Programs/Python/Python311/python.exe`（CPython 3.11.9，`-I -X utf8`） |
| 公开 wheel 闭包 | 只读复制 `.worktrees/i03/.cache/wheels` 的 18 个已核验公开 wheel 到本 worktree `.cache/wheels`；未读实现者私有缓存、未读私有日志/真实凭据 |
| 锁一致性 | 独立 `sha256sum .cache/wheels/*.whl` 18 个 hash 与 `requirements-dev-win311.lock` 逐条一致（ast_serialize ddf7… / build ecd3… / hatchling 4152… / mypy 6f72… / pytest 872f… / ruff 56b8… 等） |
| 本 worktree venv | `D:/java supplement/Firstcode/RuoCun/.worktrees/wb-m04/.venv`（按锁自建；18 wheel `--require-hashes` 安装，产品 wheel 与 `tests/support` 支撑 wheel `--no-deps` 安装） |
| 所有工程命令 | 逐条经 `tools/run.py` 从明确白名单环境启动：清空父环境、合成 HOME/AppData/TEMP、`PYTHONNOUSERSITE`/`PYTHONSAFEPATH`/`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`、`PIP_CONFIG_FILE=os.devnull`、不设 PYTHONPATH；每次 `--label` 唯一；均回显 `scan_hit=false`、`command_joined=true` |
| 仓库外验证 venv | `C:/Users/PC/AppData/Local/Temp/ruocun m04 独立验证/venv`（中文空格路径；只装本票构建出的 wheel） |

`command.json` 抽查（`raw/pytest-command.json`）显示 `environment: explicit allowlist; synthetic home/config/temp; no PYTHONPATH`、`sensitive_values_present: true`（父环境存在敏感名变量）、`sensitive_match: false`、`command_joined: true`；`m04-clean-version/command.json` 的 `argv`/`cwd` 均为仓库外验证路径，无真实 HOME/凭据。

## 4. 五项入口全量复验（亲自执行，逐条 label/退出码/实际结果）

| 入口 | label | 退出码 | 真实结果（读 `.cache/boot/raw/<label>/stdout.bin`） |
| --- | --- | --- | --- |
| `python -m pytest`（默认集） | `m04-pytest-full` | 0 | `collected 211 items / 3 deselected / 208 selected`；**`208 passed, 3 deselected in 8.83s`**（pytest 8.4.2 / CPython 3.11.9 / rootdir wb-m04） |
| `python -m ruff check .` | `m04-ruff-full` | 0 | `All checks passed!` |
| `python -m mypy` | `m04-mypy-full` | 0 | `Success: no issues found in 28 source files` |
| `python -m build`（`--wheelhouse .cache/wheels`） | `m04-build-final` | 0 | `Successfully built ruocun-0.1.0.dev0.tar.gz and ruocun-0.1.0.dev0-py3-none-any.whl` |
| `python -m ruocun_acceptance offline` | `m04-offline-final` | 0 | 4 case 全 `passed`、整体 `passed`、`logical_exit 0`：`ENT-01.version`(exit 0)、`ENT-01.help`(0)、`ENT-01.resource`(0)、`ENT-01.unimplemented`(**exit 69**，`Agent 运行路径尚未实现`)，逐 case 有 owned Popen/cleanup 回执 |

安装链各条 `run.py` 退出码：`m04-setup-venv`=0、`m04-install-tools`=0、`m04-install-product`=0、`m04-install-support`=0；`IMPORTS_OK`（`ruocun`/`ruocun_acceptance`/`pytest`/`ruff`/`mypy`/`build` 均可导入）。

构建产物实查：`dist/ruocun-0.1.0.dev0-py3-none-any.whl`（73955 字节）、`.tar.gz`（62940 字节）；`python -m zipfile -l` 列出 wheel 成员含 `ruocun/prompt/resources/system_prompt.zh.txt`(32967)、`system_prompt.en.txt`(38979)、`resources/help.zh-CN.txt`、LICENSE/NOTICE 与 dist-info，且不含 `tests/`/`.scratch/`。

## 5. 最终安装产物验证（仓库外干净 venv，只装本票 wheel）

venv 绝对路径：`C:/Users/PC/AppData/Local/Temp/ruocun m04 独立验证/venv`；`pip install --no-index --no-deps <本票 wheel>`。所有验证命令经 `run.py --cwd <仓库外验证根>` 启动（`-I` 隔离、无 PYTHONPATH、不借源码路径、不装支撑包/开发工具）。

| 验证 | label | 退出码 | 真实结果 |
| --- | --- | --- | --- |
| 新建 venv / 只装 wheel | `m04-clean-venv` / `m04-clean-install` | 0 / 0 | 中文空格路径下创建、安装成功 |
| `--version` | `m04-clean-version` | 0 | `RuoCun v0.1.0.dev0` |
| `-v` | `m04-clean-v` | 0 | `RuoCun v0.1.0.dev0` |
| `--help` | `m04-clean-help` | 0 | 帮助资源可读，`用法：ruocun [选项] [提示词]` |
| `-h` | `m04-clean-h` | 0 | 帮助资源可读 |
| 普通一次性 prompt | `m04-clean-prompt69` | **69** | stderr `RuoCun：Agent 运行路径尚未实现。`，stdout 空 |
| 包资源与导入来源 | `m04-clean-resource` | 0 | `ORIGIN=...\ruocun m04 独立验证\venv\Lib\site-packages\ruocun\__init__.py`；`HELP_LEN=187`、`ZH_LEN=13271`、`EN_LEN=38430`、`ZH_HAS_IDENTITY=True`、`EN_HAS_HEADER=True`、`NO_SRC_PATH=True`、`NO_DEV_TOOLS=True`、`NO_SUPPORT_PKG=True` |
| 合成配置目录 `--chat-demo` 端到端 | `m04-boundaries` 内 `cli_end_to_end` | 0 | `status=complete`、`answer=你好，世界 😀`、`server_closed=true`、`wire_validated=true`、`secret_leak=false`、stderr 空、子进程 `child_joined=true` |

新增提示词文本资源（zh/en）随 wheel 可读且中英文关键内容存在；导入 origin 在仓库外 site-packages，sys.path 无源码路径，无 pytest/ruff/mypy/build/hatchling、无 `ruocun_acceptance`。

## 6. 失败 / 取消 / 资源退出边界（独立构造，非实现者报告）

复核者自写脚本 `C:/Users/PC/AppData/Local/Temp/ruocun m04 独立验证/m04_boundaries.py`（不改产品，仅在仓库外干净 venv 运行），经 `run.py --label m04-boundaries` 启动，exit 0、`scan_hit=false`；原始输出全文保存在 `raw/boundaries.json`（sha256 `127b24b14b465f692923aa2901bf5bed2899b7b834eae11ed98b9818b766dcee`）。

### 6.1 配置/凭据失败（CLI，合成配置目录）

| 场景 | exit | 诊断 | secret 泄漏 | 伪成功 |
| --- | --- | --- | --- | --- |
| 缺配置目录 | 71 | `一次性对话失败（ChatConfigError）：缺少有效凭据：激活 profile 无内联 key…` | false | false |
| config.json 坏 JSON | 71 | 同上（坏 JSON 视为空档案 → 缺凭据） | false | false |
| compatibility.json 坏 JSON | 71 | `一次性对话失败（CompatibilityError）：…compatibility.json: 坏 JSON` | false | false |
| compatibility.json 未知 version(99) | 71 | `…version 必须是 1` | false | false |
| compatibility.json 缺 `sources[0].id` | 71 | `…sources[0].id 非空` | false | false |
| compatibility.json 缺 `sources[0].path` | 71 | `…sources[0].path 必须是绝对路径` | false | false |
| 缺 key + 通用环境变量 `OPENAI_API_KEY=sk-env-NOT-REAL-M04` | 71 | `缺少有效凭据`（未靠通用变量挑账户） | false | false |

全部为明确失败、有具体文件/字段诊断、退出码 71、无伪成功、无秘密泄漏。

### 6.2 SSE / 流失败（产品公开 API + 注入合成 transport）

| 场景 | 实际结果 |
| --- | --- |
| 非法 UTF-8 字节 `data: \xff\xfe bad\n\n` | `UnicodeDecodeError: invalid start byte`（明确错误） |
| 不完整 UTF-8（中文三字节只来两字节）后 `flush()` | `UnicodeDecodeError: unexpected end of data`（明确错误，不产生半个字符） |
| SSE error 事件 | `SseError: SSE error from API: {'code':'E2004',...}`（不静默吞、不自动重放） |
| 非 2xx(401) | `ApiError: API error 401` |
| 中途断流且尚无产出 | `StreamError: SSE 中途断流且尚无产出` |
| 有产出后断流 | `status=partial`、`answer=part`（保留部分、明确标记，不伪报成功） |
| 缺 `[DONE]` 且中途断流 | `status=partial`、`answer=partial`（不伪报成功） |
| 缺 `[DONE]` 但数据帧完整、EOF 干净结束 | `status=complete`、`answer=完整答案`、`finish_reason=null`、usage 有效；见 §11 观察项 O-1 |

非法/不完整字节与无产出断流均明确抛错，未把部分输出当成功答案。

### 6.3 资源退出（独立端口/线程/socket 检查，不只看 `server_closed` 字段）

用真实 `SyntheticSSEServer` + 真实 `urllib` HTTP POST，在 `finally` 中 `shutdown()` → `server_close()` → `thread.join(timeout=5)`，并**独立**用 `socket.connect_ex` 探测端口、检查 `server.socket.fileno()`、`thread.is_alive()` 与 `threading.enumerate()`：

| 场景 | port | listening_before → after | thread_alive | socket.fileno（关闭后） | owned 线程仍在枚举 | 结果 |
| --- | --- | --- | --- | --- | --- | --- |
| 成功路径（真实 HTTP） | 50296 | true → **false** | false | **-1** | false | `answer=你好，世界 😀` |
| 失败路径（非法 UTF-8 使 streamChat 抛 `UnicodeDecodeError`） | 51678 | true → **false** | false | **-1** | false | 错误明确、服务仍被关闭 |

脚本结束 `thread_summary.alive_threads=["MainThread"]`（无遗留线程）。最终独立复查（脚本结束后）：`socket.create_connection` 对 50296/51678 均抛 `TimeoutError`（`NOT_LISTENING`，无成功连接）；`connect_ex=10035`（非零）。`tasklist` 列出多个 python.exe 属其它 worktree/会话所有，本次所有子进程均 `subprocess.run` 同步 join，未清理/未杀他人进程。

## 7. 输入/预期独立来源真实性抽查

逐项对照冻结源码与既有 TS 断言（只读解包副本）：

| Python 文件 | 对照的独立来源 | 结论 |
| --- | --- | --- |
| `tests/test_client_wire.py` | 冻结 `src/client/client.test.ts`（97-152 请求体/参数、154-196 历史清洗、198-278 usage/finish_reason、36-95 累积器、280-284 非2xx）、`client.ts:50-120/208-269` | 请求字段顺序、`max_tokens` 默认 128000、`DAO_MAX_OUTPUT_TOKENS=50000`、`gpt-5` 用 `max_completion_tokens`、extra 覆盖、不加采样参数、null content→空串、reasoning 按工具轮带回、工具参数按 index 累积、空 id 不冲掉真实 id、usage 归一化（千帆 9611/9216/395）、finish_reason 有效才确认、非 2xx/SSE error 明确失败，均与 TS 断言一致；期望值为硬编码常量/规格值，**非**从 Python 实现输出回填 |
| `tests/test_prompt.py` | 冻结 `src/prompt/system_prompt.test.ts`（4-318） | 身份行、模型自识别/视觉、反思开关、项目指令、占位符、记忆/envSnapshot、interactive/headless TodoWrite、en 头部、长任务 directive 逐项一致；品牌白名单来自 R-05/ADR-0005/D09:101 |
| `tests/test_config_pure.py` | 冻结 `src/config/profiles.test.ts`（4-210）、`model_selection.test.ts`（5-31） | v2 迁移/未知顶层字段保留、6 provider 默认端点、各 provider 目录 ID 清单、contextWindowFor 渠道窗口（200K/1M/198K/256K/1.024M）、vision 正负例、outputLimitFor cap、override>agent>parent、缺 parent 明确报错、自定义网关不猜便宜档，逐项与冻结 TS 断言一致 |
| `tests/test_config_env.py` | 冻结 `src/config/env_file.test.ts`（7-66）+ D09:144-148 + 冻结 `index.ts:942`/`trust.ts:34`/`keychain.ts:18`/`client.ts:104/127/390` | dotenv 简化方言与"已有 env 含空串优先"来自 TS 断言；RUOCUN_/DAO_ 别名、逐变量谓词（AUTO_APPROVE 非空真、TRUST 仅 "1"、USE_KEYCHAIN 仅 "0"/"off"、Number||default、第三方变量保留原名）来自已确认 D09 契约与冻结源码行号，属"已确认规格/冻结源码"类独立来源 |
| `tests/test_client_sse.py` | 冻结 `src/client/sse.test.ts`（4-38）、`client.ts:313-335`、D09:95 | 字符串分帧（单/多帧、rest、[DONE]、注释/空行、CRLF、末帧 flush）逐项一致；逐字节/多块大小的中文/emoji 严格增量 UTF-8 解码、非法/不完整字节报错来自 D09:95 已确认差异（不复制来源 `data.toString()` 瑕疵） |
| `tests/test_chat_path.py` | 合成账户配置 + 规格/TS 断言 | `max_tokens=50000`、`reasoning_effort=high`、`messages` 结构、`temperature/top_p` 缺席、品牌白名单、兼容源零写入来自合成配置/规格/冻结行为；见 §11 O-2 |

总体：4 个抽查文件的请求 golden、模型目录数据、环境谓词、SSE 分帧预期主要来自冻结源码/既有 TS 断言/已确认规格（D09、R-05/R-06/R-07），**未发现"从 Python 当前实现输出回填期望值"的自证断言**（所有期望均为硬编码常量或规格值）。但存在以下弱/自证成分，具体指出文件与行号（§11 O-2）：

- `tests/test_client_wire.py:309`：`assert json.loads(captured[0][2]) == result.request_body` —— 同一 `body` 对象的两次序列化自比较（恒真），不构成独立请求 golden 校验。
- `tests/test_chat_path.py:74`、`tests/test_chat_path.py:87`：`answer == "你好，世界 😀"` 的预期来自产品内合成夹具 `src/ruocun/chat_demo.py:36-44` 的 `_SYNTHETIC_FRAMES`；`wire_request_validated` 是产品自报字段（服务端捕获 body 与 `result.request_body` 同源比较）。属端到端演示合成数据，不是冻结来源/TS 断言的独立 oracle；值在测试中硬编码，非运行时从产品输出回填。
- `tests/test_config_pure.py:114-120`、`tests/test_prompt.py:154-160`：遍历产品自身常量（`MODELS_BY_PROVIDER`、`BRAND_DELTAS`）做结构自洽检查，独立 oracle 强度有限；对应冻结 `profiles.test.ts:102-108` 同类断言，属忠实改写，非输出回填。

## 8. 任务 03 既有行为回归（逐项复验）

| 行为 | 复验位置 | 实际结果 |
| --- | --- | --- |
| `--version` / `-v` | 仓库外 venv `m04-clean-version`/`m04-clean-v`；`m04-offline-final` | `RuoCun v0.1.0.dev0`，exit 0，stderr 空 |
| `--help` / `-h` | 仓库外 venv `m04-clean-help`/`m04-clean-h`；offline | 帮助资源可读，exit 0 |
| 包资源 | `m04-clean-resource`；wheel 成员清单 | `help.zh-CN.txt` 与新增 zh/en 提示词资源随包可读 |
| 普通一次性 prompt | `m04-clean-prompt69`；offline `ENT-01.unimplemented` | exit **69**，stderr `RuoCun：Agent 运行路径尚未实现。` |
| `ruocun_acceptance offline` | `m04-offline-final` | 4 case 全 passed（其余 6 suite 仍 not-run，未改驱动） |

任务 03 行为无回归。参照 `.scratch/ruocun/integration-evidence/03-boot/README.md` 与 `r2/README.md` 的严格口径：独立构造真实故障、owned 子进程真实 join、独立端口/进程检查、失败原始输出保留、分层/未验如实记录。

## 9. 环境白名单与脱敏

- 所有工程命令经 `tools/run.py` 逐条启动，label 唯一；argv 仅含解释器绝对路径与模块/脚本参数，不含真实 HOME/凭据；`command.json` 显示合成白名单环境、`sensitive_match=false`、`command_joined=true`。
- 候选证据 `raw/demo-output.json`（34686 字节）全量扫描：`sk-synthetic`/`Bearer`/`Authorization`/`SECRET`/`PASSWORD`/`TOKEN`/`api_key`/`sk-` 字面串 **0 命中**，正则 `sk-[A-Za-z0-9_-]{6,}` 无匹配；`status=complete`、`server_closed=true`、`wire_request_validated=true`、`answer=你好，世界 😀`。
- 候选证据目录 Grep 唯一命中为 `README.md:184` 明确标注的合成值 `sk-synthetic-NOT-A-REAL-KEY`（非真实值），无真实 HOME/AppData/凭据路径。
- 复核证据只记录合成值（合成 key、合成 dotenv、合成临时路径）；未读取真实用户配置/凭据/密钥。

## 10. 分层状态与未验项（分别记录）

| 层 | 状态 |
| --- | --- |
| 产品自动测试 | **本票路径已亲自通过**：5 入口全 exit 0（pytest 208 passed/3 deselected、ruff、mypy 28 files、build、offline 4 case），仓库外 wheel-only 安装产物验证通过，7 类配置失败边界 + 8 类 SSE/流边界 + 资源退出独立证实。不扩为母案例族或全量规格通过 |
| 来源 oracle | **not-run**：本票未重跑 Node oracle / 全量 215 来源文件；预期真值来自冻结源码与既有 TS 断言静态对照，沿用 02 已验 6 文件 190 断言，不冒充本票通过 |
| 真实模型 | **0 次**（合成账户配置 + 本地合成 loopback SSE 服务，无授权凭据与费用范围） |
| 终端 / HITL | **not-run**：ADR-0004 集中最终 77/78/85；未请求用户键盘/窗口操作、未代填 |
| Windows 全功能 / 安装产物 | **部分执行**：仅覆盖仓库外中文空格路径干净 venv 只装产品 wheel 的 CLI 版本/帮助/资源/exit 69/`--chat-demo` 端到端；onedir/onefile 独立产物、升级/卸载、真实 Windows Terminal、中文 IME/连续缩放、WT-01..09、系统凭据后端、IPC/ACL/Job/定时/剪贴板/通知/OS 沙箱均为 **not-run** |
| 其它平台实机 | **not-run**（Linux/macOS 保留设计，未实机验收） |
| 完整 Agent / StoragePort / 会话恢复 / 六 suite 其余 | **not-run**（后续票；普通 prompt 仍 exit 69） |

## 11. 发现的问题清单

**无阻断缺陷**（5 入口、安装产物、失败边界、资源清理、抽查均通过）。以下为如实记录的观察项，交主代理/实现者判断，本复核不私改产品、不放宽测试：

- **O-1（`[DONE]` 缺失但 EOF 干净结束，非回归、待语义确认）**：独立构造 `done_missing_but_eof_clean`（fake transport 两 content 帧 + usage 帧、无 `[DONE]`、正常 EOF），产品返回 `status=complete`、`answer=完整答案`、`finish_reason=null`、usage 有效，**未对"缺结束标记"给出明确错误**。对照冻结 `client.ts:210`（`[DONE]` 仅作被跳过哨兵）与 `client.ts:313-337`（流终止由 `reader.read().done` 决定），来源本身不因缺 `[DONE]` 报错，Python 为忠实迁移；且答案是完整数据帧累积结果而非"部分输出"，未违反"不把部分输出当成功答案"的实质。但相对本次复验清单"`[DONE]` 缺失 → 明确错误"的字面期望存在差异。复现命令：`m04_boundaries.py` 的 `done_missing_but_eof_clean`（label `m04-boundaries`，原始结果 `raw/boundaries.json`）。是否需要对"缺 `[DONE]` 的正常 EOF"增加显式失败/终止标记校验，属产品语义/范围决定，交主代理（或后续票）处理；本票按冻结来源行为实现，不构成 PORT-REGRESSION。
- **O-2（弱/自证断言，非回归，已指出文件与行号）**：见 §7 末尾四条（`test_client_wire.py:309`、`test_chat_path.py:74/87`、`test_config_pure.py:114-120`、`test_prompt.py:154-160`）。均为"以产品自身输出/常量为断言对象"的结构性自证或演示合成夹具，独立 oracle 强度有限，但**不是**从 Python 当前实现输出回填期望值（全部为硬编码常量/规格值），未发现任务票禁止的自证断言。
- **ENV（非缺陷）**：`connect_ex` 最终复查返回 10035（WSAEWOULDBLOCK 类非零值），阻塞 `create_connection` 抛 `TimeoutError` 而非 `ConnectionRefusedError`；结合脚本内同一进程 `listening_after=false`、`socket_fileno_after_close=-1`、`thread_alive=false`，仍足以判定无遗留监听端口，未夸大证据。

## 12. 自有进程 / venv / 临时资源清理

- 本 worktree 自建 `.venv`、`.cache/wheels`、`.cache/boot/raw/`、`dist/`、`build/`、`.pytest_cache/` 等均在本 worktree 的 `.gitignore` 忽略目录内，保留（不提交、不清理他人资源）。
- 仓库外验证 venv 绝对路径 `C:/Users/PC/AppData/Local/Temp/ruocun m04 独立验证/venv`，**清理方式**：本次复核收尾由复核者删除该自建目录树（含 `venv/`、`cfg/`、`m04_boundaries.py`）；该目录在仓库外、非他人 worktree、非共享缓存。清理回执在最终返回中如实给出。
- 两个合成 loopback 服务（端口 50296/51678）：`shutdown()`+`server_close()`+`thread.join()` 真实发生，脚本内与脚本后独立端口探测均无监听，线程枚举只剩 MainThread，无自有遗留进程；`tasklist` 中其它 python.exe 为他人所有，未杀、未清理。
- 所有 `run.py` 子进程 `command_joined=true`（同步等待），边界脚本内 `subprocess.run` 全部同步 join。

## 13. 结论与建议

- 两次 merge 与 HEAD 历史核对通过；五项入口、仓库外 wheel-only 安装产物、失败/取消/资源退出边界、来源真实性抽查、任务 03 回归、白名单脱敏均**亲自复验通过**，无阻断缺陷。
- 建议主代理按**本票路径范围**接收/集成；O-1 为相对复验清单字面期望的语义观察项（与冻结来源一致、非回归），请主代理确认是否需要差异决定；O-2 弱断言建议后续补独立 oracle 时加强。
- 母案例族与全量规格不因本票标全量通过；来源 oracle not-run、真实模型 0 次、终端/HITL not-run（ADR-0004 → 最终 77/78/85）、Windows 全功能仅按 §10 实际范围执行。
