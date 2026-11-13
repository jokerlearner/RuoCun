# 15 独立审查：源码候选

独审分支 `codex/n24-review`，源码候选与主协调 `8415581` 对齐后，收录长路径 `a295c70`、`c999e77`，unknown 关闭 `04a6f5e` 与普通入口 notice `5048b4d`。只补独审证据，不修改产品。

结论：下述已核范围剩余阻断为 0，可以进入固定包验收。15 整票仍须固定同包安装出口；Windows Terminal/IME/缩放与用户体验没有据此验收，16/17 没有据此完成。

## 实际运行

所有命令由 `tools/run.py` 的明确环境白名单启动，HOME/配置/TEMP 合成，未请求真实或付费模型。以下各组有重叠，不相加成独立测试总数。命令、stdout、stderr 在同名 `raw/` 目录；均 exit 0、敏感值扫描 false。

| label | 实际结果与范围 |
| --- | --- |
| n24-review-managed-shell | 39 passed in 44.75s；15 来源生命周期、存储、14 输出、原 Shell/Windows Shell、双语工具来源契约 |
| n24-review-managed-shell-mypy / ruff | 10 源文件无类型问题；Ruff 通过 |
| n24-review-runner-owner-kill | 真实 DB owner 被强杀，runner 存活，新 owner 同 run 接管与取消、真实 receipt/Job 止写、原 ack 保留全部通过 |
| n24-review-long-path | 22 passed in 35.46s；私密文件/重解析竞态、长目录原子写与 ACL、普通七工具与保存重开 |
| n24-review-long-path-mypy / ruff | 3 源文件无类型问题；Ruff 通过 |
| n24-review-close-final | 4 passed in 19.74s；两种未知关闭、真实取消及坏附件关闭、原普通 TTY |
| n24-review-close-final-mypy / ruff | 3 源文件无类型问题；Ruff 通过 |

## 同 run 强杀接管

复用 `tests/test_n15_managed_shell.py` 既有受控 SQLite 与生命周期辅助函数，脚本为 [runner-owner-kill.py](runner-owner-kill.py)。source 模式显式 source role loader，不能据此声称默认安装 `-m` 已验。

从实际存储 owner 的 `ProcessIdentity` 取得 PID/creation，保留 HANDLE 并核创建时间后强杀、等 HANDLE signaled。本次 launcher 的 PID 确为 shim，未把 launcher 退出当作真实 DB owner 退出。另保留真正 runner HANDLE，确认 owner 死后仍活着。

新 Conversation 获得更高 owner epoch，manager.restore 获得更高 control epoch；RunRef、runner 身份、start.claim SHA256 与一次启动计数不变。恢复前保存的真实工具 ack 未被恢复提示覆盖。随后同 run cancel，等待真实 canceled receipt、日志摘要与终态文件，真实孙进程 ticks 停写，runner HANDLE 最终退出。没有把已发送取消请求等同停止成功。

## 长路径边界

`durable_file` 将本地长盘符路径统一成扩展路径；已有扩展本地路径幂等，短路径保持短表示，扩展 UNC/设备名仍拒绝。本地固定卷与逐级 reparse 拒绝保持，NT 打开仍带 `OBJ_DONT_REPARSE`。创建目录、ACL、私密读取、原子发布、Flush 与 Python I/O 使用同一表示；manager/runner 比较路径时同样规范化，消除重开时别名不一致。

原长路径用例及原 junction 跨进程竞态已运行；普通七工具原断言含真实 Bash 和正常保存重开已通过。未新增网络共享支持或放宽设备/reparse 规则。

## unknown 关闭与普通入口

`cancel` 在控制前核私密文件、capability、签名 manifest、原 runner 身份和当前 owner/control epoch。缺认证或坏终态不写 cancel_requested/cancel.json，不伪报已经请求。已知终态不降级；unknown 留原现场，并由 close 返回 notice。无法确认停止仍是 unknown。

普通 runtime 在 broker 关闭和已有输出 drain 后直接打印 `conversation.redact(notice)`；不再向已关闭 broker 排队输出。KillShell 的 reason 明确“未发送”，避免假成功。后台 running 的稳定 task id ack 是已批准语义，只有 manager 已核真正 start/claim 才能给出；unknown 不补造 ack、不重放原执行。

固定安装包实际入口复核另见后续纯安装报告。
