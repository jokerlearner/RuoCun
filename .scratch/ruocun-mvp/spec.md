# RuoCun纯Python编码首版

Status: implemented / automatic-passed / human-pending
启动：2026-11-10 21:01:03 +08:00。基线：01e4606bc8fbb4f2df3394b7bc8926ad015be721。
唯一范围：[ADR-0011](../../docs/adr/0011-python-coding-mvp.md)。用户已明确开始，不重复请求需求确认。

自动技术出口：r2固定代码1ad72d6，**601 passed / 3 deselected**；五项工程入口通过，源码/安装/wheel64成员及固定SQLite绑定通过，独立Standards/Spec剩余产品问题0。仓库外纯产品环境验证七工具、拒绝、普通两轮交互、保存重开及程序内SIGINT。实际console launcher在本机Temp路径受应用控制WinError4551阻止，准确记ENV，模块入口`python -m ruocun`通过。真实模型与真实Windows Terminal/用户体验仍pending，不回填accepted。

交付：[启动](../../docs/mvp-start.md)、[M03原始结果与产物](evidence/m03/README.md)、[M04独审](evidence/m04/README.md)。旧82票与原参考技能保持，后置功能未自动开始。

## 交付与最小验收

1. 已安装的ruocun使用显式选择的配置账户/模型，在工作目录逐轮文字对话，支持一次性任务与交互式多轮；使用已有Chat/Responses路由和重试，不借合成demo冒充普通产品入口。
2. 模型实际调用Read/Write/Edit/Glob/Grep/Bash/TodoWrite，能读取代码、修改文件、执行测试、读取结果后继续回答。schema/参数/所选行为沿冻结DAO；只注册实际实现工具，首版文本文件优先。
3. 写入、编辑、Shell执行前展示操作并文字确认，拒绝不执行；工作区外访问有明确审批。源码中的读取/修改基线等护栏保留，复杂权限规则及auto分类不宣称支持。
4. 同时只运行一个前台任务，不接忙时排队。Ctrl+C取消模型请求及受管Shell子孙进程，真实退出后才报告取消，不留下所属工程进程；不提供后台模式。
5. 复用唯一StorageWorker：保存已确认消息/工具配对、累计token和owner/revision。正常退出后新进程恢复同一会话；未知副作用明确阻塞，不自动重放。历史分模型费用按R1不保证完整，费用摘要真实。
6. 不自动压缩/蒸馏；上下文过大或供应商明确返回上限时停止继续请求，保留记录并提示新会话。不能仅靠字符估计宣称精确token容量或静默截断。
7. wheel/sdist构建与仓库外安装、版本/帮助/基本用法及数据位置说明可用。运行库必须沿07的实际SQLite固定组合，不静默降级。对应DAO测试及必要工程检查通过，真实模型/真实终端未做部分如实记录。

## 文件归属与任务

| 任务 | 当前负责人/分支 | 独占文件 | 状态 |
| --- | --- | --- | --- |
| M01 文件工具 | /root/mvp_files，codex/mvp-files | tools/read_file.py、write_file.py、edit_file.py、glob.py、glob_files.py、grep_files.py、todo_store.py、todo_write.py、paths.py、schema.py、registry.py及对应测试/独有证据 | resolved（首版子集） |
| M02 前台Shell | /root/mvp_shell，codex/mvp-shell | tools/exec_shell.py、platform/windows/process_tree.py、platform/process_tree.py及对应测试/证据 | resolved（首版子集） |
| M03 主循环与CLI | /root，integration/ruocun-migration | agent/loop.py、agent/runtime.py、tools/execute.py、tools/types.py、cli.py、基础会话接线、README/help/必要包资源 | awaiting-user（自动通过，体验pending） |
| M04 独立复核与安装 | /root/mvp_review，codex/mvp-review | 独立证据；不修改产品掩盖失败 | awaiting-user（自动技术出口；人工pending） |

M01/M02沿唯一tools/types.py契约独立开发；M03可用已声明接口迁移来源循环断言，实际接线必须消费已提交并复核的实现。M04核对M01–M03、复跑对应来源测试及最小安装/取消/保存重开，失败返回原负责人。各票保存来源、代码SHA、命令结果、未验项；原82票不因MVP子路径通过整票resolved。

## 共用接口

Tool为name/description/schema/capability/approval/async handler；schema是来源Zod对应JSON Schema，先校验再调用。ToolContext使用来源camelCase字段，signal适配threading.Event，mtime为stat毫秒。handler(args,ctx)返回字符串；Bash拒绝background=true。注册表接口固定为register(tool)、get(name)、toApiTools()、async dispatch(name,rawArgs,ctx)；后续确有需求由单一所有者兼容扩展。

独立worktree可复用自己的venv/公开hash缓存，HOME/配置/会话按本批合成隔离。工程命令通过tools/run.py与清空环境的外层启动器，不直接继承真实账户配置；不运行旧异常探针。固定普通候选一套产物供源码/hash绑定后复核，代码变化必须更新安装产物。保留原始参考技能/许可、旧工作树和失败证据。
