# 70 命令目录/解析/帮助切片

从含70正式领取记录631fbc44的主线合并后实施。候选目录/parser为0f7bf3b0；不改runtime/cli/loop/全局票，实际动作/入口与最终接线由root验证。本材料不把帮助文字算成功能实现。

目录采用模块对应表CMD-*及n70-command-inventory.md已核的52个固定历史名称，包含accounts/yolo/task/quit原别名和范围外plugin来源记录。公开目录过滤plugin后51项；解析器不自动改写名字或别名，保留Config大小写，未知合法名字交调用方提示。未把App补全菜单里仅以Skills fallback可达的security-review/debug-session/dod当成新增固定路由。

词法规则直接依据冻结src/commands/commands.ts:16–28、commands.test.ts:195–217和index.ts:1917–1920：trim→首段ASCII `[a-zA-Z0-9:_-]+`→空白折叠参数。空/非slash/含斜杠或点的绝对路径返回None；大小写不归一，合法未知名字仍是命令。`parseSlashCommand(text)->(name,argsstr)|None` 不掌握权限、暂停或运行状态。

2个压缩来源用例 missing-module red→green；Ruff/Mypy单文件0，完整工具白名单argv和合成HOME在raw/command.json。仅此切片定向，没有重跑42/57、没有全量/构包。

## 冻结 CLI oracle 与待组合决定

`cli_oracle.py <node.exe>` 从冻结ZIP只读src/index.ts，仅取原argv表达式块，使用Node v24.15.0执行11个合成参数排列。没有启动DAO主入口/模型/工具；权限提取器在这些不含权限参数的案例中用identity替身。完整src/index.ts SHA256和实际结果在cli-source-oracle.json。它证明冻结表达式的行为，不冒充完整来源CLI/TTY运行。

| 合成输入 | 冻结表达式实际行为 | 组合根需保留或明确登记的边界 |
|---|---|---|
| `--unknown hello` | prompt为`--unknown hello` | 未知flag是prompt，不按argparse一律拒绝 |
| `--Model same hello` | prompt完整保留，未设置model | flags区分大小写，不增大写别名 |
| `--model`、`--provider`、`--api-key`单独出现 | 对应值undefined，prompt空，不在此层报缺值 | 与权限提取器强制参数规则分开；后续账户/模型校验不是该表达式结论 |
| `--model --obs hello` | model实际取`--obs`，该布尔flag仍启用 | 标记和值重叠是原行为，不凭常规CLI习惯推测 |
| `--model same say same` | prompt变成`say`，重复的same全部被Set过滤 | 来源会吞掉真实prompt词；root若修成只消费参数位置，应记具体缺陷差异，不能谎称逐字一致 |
| `-c synthetic-session synthetic-session hello` | prompt变成`hello` | 相同Set问题也适用于显式恢复ID |
| `-c --unknown hello` | 最近会话恢复，prompt仍为`--unknown hello` | -c仅取紧跟且不以`-`开头的ID |
| `--model=same hello`、`-- hello` | 两者均进入prompt | 来源没有通用等号参数/结束选项约定；RuoCun自有扩展参数另列 |

source index.ts:871实际为`!no-progress-advice && !interactiveSession`；`--progress-advice`本身仅从prompt过滤，不单独强开TTY。该事实已同步root和B；不是本切片修改进度算法。

## 帮助差异

保留原有账户/输入/权限/记忆/后台/源码说明，补/help、doctor、agents、51条公开目录、大小写/路径规则、临时key/provider、verbose/debug、两类反思、可选HTTP观测、progress/eval及独立禁用、Skill add操作员入口和quit keep-background。显式区分Schedule系统crontab与会话内loop、Deck/沙箱尚未交付、Windows无来源OS沙箱、最终体验单列。root需在70/71对应实际入口接通后消费这些帮助，不能用此文本替代消费者验证。
