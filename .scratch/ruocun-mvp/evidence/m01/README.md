# M01 六工具候选证据

状态：实现与定向自动验证通过，等待独立复核；本文件不将原完整迁移票或人工体验标为完成。
工作树：`.worktrees/mvp-files`，分支：`codex/mvp-files`。
派发起点：`e672f7201a9db371c1bcf7b7cb22fa9cf5e707ab`；首次送审已合入根候选 `d31e5e4`（含 `235f840`、`ec38bc8`）；junction回修送审合入根 `675f593`。

## 来源与实现

统一来源为冻结 `dao-f17e189-7ac654a0dc06/source.zip`，只读展开位置为另一工作树 `.worktrees/b01-tools/.cache/frozen`；未改活动 DAO。所读工具/支撑/测试成员哈希见 [source-hashes.json](source-hashes.json)。MIT 来源与版权继续由项目 LICENSE/NOTICE 保留。

| 来源 | Python 产物/职责 | 来源测试数 |
| --- | --- | ---: |
| read_file.ts / read_file.test.ts | `read_file.py`：行号、offset/limit、裁剪、二进制/大小限制、已读/mtime/size | 14 |
| write_file.ts / write_file.test.ts | `write_file.py`：新建/整写、写前读取、重复整写限制、元信息拒绝 | 10 |
| edit_file.ts、edit_mismatch.ts、diff_hunk.ts / edit_file.test.ts | `edit_file.py`：精确/形近标点替换、唯一性、并发串行和带行号diff | 9 |
| todo_store.ts、todo_write.ts / todo_write.test.ts | `todo_store.py`、`todo_write.py`：整表替换、最多1个in_progress、activeForm和完成提醒 | 10 |
| paths.ts、file_lock.ts、fs_atomic.ts / paths.test.ts | `paths.py`：路径与链接逃逸、区外授权、同路径锁和临时文件原子替换 | 6 |
| glob.ts、walk.ts、file_search.ts / 三份对应test.ts | `glob.py`、`glob_files.py`：匹配、忽略目录、文件范围、mtime倒序和100条上限 | 12 |
| grep_files.ts、output.ts / grep_files.test.ts | `grep_files.py`：内容/文件、上下文/分页/跨行/类型过滤、only_matching和输出上限 | 17 |
| registry.ts、schema.ts / registry.test.ts核心普通工具与schema.test.ts | `registry.py`、`schema.py`：顺序注册、解析、参数诊断和派发 | 13 |
| 合计 | 仅首版适用的来源语义迁移 | **91** |

仅测试以上公开工具 handler、路径/匹配公开函数和注册派发接口。没有新增压力、竞态排列、模型或故障注入框架。

## 首版必要适配与未覆盖

- 工具声明采用根固定 `tools/types.py`：camelCase上下文、threading.Event。注册表默认空；`register`、`get`、`toApiTools`、`dispatch`按固定契约；额外 `validate(name, rawArgs)` 无副作用，可先校验再审批/记工具意图。
- 写/编辑必须由组合根作明确审批；区外写由 `approveExternalWrite` 明确批准后才继续，替代来源完整权限gate。区外读/查找未批准返回Error，尚未执行写入。已知副作用前拒绝使用根 `ToolRejected`；原子替换及写后stat等错误直接传播，不能误报“未执行”。
- Edit按ADR-0011加入读后mtime/size拒绝及写后基线刷新；来源Edit没有此检查，来源Write P2-23断言语义用于最小确认。空 `old_string` 首版明确拒绝，已向主协调说明并获准记录差异。
- 纯Python Grep使用标准库 `re`，schema/工具描述明确实际语法；不支持的JS专属语法报诊断，不宣称完整JS正则兼容。来源17条既有模式均通过。未知参数按首版要求明确拒绝，区别于Zod对象默认剥除未知字段。
- Python JSON整数校验接受数值2.0并转换为int后用于切片，以保持Zod `.number().int()`语义。
- Windows相对查找路径统一为 `/`，使glob跨平台按源码注释定义匹配；目录软链逃逸断言用Windows junction承载。fixture显式写LF原始字节，避免Python默认换行转换改变来源输入。首次偏差失败保留在 `m01-read-write-edit-source`，回修后通过。
- Todo运行状态保存于 `ctx.todos`，避免跨上下文使用来源全局store。完成提醒保留“对照任务原文本身核实证据”，按MVP去掉不存在的verify子代理工具要求；3条相关来源文字断言按这一明确差异适配，未改变提醒出现条件。
- 来源Write中“未提供pendingUnverifiedWrites时绕过护栏”的测试不适用于固定ToolContext（该集合始终存在），单列未迁移；运行产品始终保留护栏。注册表后置MCP/动态激活/延迟工具/子集、英文与predicate接口不在根固定首版API内，未迁移这些断言。
- 图片输入与动态Skills/onFileAccessed后置；Read对图片明确报不支持。没有真实模型调用、真实Windows Terminal操作/缩放或用户体验通过证据。

