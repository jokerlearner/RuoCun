# 任务 04 收尾验证（final-check）

> 本文件只记录**收尾实现代理**这一小步的核查与验证结论；`README.md` 与
> `raw/summary.json` 的历史结论未改动、未重写。

- 角色：任务 04 收尾实现代理（独立上下文）
- 唯一工作根目录：`D:/java supplement/Firstcode/RuoCun/.worktrees/wb-i04`
- 分支：`impl/04-chat`
- 接手起点：`9c7c43e9387042074a42d3a87151bdd46e6d5fd6`
  （`feat(04-chat): 用兼容账户配置完成首轮流式对话`）
- 主体证据：本目录 `README.md`、`raw/summary.json`（208 passed / 3 deselected 等）
- 约束：只在指定 worktree 内操作；真实模型调用 0；活动 DAO 只读；不推远程、不建 PR；
  不清理他人 worktree、不杀他人进程；日志脱敏，只记录合成值。

## 1. 接手时的 3 个已暂存改动

接手时 `git status --short`：

```
A  src/ruocun/prompt/resources/.gitattributes
M  src/ruocun/prompt/resources/system_prompt.en.txt
M  src/ruocun/prompt/resources/system_prompt.zh.txt
```

### 1.1 真实意图

新增的 `src/ruocun/prompt/resources/.gitattributes` 共 4 行，实质规则只有一行
`*.txt -text`，注释说明：冻结提示词文本资源按原始字节保真，Git 不做 CRLF/LF
转换；与冻结快照 `.scratch/ruocun-discovery/reference/.gitattributes` 的
`* -text` 约定一致；运行时 `read_text` 仍做 universal-newline 归一，请求 golden
不受平台换行影响。

- 根 `.gitattributes` 含 `/src/ruocun/** text eol=lf`；目录级 `*.txt -text`
  对该目录的 `.txt` 覆盖之。`git check-attr -a` 结果：
  `text: unset`（另显示 `eol: lf`，属根规则残留；因 `text` 为 unset，
  Git 不做任何换行转换，提交后 blob 为 CRLF 即为其证）。
- 全局 `core.autocrlf=true`：这是此前把 CRLF 工作区规范化成 LF 存入 index 的原因。
- 冻结参考 `reference/.gitattributes` 内容为 `* -text`（已核对），注释属实。

### 1.2 字节差异性质（结论：仅行尾/字节保真，**无**提示词正文改动）

`git diff --cached --stat`：`3 files changed, 681 insertions(+), 677 deletions(-)`；
`--numstat`：`.gitattributes` `4/0`、en `344/344`、zh `333/333`（整文件每行都显示变化）。

对 HEAD(`9c7c43e`) / 暂存区 / 工作区三者做字节级核验（`.venv` 内 Python，仅本地分析）：

| 文件 | 版本 | bytes | CRLF | LF | BOM | sha256(CRLF→LF 归一) |
| --- | --- | --- | --- | --- | --- | --- |
| zh | HEAD | 32634 | 0 | 333 | 无 | `e7926bdb7f0623141b382b3c9b263c92475ccf0d8fc47cce8864421881bb07d3` |
| zh | 暂存 | 32967 | 333 | 333 | 无 | `e7926bdb…`（同上） |
| zh | 工作区 | 32967 | 333 | 333 | 无 | `e7926bdb…`（同上） |
| en | HEAD | 38635 | 0 | 344 | 无 | `89b186ffb180adc46b8206ee23e083e1414de5ae35e9acef2a2d69296640b97d` |
| en | 暂存 | 38979 | 344 | 344 | 无 | `89b186ff…`（同上） |
| en | 工作区 | 38979 | 344 | 344 | 无 | `89b186ff…`（同上） |

附加判定：

