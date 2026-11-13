# 13 实际方言与执行快照独审

受审产品为 `84b64e2`、`2f0185d`、普通入口 `5bdb63b`，独审树 `116233a`。13 模块及普通入口接缝可集成，剩余审查阻断 0。

审批前生成不可变 ShellExecutionPlan，保存实际 cwd、筛除敏感键后的环境、绝对解释器、argv、native commandLine 与原始命令。Windows 默认 cmd 通过 `/d /s /c` 的原生命令行启动，显式解释器分别分析。ContextVar 将本批候选及批准映射隔离，dispatch 子任务继承既有快照，后续批次换新映射。产品 handler 从权限回调取得同一已批准对象，禁止改 cwd 或消费本批未批准命令。

在途只读审查发现的两条实际身份漏判已在候选中修复。PowerShell AST 的 CommandElements 用于解析 `& cmd /c 'del target.txt'`，内层 del 进入硬 deny。无法确定的 PS 函数、别名、动态 AST 与 native 参数封送保持人工。系统受信 PS helper 只对 stdin 业务文本 ParseInput，没有执行该文本。cmd 首词依据 cwd/PATH/PATHEXT 查实际目标，工作区 `whoami.cmd` 遮蔽不再走只读放行。复杂与包装调用使用 noPersist，仅本次确认的 UI 与 gate 均不接受永久授权。

独立复跑原 n13 计划确认、分类器/权限来源回归、两组 exec_shell 来源测试及既有普通 TTY，共 **186 passed in 14.43s**。覆盖实际中文空格重定向、PS parser 无业务副作用、EncodedCommand/调用运算符内层 deny、工作区脚本遮蔽和旧 dispatch 任务的 ContextVar 快照隔离。受影响 9 个源码 mypy 与定向 Ruff 通过，回执均 exit 0、scan_hit=false。

另外沿既有普通受控 TTY 方式保存单一 [shell-runtime.py](shell-runtime.py) 接线确认。普通入口显示完整原命令及绝对 cmd 路径、仅本次提示且没有 a 选项。人工 y 后实际创建中文空格路径文件，捕获的执行计划证明 argv、原生命令行和 cwd 与批准计划一致。第二条显式 deny 命令没有执行或写文件。脚本通过，原始回执随记录保存。

以上测试仍使用白名单环境、合成 HOME/config/TEMP、独审源码和已锁依赖，没有真实模型费用。14 的增量输出、codec 细分、取消后整树止写及后续后台恢复继续按各票验收，非 Windows 实机与终端最终体验保持未验。
