# A02 静态 Skills 交付证据

范围为 ADR-0012 / 阶段A 的静态子集，原34、70不因本批局部自动通过而 resolved。实现者工作树为 `.worktrees/advanced-skills`，分支 `codex/advanced-skills`，起点 `0b9537ab9849ccad610a482d1eab408393c37eef`；已快进合入主协调指定稳定提交 `fa5815ac0202418b98ad184c8fd6eef9734f688e`。公共类型、配置来源装配、CLI和提示接线由主协调拥有，本分支未修改。

## 来源与原文

- 统一冻结快照 `dao-f17e189-7ac654a0dc06`；source.zip SHA-256 `1f8308959d8b9ac0783b6ce6ddbffe7a71cc60bc59332f309f0d62083efac078`。`capture_source.py` 校验归档7项checksum，并核对所用6个展开源码/测试/LICENSE与ZIP成员原始字节相同；完整hash见 `source-receipt.json`，原字节保留在 `source/`。
- core正文实际定义于冻结 `src/skills/bundled.ts`，并非8个源Markdown文件。`core-golden.json` 从该源文件独立提取运行时模板文本：JS模板换行归一为LF、`\``转成反引号；本源没有其它转义或插值。原TS文件字节和运行时body是两个不同的校验对象。`materialize_core.py` 只从golden写入产品资源，不用模型改写，不安装新技能包。
- 8个产品Markdown不增添末尾换行、正文逐字保留，包括原DAO路径及工具/子代理名称；不能据这些引用宣称当前RuoCun已经提供所引用能力。8段body、description、顺序、core标记与独立golden完全一致。MIT原许可在产品资源与证据中均保留；全项目归属由现有NOTICE/LICENSE承担。

## 可消费接口

- `await loadSkills(*dirs: str | Path) -> list[Skill]`：仅读取显式目录；兼容`<slug>/SKILL.md`和扁平`<slug>.md`，后目录覆盖同name，先按realpath去重；不存在或不可读目录/文件沿来源忽略。用户/项目/兼容源的装配仍由组合根决定，不查真实HOME或自动读`~/.dao`。
- `skillCatalogLines(skills)`：只列modelInvokable不为false的元信息，保留namespace调用名及220个UTF-16 code unit描述预算；不注入正文。
- `findUserInvocableSkill(skills, name)`：按slug/name/namespace:slug选首个用户可调用项。
- `BUNDLED_SKILLS: list[BundledSkill]`：原8core的name/description/body/core；组合根需要补`dir=''`和`slug=name`，并处理磁盘覆盖/禁用。
- `skillTool: Tool`：`read/auto`，必填name、可选args；匹配优先级namespace:slug→精确name→大小写不敏感name→slug。返回来源标题/资源目录/用户参数/正文/执行约束；调用可选使用计数与适配回调，但本批未提供自动转换器。描述及返回尾部添加当前能力说明，引用其它工具须以当前列表为准，用户选项/确认走当前文字交互入口。
- frontmatter沿来源的逐行标量子集；保留when_to_use三个别名、paths简单分隔及调用开关别名，未引入完整YAML。paths仅解析，条件激活由后续功能处理。

## 验证

所有Python、Git变更、构建和验证命令均经指定外层启动器与`tools/run.py`，Python 3.11固定`-I -X utf8`，私有`.venv`，18包hash锁与只读wheelhouse，合成HOME/config/session、明确环境白名单。每次测试消费非editable的`py311-none-win_amd64` wheel，未误装旧any包。命令索引为 `command-index.json`，原始失败/输出及回执在 `commands/`；生产测试没有读取真实用户状态，没有调用真实/付费模型API。

逐片TDD共13组`skills-sliceNN-red/green`，从缺失公开API、缺失字段/匹配分支到通过，未删除原失败。随后补入已由现有实现满足的适用来源断言，并如实记为直接通过，未伪造red。

| 来源/确认 | Python断言 | 结果 |
| --- | --- | --- |
| skills.test.ts：3条catalog、6条load/find | `tests/test_advanced_skills.py`，9项 | 通过 |
| skills.test.ts：4条Skill工具 | `tests/test_advanced_skills_tool.py`，4项 | 通过 |
| bundled.test.ts：6条8core | `tests/test_advanced_skills_bundled.py`，6项 | 通过 |
| 原34要求的完整正文/元信息golden | 同bundled文件，1项 | 通过 |
| 定向Ruff与3个产品文件mypy | `skills-ruff-01` / `skills-mypy-01` | 通过 |

共20项定向测试通过。目录链接fixture在Windows用junction适配来源symlink，不需要额外符号链接权限；非Windows保留symlink分支，未作实机验收。另有一次证据收集脚本首次把自身尚未生成的回执纳入扫描而失败，已修正为忽略当前未完成命令；原失败日志保留，它不是产品失败。

最终固定wheel、候选源码/hash绑定、重跑与仓库外最小资源/参数/目录包装确认在最终回执中记录。该最小确认是Python交付适配，不冒充新增DAO来源测试。未验项为主协调集成接线、完整CLI/TUI及真实Windows Terminal缩放/用户体验；真实模型调用为0。动态paths激活/安装/插件/第三方自动转换/完整TUI均未在本批实现，不声明通过。

最终候选绑定源码提交 `5c5e85fa94a4101e6c81d52d5d3079aeb9c7e8ff`，产物位于本工作树 `.cache/candidate-dist/ruocun-0.1.0.dev0-py311-none-win_amd64.whl`，SHA-256 `9e3d38d15473113fdcd035e6abde4f06e79bc6d0ee50a02c58f7e627f1c68107`。`candidate-receipt.json`逐成员绑定wheel、已提交源码和独立非editable安装内容，全部产品成员字节一致；后续提交只补本证据。候选重跑20项通过，定向Ruff/mypy通过；`skills-candidate-installed-smoke`在合成临时目录cwd确认已安装包的8core原文、显式目录覆盖及body/args/资源包装通过。

第一次Git提交因白名单环境没有用户全局身份而失败，保留失败记录；修复是该次命令临时使用合成`Codex <codex@local.invalid>`，没有读取真实HOME或修改用户配置。Git失败的自动身份探测信息含本机hostname，原始日志隔离保留在本工作树`.cache/sprint-root/raw/skills-commit-source/`，入库/展示的stderr仅将该自动身份替换为`<redacted-host-identity>`，其余字节和失败状态保留。