- 工作区 `==` 暂存区（byte identical）；HEAD `!=` 暂存区（仅差 333/344 个 CR 字节）。
- `HEAD.replace(b'\r', b'') == 暂存.replace(b'\r', b'')` 为 **True**（正文中不存在其它 CR）。
- 归一后（CRLF→LF）三者 sha256 完全相同；无 UTF-8 BOM。
- `git diff --cached --ignore-cr-at-eol --numstat` 与 `git diff --cached -w --numstat`：
  两个 txt 净差异 **0**，仅剩 `.gitattributes` 的 4 行；抽样 diff 显示每行仅多一个 `^M`。
- `git diff`（工作区 vs 暂存区）为空。

**结论**：3 个改动是"给冻结提示词资源加 `-text` 以按原始字节保真、把 index 中
资源由 LF 改回原始 CRLF 字节"，**不是**对提示词正文的实质改动（中文、emoji、
占位符、段落、字符数均未变）。

### 1.3 为何不影响请求 golden

`src/ruocun/prompt/system_prompt.py:40` 的 `_template()` 用
`files("ruocun.prompt").joinpath(...).read_text(encoding="utf-8")`；
`read_text` 默认 universal-newline，会把 CRLF 归一为 LF。因此无论资源是 LF 还是
CRLF，`_template()` 返回字符串相同，`buildSystemPrompt` 输出相同，请求 golden 不变。
实测证据见 §3.1。

## 2. 验证环境

- 全部经 `tools/run.py` 逐条启动：`-I -X utf8`、每次 `--label` 唯一、清空父环境、
  合成 `HOME`/`APPDATA`/`LOCALAPPDATA`/`TEMP`、`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`、
  `PIP_CONFIG_FILE=os.devnull`、**不设 `PYTHONPATH`**；runner 只回显
  `label`/`exit`/`scan_hit`。
- runner 与被测解释器均为本 worktree `.venv/Scripts/python.exe`（CPython 3.11.9），
  复用已有 `.venv` 与 `.cache/wheels`；未创建/修改锁文件。
- `pyproject.toml:27-35` 的 pytest 配置无 `pythonpath`，导入
  `.venv/Lib/site-packages/ruocun`；已核验其中两个资源为 **CRLF**
  （zh 32967 / en 38979，sha(norm) 同上），即**验证确实覆盖当前字节保真后的资源**。
- 原始输出在忽略目录 `.cache/boot/raw/<label>/{stdout,stderr,command.json}.bin`，未提交。

## 3. 验证结果（label / 命令 / 结果 / 退出码）

| label | 命令 | 结果 | 退出码 |
| --- | --- | --- | --- |
| `i04-final-pytest-full` | `python -m pytest`（默认全量） | **208 passed, 3 deselected**（对照 README §5 一致） | 0 |
| `i04-final-pytest-targeted` | `python -m pytest -q tests/test_prompt.py tests/test_client_wire.py tests/test_chat_path.py` | **64 passed** | 0 |
| `i04-final-ruff` | `python -m ruff check .` | `All checks passed!` | 0 |
| `i04-final-mypy` | `python -m mypy` | `Success: no issues found in 28 source files` | 0 |
| `i04-final-demo` | `python -m ruocun --chat-demo .cache/i04-demo 用兼容账户完成首轮流式对话` | 见 §3.1 | 0 |
| `i04-final-postmerge-pytest` | merge 后 `python -m pytest`（默认全量） | **208 passed, 3 deselected** | 0 |

6 条回执均为：`exit=0`、`scan_hit=false`、`sensitive_values_present=true`
（父环境存在敏感名变量但输出未命中）、`command_joined=true`、stderr 空。

### 3.1 请求 golden 与既有行为（决定性证据）

重跑 `--chat-demo`（复现 `i04-demo-manual` 的 argv，合成配置目录 `.cache/i04-demo`，
合成 key 与合成 dotenv 值 50000/high，均非真实值）：

