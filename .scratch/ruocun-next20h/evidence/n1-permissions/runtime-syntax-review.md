# 09 在途独审修正：权限命令的修改语法分类

`isMutatingCommand` 现与同文件 command 的语法一致：`/permissions add|remove` 仅在
kind 为 allow/ask/deny、且 split 后仍有非空 rule 时返回 True；缺 kind、缺 rule 或未知
kind 返回 False。没有增加规则方言约束，也未修改执行命令、排队或 TTY 代码。

原 `test_mode_commands_follow_source_toggle` fixture 增补已发现的错误语法与有效语法分类断言；
`n1-runtime-syntax-review-red` 1 项确定失败，green 1 passed。Ruff 同产品/测试文件通过，
mypy 1 源文件通过。没有新增 pytest case/矩阵、构建或重复 392/162 项。
真实入口的 queued 保留由 root/作者2原 TTY fixture 独立验证，本片不据布尔分类通过声称 TTY 已通过。

产品/测试 SHA 和四项原始命令、stdout/stderr 保存在 `runtime-syntax-review/`。
