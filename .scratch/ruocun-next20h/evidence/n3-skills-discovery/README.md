# 35 动态 Skills 模块候选

基线 `5afc65f9233ecc2cd153b2124673ff088395653a`。来源为唯一冻结 DAO `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`。模块和测试的工作区字节、冻结源字节见 [source-members.json](source-members.json)。普通入口由主线接入和验收。

## 来源行为与接口

- `skills/discover.ts`、`index.ts:819–845,1167–1194`。启动扫描保留 4000 文件上限。预命中副本去掉 `paths`，其余条件项进入每会话待激活池。文件访问从嵌套目录向上发现，不含 cwd，跳过 `node_modules`，只缓存存在目录。多目录从深到浅交给来源同序的 `loadSkills`。后传覆盖前传，所以同批深浅同名实际由浅层胜出。新发现的嵌套项保留来源直接可用的行为，即使它含 `paths`。发现时按现有活名单排除同名技能，并在活列表和待激活池按真实文件去重。待激活项与不同物理文件同名时各走发现、激活分支，沿 `index.ts:1174–1187` 的来源顺序。
- D09 与 S-03。自动探测原生嵌套 `.ruocun/skills`，旧品牌嵌套 `.dao/skills` 仅接受本项目源映射的精确路径。加载动态正文前核对目录及文件解析后的路径。冻结 `index.ts:320–322,768–773,1169` 只关闭了启动磁盘加载，动态回调仍可发现，这是静态来源隔离缺口。会话 `disk_enabled=False` 关闭整个磁盘发现/激活通道，显式 `disabled=True` 同时关闭 core。兼容源只读。
- `loadRuntimeSkills(..., discovery=...)` 返回同一活列表类型，给实例初始化待激活池。`await discovery.prepare(paths, active, disabled=...)` 返回新发现项、已匹配候选和按来源顺序生成的尾部 system 目录文本。放弃提案不消耗待激活项和正目录缓存。主线在真实工具配对与图片投影完成、活代次有效时确认尾部目录，随后调用 `discovery.confirm(candidate, active)` 发布。手动专用正文、静态兼容顺序、固定系统前缀和会话记录分别沿现有入口。
- `skills/usage.ts` 与 `index.ts:847,1154`。`recordUsage`、`usageScore` 同步，使用次数乘以七天半衰期系数，下限 0.1。冻结普通目录没有调用 `usageScore` 重排。`loadUsage`、`saveUsage` 通过线程读取/发布原生 `skill-usage.json`。加载损坏状态返回空视图，保存重新检查并保留坏原件。结果 `saved` 表示确认发布，`failed` 表示写前失败，`unknown` 表示结果无法确认。调用方遇失败/未知停止该次记账，不自动重复写。用量保存与工具结果独立。
- `tools/skill.ts:41` 在找到 Skill 后、适配正文前调用 `recordSkillUse`。`index.ts:1154` 更新用量并记 `loaded`，`skillRound` 初始 0，`index.ts:1853` 的 Ink 用户消息消费点递增。主线给普通入口按实际消费的用户输入提供轮次和 UTC 日期。`createSkillAuditSink(sessionDir, env).loaded(round, name)` 同步写 `skill-trace.jsonl`，开关为 `RUOCUN_SKILL_AUDIT` 优先及 DAO 后备，细流覆盖总开关。来源统计按不同加载轮数、总次数排序，忽略旧 offered/activated；只含实际加载名、轮号、时间。

## 自动证据

复用冻结 `discover.test.ts` 15 项、`usage.test.ts` 2 项和 `skill_audit.test.ts` 4 项。加入一个必要装配用例覆盖 S-03、已声明与未声明目录、同名来源顺序、放弃提案与确认。原用量累加用例同时确认 Windows 原生原子保存和坏原件保留。复用原静态加载 14 项。

| 回执 | 实际结果 |
| --- | --- |
| [来源 red](raw/n3-35-source-red/command.json) | 2 个模块缺失，收集失败 |
| [首次来源 green](raw/n3-35-source-green/command.json) | 36 passed in 0.58s |
| [完整定向回归](raw/n3-35-source-final-02/command.json) | 36 passed in 0.49s |
| [末次受影响定向](raw/n3-35-affected-final/command.json) | 22 passed in 0.29s |
| [发现同名收口](raw/n3-35-discovery-final/command.json) | 16 passed in 0.21s，发现模块 Ruff/mypy 通过 |
| [Ruff](raw/n3-35-ruff-final-02/command.json) 与 [末次 Ruff](raw/n3-35-audit-static-final/command.json) | 通过 |
| [mypy](raw/n3-35-mypy-final-02/command.json) 与 [末次审计 mypy](raw/n3-35-audit-mypy-final/command.json) | 5 源及受影响审计源通过 |

首 Ruff 导入排版、首 mypy 显式类型导入/浮点运算，以及调整导入路径时的中间错误均保留原回执。所有回执使用白名单启动器、私有 CPython 3.11 和合成目录，敏感扫描均为 false，进程已收齐。主线固定产物和真实普通入口证据另记。

## 独审回修

冻结 `index.ts:1170–1193` 分别处理目录发现与条件池匹配。源装配用例追加单个目录项 stat 拒绝，确认发现失败后匹配项仍可进入候选。审计原用例追加一行坏 UTF-8，按冻结替换解码和逐行解析保留合法记录。复用两个现有用例，先 [2 failed](raw/n3-35-isolation-red/command.json)，修后 [2 passed in 0.17s](raw/n3-35-isolation-green/command.json)。[mypy 两源](raw/n3-35-isolation-mypy/command.json)及 [末次 Ruff](raw/n3-35-isolation-ruff-final/command.json)通过。原候选字节记录继续指向初版，回修字节由本次提交固定。