```
status=complete                 answer=你好，世界 😀
model=deepseek-v4-pro           provider=deepseek   selection=native
wire_request_validated=true     server_closed=true
usage={prompt_tokens:12, completion_tokens:5, total_tokens:17}
secret_in_output=false          stderr 空
```

- 新 demo 的 `request_golden` 与既有 `raw/demo-output.json`
  **逐字段完全一致**（Python `==` 为 True）。
- system content 完全一致、`system_len=13544`（与既有相同），且
  `'\r' in system_content == False` → `read_text` 归一生效，CRLF 未泄漏进请求体。
- stdout 不含合成 key 字面串、`Bearer sk-`、`Authorization` → `secret_in_output=false`。

**判断：无回归，请求 golden 未变化**，满足"不破坏请求 golden 与既有行为"的收尾条件。

## 4. 提交与 merge

- 提交 1：`2b896f15e40f15c4a60210280008e9530a5d88ac`
  `fix(04-chat): 冻结提示词资源按原始字节保真`
  （`3 files changed, 681 insertions(+), 677 deletions(-)`；提交信息内附验证结论）。
- `git merge integration/ruocun-migration` → **`Already up to date.`**，exit 0。
  integration tip 仍为 `19b3c01eb2738937cdf3c8e3b17ae37f8b3e62de`
  （= 起点 = `merge-base`），无合并提交、无冲突、HEAD 不变，如实记录。
- 提交 2：本证据文件 `final-check.md`（新增收尾证据，SHA 见交接报告）。
- 最终 `git status --short`：干净；最终完整 SHA / 分支见交接报告。

## 5. 实际覆盖范围与未完成项

**实际覆盖**：

- 2 个冻结提示词资源的行尾字节保真与 `-text` 属性生效（提交前后 blob 均已核验）。
- 全量 208 用例（含任务03 基线 29）、提示词/请求 golden 定向 64 用例、ruff、mypy。
- `--chat-demo` 端到端：真实 `urllib` HTTP POST + 3 字节分片 SSE 严格增量 UTF-8 解码 +
  服务端校验请求 body；请求 golden 与既有记录逐字段一致。
- merge 后默认 pytest 回归。

**未跑 / 未完成（如实，不伪完成）**：

- 本次收尾**未重跑** `python -m build`、`ruocun_acceptance offline`、
  `--version`/`--help`/普通 prompt exit 69 的逐项复验；这些由上一代理在
  README §5/§7 记录，本次聚焦题目指定的 5 类验证（已全部执行）。
- 未做 Linux/macOS checkout 实机验证：`-text` 保真理论上让各平台得到相同 CRLF 字节，
  但本票只在 Windows 验证。
- 真实模型调用 **0**、HITL 未验、其它平台实机未验、来源 oracle 全量未重跑
  （沿用 README §6/§9 的 not-run 声明）。
- 未改公共文件：`.scratch/ruocun/implementation.md`、`module-map.md`、
  `acceptance-matrix.md`、任务票 `04-chat.md` 任何字段，以及证据 `README.md`
  的历史结论；未推远程、未建 PR。

## 6. 自有进程与临时资源清理

- 本地合成 loopback SSE 服务：`chat_demo.py` 在 `finally` 中
  `shutdown()` + `server_close()` + `thread.join(timeout=5)`；本次回执
  `server_closed=true`，无遗留监听端口/后台线程。
- 6 条 `tools/run.py` 命令均以 `subprocess.run(..., capture_output=True)` 同步等待
  （`command_joined=true`）；收尾复查当前 shell 未见遗留 python/ruocun 进程。
- 合成配置 `.cache/i04-demo/`、`.cache/boot/raw/`、`.venv/`、`.cache/wheels/`、
  `.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/` 均在本 worktree 忽略目录内；
  未清理他人 worktree、未杀他人进程。
- 日志脱敏：run.py 只回显合成 label / 退出码 / `scan_hit`；原始输出仅存忽略目录；
  本文件只记录合成值，未读取任何真实用户配置/凭据/密钥。
