# 13 实际Shell方言与不可变执行计划候选

本候选接续24独审通过后的主线，在 `codex/n24-permissions` 实施。13保留 claimed，等待主协调公共入口接线、独审和集成。

Windows按D10恢复cmd默认。默认EXE为已解析的绝对ComSpec或系统cmd，显式非cmd配置拒绝。实际启动采用cmd专用原始native commandLine，保留 `/d /s /c` 与原command的引号语义。实际cwd、脱敏环境、argv、解释器及输出codec保存在frozen ShellExecutionPlan中。非Windows保留原 `/bin/sh` 路由，实机验收仍待后续。

PermissionRuntime在最终参数阶段生成计划，并用ContextVar保存本批不可变映射。只有本批批准的命令进入getShellPlan。独立dispatch任务继承各自快照，后续批次换新映射，旧任务不会消费新批次计划。handler通过ToolContext.getShellPlan取得已批准对象，cwd改变、未获批准或缺计划时在业务进程启动前拒绝。直接调用handler的历史调用方仍可构造执行快照，正常产品入口由主协调绑定权限回调。

cmd采用保守词法与真实cwd/PATH/PATHEXT命中。扩展、CALL/FOR、脚本与未知身份保持人工，读快捷只保留真正cmd内置。显式PowerShell使用同实际受信系统引擎的ParseInput，stdin传入数据，只解析业务代码。EncodedCommand按UTF-16LE解码并显示，CommandElements保留调用运算符后真实子命令。PS未限定函数/别名、动态AST和PS→native封送不明均保持人工。未知不送分类器，复杂/嵌套确认仅本次。项目目录伪装解释器不会在审批前被当parser运行。实际Git Bash payload消费既有Bash AST，WSL、login/profile注入或解析不可用保持人工。

硬deny对已解析的完整包装链逐层匹配，Windows命令名称/拒绝目标按大小写不敏感保守处理，实际根路径删除/磁盘操作维持危险强确认。审批与写/执行审计均展示同计划的解释器、完整原command和解码内层脚本，叠加既有凭据脱敏。

验证沿用冻结权限及exec_shell来源断言，Windows原测试只将旧默认PS语法改为显式PS，未删除断言。必要适配确认覆盖cmd默认native line、中文空格重定向、PS内层deny与parser不执行业务输入、ContextVar批次隔离、cwd脚本遮蔽及PS调用运算符的独审最小复现。

- n13-plan-red记录缺模块失败，n13-plan-green1为初始闭环通过。
- n13-final-plan1捕获合成PATH缺PowerShell解析器的原失败，测试改为实际系统EXE。
- n13-shell-regression1保留4个旧默认PS语法失败。显式解释器适配后，regression2保留重复权限parser导致旧3秒断言失败。执行入口复用计划后，regression3通过全部34项。
- 独审指出的PS调用运算符和cwd脚本身份缺口已回修，8项plan确认通过。
- 最终n13-submit-r1为185项通过，n13-submit-mypy和n13-submit-ruff通过。

所有检查均经tools/run.py白名单环境、合成HOME/配置/临时目录，源码从本worktree/src加载，未调用真实模型。原始失败及修复回执保留在raw，日志秘密扫描为false并经人工查看。来源与产品哈希见manifest。

本票尚待正常产品入口独审。14负责增量输出、codec细分、前台取消及其它执行边界，当前cmd的OEM与原生子工具输出组合尚需该票逐项核验。15及后台恢复未启动。
