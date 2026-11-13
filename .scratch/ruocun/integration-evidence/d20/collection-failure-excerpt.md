# 封存入口误报记录

本轮原生最小组、只读 post-audit 和归档回读均已完成后，附加 PowerShell 组合入口检查失败。扫描脚本实际输出两项 false，但成功路径未显式设置进程退出码，外层以 `$LASTEXITCODE -ne 0` 读取未由该脚本设定的值，错误地抛出 `Sensitive scan failed`。这是独立封存入口的退出状态传递错误，不是敏感值命中、PSEC 失败或测试通过。

该次命令由工具直接执行，没有 stdout/stderr 原字节文件；下列仅为工具返回的输出摘录，不能冒充原字节捕获：

```text
{"has_current_sensitive_environment_value":false,"has_common_token_pattern":false}
Exception:
Line |
   2 |  … s1'; if ($LASTEXITCODE -ne 0) { throw 'Sensitive scan failed' }; Get- …
     |                                    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Sensitive scan failed
```

修正仅为 `scan.ps1` 成功路径显式 `exit 0`；再次扫描仍只输出两项布尔值，无敏感值输出。没有修改原候选75资产、断言、raw、结果，也没有再次运行任何 PSEC/网络/ACL 实验。

随后给全部独立证据设置 `-text` 以保留原字节时，自己生成的顶层 `manifest.json` 和 `scan.json` 使用了 PowerShell 的 CRLF，`git diff --cached --check` 将 CR 视为 trailing whitespace，检查失败并阻止提交。对同一未改 index 仅重读一次该检查，二进制 stdout/stderr 和 exit=2 记录在 `collection/diffcheck-failed.*`，两份当时生成文件原字节保留于 `collection/*-before.json`。修复仅让这两份可再生的顶层元数据使用 LF；历史 raw、测试和业务实验均未改或重跑。
