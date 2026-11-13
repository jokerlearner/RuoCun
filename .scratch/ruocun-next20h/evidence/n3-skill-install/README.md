# 36 技能安装及适配模块候选

领取基线 `25bb8c0df59d15c4ea5ceb95c3f8370ab684dfcc`，共享参数入口与回调 `64efcec16b868352a2dfb5e94582c61d5200e6d0`。唯一冻结 DAO `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb` 的来源和候选工作区字节见 [source-members.json](source-members.json)。

## 安装与确认

- `skills/install.ts` 及 `tools/skill_install.ts`。`makeSkillInstallTool(user_root, run_git=...)` 创建 exec/required/deferred 工具。`source` 必填非空，`scope` 可选，缺省 user。受控 `run_foreground_argv` 使用绝对 Git 可执行路径、字面参数和本轮 Event。HTTP(S)/git@ 拉取到独有临时目录，优先仓库 `skills/`。本地源按工作区解析，递归遇 `SKILL.md` 停止，按来源前导 `---` 检查。源正文、嵌套目录及二进制资源按字节读取复制。
- D09 路径边界。只向原生 userRoot/skills 或项目 `.ruocun/skills` 发布。目标与源不能重叠，原生根和资源树拒绝链接或重解析点，避免复制超出技能树的内容。导入时排除 Git 行政元数据，已安装目录的旧资源在同名合并时保留。
- `installSkills(...)` 返回 `InstallResult`，记录确认的安装目录名、跳过说明和已知失败。完整候选在可见技能根外同卷暂存，文件和 Windows 目录同步后交换。同名安装先备份完整旧目录，确定新目录移动失败时恢复旧目录。已确认的前序安装保留。结果不明抛 `InstallUnconfirmed`，留本次暂存供核对，由既有 exec 未知结果规则停止。取消在准备和发布前检查，已进入目录交换的操作完成确认后报告实际结果。
- 工具只为已确认的安装同步登记 `ctx.onSkillsInstalled(scope)`。主线在工具配对确认后刷新会话目录并持久化尾部消息。工具回执先报告安装，不提前声称会话已加载。这里提供工具入口，独立操作员 `Skill add` 未加入本票。

## 适配与缓存

`makeSkillAdapter(daoTools=..., catalog=..., callFlash=..., userRoot=...)` 返回异步正文适配器。沿 `adapt.ts` 的工具语境和命名空间识别，原生技能正文直接返回。外来正文使用真实工具词表，缓存键沿 `convert.ts` 的 `inherit-model-v2`、词表及正文 SHA-256 前 16 位。缓存只写原生 `skill-adapted`，不改源文件。异常或空答返回原文与通用提示。模型档位默认继承主模型，当前工具表提供 agent 时才允许转成子代理调用。受控用例由注入的合成回调返回正文。

## 自动证据

复用冻结 `install.test.ts` 2、`skill_install.test.ts` 2、`adapt.test.ts` 6、`convert.test.ts` 7 项。原本地用例同时确认二进制资源、源保留和同名旧资源。新增最小 Git 参数与同名发布回滚各一项，使用合成目录及受控 runner。真实主线刷新、模型与固定包由相应出口另行记录。

| 回执 | 结果 |
| --- | --- |
| [来源 red](raw/n3-36-source-red/command.json) | 两个模块缺失，收集失败 |
| [原来源及必要适配](raw/n3-36-source-green-01/command.json) | 19 passed in 0.31s |
| [末次安装定向](raw/n3-36-install-final/command.json) | 6 passed in 0.22s |
| [Ruff](raw/n3-36-ruff-01/command.json)、[mypy](raw/n3-36-mypy-01/command.json) | 通过，mypy 4 源 |
| [末次 Ruff](raw/n3-36-ruff-final/command.json)、[末次 mypy](raw/n3-36-mypy-final/command.json) | 通过，mypy 2 源 |

所有运行经白名单启动器，使用私有 CPython 3.11、合成 HOME/TEMP，敏感扫描均为 false。受控 Git 确认正常暂存已清理，同名回滚确认完整旧目录和仅原目标可见。

## 独审路径回修

复用原安装和缓存用例覆盖三处已复现问题。Windows 按平台文件名比较排除 `.GIT`，完整复制仍包含普通资源。本地显式源在解析前核验根身份，并拒绝经祖先别名重定向。缓存读取复用 `PrivateDirectory` 只读文件锚，缓存目录重解析时按未命中继续正常适配，外部字节保留。测试使用合成真实 junction，结束后只移除该别名。先 [3 failed in 0.49s](raw/n3-36-path-review-red/command.json)，修后 [3 passed in 0.40s](raw/n3-36-path-review-green/command.json)，[Ruff](raw/n3-36-path-review-ruff/command.json) 与 [mypy 两源](raw/n3-36-path-review-mypy/command.json)通过。初版候选哈希保留，回修字节由本次提交固定。
