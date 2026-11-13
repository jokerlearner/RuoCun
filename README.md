# 若存 Code（RuoCun）

若存 Code 是用 Python 编写的终端编码助手。它可以在指定项目目录中阅读和修改代码、执行命令，并在重开会话后继续工作。

当前安装包面向 Windows x64 和 CPython 3.11。各平台的验证范围见[发布记录](docs/release/batch-09.md)。

## 当前状态

当前版本包含分层权限、前台输入队列、后台任务、文件搜索、Skills 和上下文压缩。各批固定产物、自动检查和实机验收记录见[实施进度](.scratch/ruocun/implementation.md)及[发布记录](docs/release/batch-09.md)。

开发使用 pytest、统一验收驱动、Ruff、mypy 和 build。构建与复现方法见[开发说明](docs/development.md)。

Codex 负责编码和自动验证，用户负责决策和体验验收。
已确定目标以 [CONTEXT.md](CONTEXT.md) 为准。

## 用法

将 Windows wheel 安装到 CPython 3.11 的专用环境。离线安装、手动更新和恢复见[安装指南](docs/install-and-recovery.md)。

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install "路径\ruocun-0.1.0.dev0-py311-none-win_amd64.whl"
.venv\Scripts\python -m ruocun --help
```

真实终端首次启动时，引导会设置语言、服务商、密钥和工作目录信任。也可在`%USERPROFILE%\.ruocun\config.json`预先填写账户，或用`--config 文件`显式选择。管道和一次性提示模式需要已有可用配置。

```json
{
  "version": 2,
  "activeProfile": "main",
  "profiles": {
    "main": {
      "provider": "openai",
      "baseUrl": "https://你的兼容服务地址/v1",
      "model": "你的模型ID",
      "key": "你的API密钥"
    }
  }
}
```

账户配置优先读取内联key，也支持Windows系统凭据的keyRef。将配置保存在项目外，不提交凭据。
支持既有Chat/Responses路由及六种已登记provider格式；费用和连接由用户自己的服务决定。

```powershell
.venv\Scripts\python -m ruocun --cwd "你的项目目录"
.venv\Scripts\python -m ruocun --cwd "你的项目目录" "读取项目并修复一个问题"
.venv\Scripts\python -m ruocun --cwd "你的项目目录" --continue
.venv\Scripts\python -m ruocun --cwd "你的项目目录" --continue 会话ID
```

权限按分层规则与有效模式裁决，需人工审批时仅在真实交互终端询问。一次性提示词和pipe不会把输入的`y`当作批准。用`--permission-mode`选择模式，`--allow`、`--ask`、`--deny`追加本次规则。`/mode`、`/plan`和`/permissions`用于会话内查看或调整。plan同时限制模型可见工具与实际执行。auto分类失败、结果不明或达到熔断条件时转人工，显式拒绝规则始终有效。Windows的Bash工具默认运行cmd，按实际执行计划分析方言。未知方言仅支持本次人工确认。Windows没有OS沙箱。

交互终端忙时可继续编辑草稿，已确认输入保存后在安全工具边界按序消费。pipe保持逐轮顺序。Esc先持久清空等待队列，再次按下暂停当前轮。Ctrl+C暂停当前轮，2秒内再次按下退出。审批中的取消会拒绝当前审批并暂停。`/exit`退出，`/usage`、`/cost`查看用量，`/files`查看本会话已读文件。完整选项以`--help`为准。

同一批安全工具最多8路并行；写入或执行命令时独占，结果按调用原序返回。未知副作用仍停止处理。

AskUserQuestion支持选项、多选、自填和先讨论，SendUserMessage可显示正文与附件。Bash可显式转后台，使用BashOutput读取新增日志、KillShell请求停止。只有已持久保存且runner确认的后台保留决定允许跨会话退出继续运行，恢复接管同一次执行。Shell取消以真实进程树和日志关闭回执为准。NotifyUser提供终端提示。

Agent可同步或后台执行内置或已发现的角色。TaskWait可等待后台Shell或代理，完成事件和用户消息持久投递。用TaskOutput查询子代理新增转录，TaskStop先记录取消请求，等同一执行器确认退出。

终端支持内联 Markdown、工具执行展示、双语界面、主题、图片附件和欢迎形象。用 `/account` 选择或管理账户，`/model` 选择模型，`/lang` 保存语言，`/theme` 切换本次主题，Alt+V 附图。删除当前账户后，本进程保留原连接，直到手动切换账户或重启。

`/recovery`可在未知操作阻塞时查询现场，以resolve/decide记录人工核实决定。普通后台子代理因进程中断而失去执行器时，可用`/recovery continue <任务ID> <继续指令>`恢复。命令核对原定义、模型、权限和目录，再启动一个新运行。旧工具结果保留，同一恢复指令重复提交只返回已有结果。

项目指令读取 `RUOCUN.md` 和 `RUOCUN.local.md`，项目配置按信任规则启用。`/skills` 选择启动技能，`/<技能slug>` 调用。模型也可按需读取 Skill 正文。文件访问可发现嵌套技能并激活匹配 paths 的条件技能。SkillInstall 按权限安装本地或 Git 的完整资源，结果保存后同一会话即可调用新技能。外来正文可在加载时适配，转换失败沿用原文。技能开关重启生效。

模型可用 MemoryRead 查询长期记忆，用 MemoryWrite 按权限写入项目、用户或知识域。用 `/memory` 查看并审核记忆，用 `/memory delete 名称` 删除可写记忆。项目记忆位于项目的 `.ruocun/memory`，用户记忆和知识库分别位于 `~/.ruocun/memory` 和 `~/.ruocun/knowledge`。锁定记忆保持只读。

启动时先清理达到规则的旧记忆，再按当前项目选取本次进程使用的快照。重开会话时重新选择，已保存的工具记录保持。达到条数和间隔条件时，文字交互可用当前配置模型整理同域重复记忆，整理不阻塞前台，结果下次启动才进入前缀。同名覆盖未确认时保留旧记录的恢复副本并停止该域。用 `--no-memory` 关闭本次注入和模型整理，本地清理、显式记忆工具与 `/memory` 仍可用。

会话保存在`~/.ruocun/sessions/<工作目录摘要>/<会话ID>/session.db`，运行库在`~/.ruocun/runtime`。正常退出可重开；遇到未知副作用明确阻塞，先检查实际工作目录，不自动重放。保存历史token，跨重启费用只统计本进程，不冒充完整历史账单。文件读取基线在新进程重新建立，恢复后修改现有文件须重新Read。

`/session`查看当前会话，`/resume`列出或按ID切换，`/rename`保存标题，`/branch`创建聊天分支，`/export`导出Markdown，`/clear`清空上下文。`--continue`省略ID时选择本目录最近未完成的会话，重开已完成历史使用明确ID。聊天分支保留消息和附件引用，执行记录及后台任务使用独立身份。

Monitor 按行批量推送命令输出，支持超时和持续运行，TaskStop 等待实际执行器停止。MCP 从若存用户和项目的 `mcp.json` 加载服务，支持 stdio、HTTP/SSE、工具搜索、资源和提示模板。用 `/mcp` 查看、添加、开关或重连，用 `--no-mcp` 关闭本次连接。可能已执行的请求在断线后保持未决，重开和更换工具调用 ID 时仍须核实原结果。

`/context`、`/status`查看上下文与用量，`/context-window`、`/effort`查询或调整窗口和推理力度。支持`/compact`、85%阈值主动压缩及上下文错误后的有界压缩；摘要失败或为空时保留原上下文并停止本轮。Read支持文本与常见图片格式，图片需所选模型支持视觉。

RepoMap按预算提供TS/TSX/JS/Python/Go/Rust/Java代码地图，启动时异步生成，也可经ToolSearch激活后刷新。默认预算2048，可用`RUOCUN_REPO_MAP_TOKENS=0`关闭启动地图；显式工具仍可用`max_tokens`指定预算。

WebFetch 抓取静态网页，可按提示使用当前账户的辅助模型抽取。抽取失败时返回已抓取的原文。WebSearch 解析 DuckDuckGo 网页结果。用 `--no-web` 关闭这两项工具和网页抽取。抓取的网络检查范围为初始主机名和字面地址。`max_chars` 限制返回文本，抓取不执行网页 JavaScript。

Config工具读取项目优先的设置并写入原生用户`settings.json`，可经ToolSearch激活；`/Config`仅显示当前配置状态。保存不会立即重载权限模式或检查点，主题仍由`/theme`临时切换；损坏文件拒绝覆盖并保留原字节。

LSP从用户或项目的`lsp.json`读取`servers`配置，每项声明`command`、`args`、`extensions`；按需启动已配置的语言服务器，支持定义、引用、悬停、符号及调用层级等9项操作。位置按外部1-based/协议UTF16约定处理，Windows文件路径转换为URI；无配置时不注册工具。语言服务器由使用者另行准备，RuoCun不自动安装。

平台支持和已验证的终端功能见[发布记录](docs/release/batch-09.md)。启动器在 Windows 应用控制下的限制见[安装指南](docs/install-and-recovery.md)。

## 工程入口

- 开发规则：[AGENTS.md](AGENTS.md)
- 项目上下文：[CONTEXT.md](CONTEXT.md)
- 本地任务工作流：[issue-tracker.md](docs/agents/issue-tracker.md)
- 文档阅读规则：[domain.md](docs/agents/domain.md)
- 架构决定：[docs/adr/](docs/adr/)
- 迁移基线：[baseline.md](docs/migration/baseline.md)
- 当前决策地图：[RuoCun 迁移决策地图](.scratch/ruocun-discovery/map.md)
- 冻结参考快照：[复现方法](.scratch/ruocun-discovery/reference/README.md)
- 模块对应：[module-map.md](docs/migration/module-map.md)
- 验收矩阵：[acceptance-matrix.md](docs/migration/acceptance-matrix.md)
- 迁移规格：[spec.md](.scratch/ruocun-migration/spec.md)
- 首张任务票：[01-baseline-inventory.md](.scratch/ruocun-migration/issues/01-baseline-inventory.md)

规格、任务票、ADR、对应表和验收记录均纳入 Git。
创建 worktree 时，从包含这些记录的提交创建，文档内部使用仓库相对链接。

可直接维护 docs/agents/ 下的配置；切换 issue tracker 或重新建立工作流时再运行 setup-matt-pocock-skills。
相关工程技能通过 AGENTS.md 中的入口读取本项目约定。

## 许可

若存原创内容采用 [MIT 许可证](LICENSE)。[发布须知](NOTICE.md) · [第三方许可证](THIRD-PARTY-LICENSES.txt)
