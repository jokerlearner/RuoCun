# M02 — 前台Bash与受管进程树取消

Type: task
Status: resolved
Assignee: /root/mvp_shell
Branch: codex/mvp-shell
Worktree: .worktrees/mvp-shell
Blocked by: none（共享声明已固定；不等待后置持久runner）
用户体验验收：not-required

结果：8b76ee1已独立复核并集成；28项定向独审通过，真实子/孙句柄signaled后返回。普通CLI native输出问题经单变量确认属于合成父环境漏PATHEXT，产品叶子未改，详[诊断](../evidence/m02-shell/native-stdout/README.md)。仅关闭首版前台Shell子集，完整后台/沙箱母案例未完成。

按[首版规格](../spec.md)迁移冻结exec_shell前台子集；工具名Bash，实际Shell方言/argv/编码可解释。signal为ToolContext.threading.Event，真实受管子孙停止后才报告取消；background=true明确拒绝。复用来源已有输入/预期和既有Windows最小探针，保留必要进程树确认，不做新压力矩阵。

独占exec_shell.py与process_tree平台叶子及对应测试/证据；不改types.py、registry、loop、cli或07私密文件。与M01接口并行，源码/证据提交后独立审查。所有自有子进程须回收，合成cwd与环境白名单必需；不得运行旧相对句柄探针。

## Comments

2026-11-10：首版前台候选已实现，基线e672f7201a9db371c1bcf7b7cb22fa9cf5e707ab；代码/来源/原断言/安装绑定与失败原字节见[M02证据](../evidence/m02-shell/README.md)。最终定向回归28 passed、Ruff/mypy3文件及wheel/sdist构建通过；真实自有Python子进程及孙进程取消后句柄signaled，所属工程进程无遗留。先发现并最小修复Job计数归零不等于进程对象signaled的已确认缺陷，同一复现及原失败保留。

Shell方言固定Windows PowerShell5.1并明确UTF-8，background=true拒绝。来源sleep/内联脚本/数据库备份/pending反馈/崩溃重新规划护栏保留。主协调已确认两处必要可见差异：取消后包管理恢复需要新审批；首版保留自动备份，不按路径扫删归属不明的备份。38项来源原用例不宣称全量通过。状态仍claimed，待独立复核/集成；真实模型、真实Windows Terminal及Linux/macOS未验。共享对应表与验收矩阵由主协调收录MM-636/MM-637、TOOL-Bash首版部分，不关闭完整Shell母票。
