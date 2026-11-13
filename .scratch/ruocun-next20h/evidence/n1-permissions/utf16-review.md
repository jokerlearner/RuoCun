# A 独审修正：私有 glob 的 JS UTF-16 匹配单位

冻结 `new RegExp` 未带 `u`，`?` 匹配一个 UTF-16 单元；Python 默认匹配一个 Unicode
码点，会把 `Read(secret?.txt)` 对 `secret😀.txt` 的 allow 拓宽。本次仅把私有规则 glob
的 pattern 和待匹配文本转换为 UTF-16 单元序列，不替换方言、不改其它工具 glob。

复用既有 `rule_matches` 参数用例中的路径断言，red 确定失败后修复为 19 passed / 31 deselected；
Ruff 与 mypy 1 源文件通过。命令、原始输出和产品 hash 见 `utf16-review/`。