## 实际命令结果

所有工程命令经清空环境的外层启动器和 `tools/run.py`，使用本工作树私有 `.venv`，合成HOME/配置/临时目录。18个包由只读wheelhouse按 `requirements-dev-win311.lock` 离线哈希安装；无editable安装、无真实账户配置。

- 每个新工具/派发边界先运行来源首条断言，缺失模块red，再构建/安装实现green。逐次回执与原始stdout/stderr见 `raw/m01-{registry,read,write,edit,todo,glob,grep}-{red,green}`。
- `m01-candidate-tests`：构建wheel、强制安装当前产物，再运行9份本票测试和根 `test_mvp_loop.py`，**103 passed**（91来源 + 5必要适配 + 7根循环回归）。可重放构建/安装/pytest脚本为 [build_install_tests.py](build_install_tests.py)。完整argv/环境出口/扫描结果保存在每个 `command.json`。
- 最后合入根 `d31e5e4` 后，按主协调要求仅定向复跑本票已有用例：`m01-final-d31-tests` **96 passed**（91来源 + 5必要适配），工具源码和已通过的Ruff/mypy输入未再改变。新wheel已重建并安装，产物指纹更新为此版本。
- `m01-candidate-ruff`：定向工具源码及本票测试，exit 0。
- `m01-candidate-mypy`：`mypy --strict src/ruocun/tools`，exit 0。
- 早期Ruff两项import问题、mypy一项Match变量类型问题已修复，保留最初失败。合入根的Windows wheel标签变更后，回执脚本一度安装旧py3-none-any产物，导致新增根循环导入失败；已改安装实际py311-none-win_amd64产物，失败与重跑结果均保留。
- 所有回执 `scan_hit=false`。提交前再次审查日志仅含源码、合成fixture和合成路径；`raw/** -text` 保留字节。产物/相关源码指纹见 [artifact.json](artifact.json)，实际wheel保留于本工作树 `dist/` 供独审绑定复用。

## 消费接口

导出：`read_file.readFileTool`、`write_file.writeFileTool`、`edit_file.editFileTool`、`glob_files.globFilesTool`（另保留来源别名 `fileSearchTool`）、`grep_files.grepFilesTool`、`todo_write.todoWriteTool`。

短文件IO在线程执行；取消应设置Event并等待handler真正结束，不能仅取消asyncio task便宣称线程已退出。Bash执行成功后清空 `ctx.pendingUnverifiedWrites` 由Shell负责人接入。

## 独审junction回修

独审先复跑本票96项通过，随后用单个合成workspace/outside/junction复现确认P1：Python 3.11 Windows的junction仍报告 `is_dir(follow_symlinks=False)=true` 且 `is_symlink()=false`；无区外审批时Glob返回 `linked/synthetic.txt`，Grep返回该区外文件内容。来源 `walk.ts` 只进入Dirent普通目录/文件，目录链接应跳过。独审原始回执保存在 `raw/review-m01-junction-boundary-01`。

修复仅修改 `glob.py` 的 `walkFiles`：递归遇到Windows目录时检查 `FILE_ATTRIBUTE_REPARSE_POINT`，跳过junction/reparse目录。显式指定的root仍由上游路径分类和区外审批处理；不改变已批准外部根的访问能力。

复用同一个最小复现 [junction_repro.py](junction_repro.py)，只加独立预期断言，未扩新矩阵。`m01-junction-red` 在修前稳定失败并保留原始输出；回修后 `m01-junction-675-green` exit 0，Glob/Grep均返回无匹配。最初red错误文本受 `-I` 忽略编码环境影响为Windows编码，字节原样保留；最终green显式 `-X utf8` 提供可读回执。

按主协调要求只定向运行受影响的既有Glob/Grep来源断言：`m01-junction-675-source` **29 passed**，未再跑全96或全量。`m01-junction-ruff`、`m01-junction-mypy` 定向检查通过。以上回执均由白名单环境启动且 `scan_hit=false`；已重建并安装合入675f593后的wheel，当前产物/工具源码指纹已更新到 `artifact.json`。此回修仍等待独审复核，不据此前96通过推定新候选已获独审放行。
