# A04 独立审查

当前独立技术结论：阶段 A 固定 r2 `bccbb57062a5518aad8ee4882eae4a1eef3429e6` 的双轴复核、固定产物绑定及仓库外纯产品/账本确认通过，原四项 P2 已关闭；真实模型、Windows Terminal 和人工体验仍 pending。独立审查者 `/root/advanced_review`，分支 `codex/advanced-review`，初始起点 `0b9537ab9849ccad610a482d1eab408393c37eef`，开始时工作树干净。未改产品实现、旧 82 票或首版人工状态。下文按真实审查顺序保留准备、失败、回修及通过证据；全量/最终公共出口由主协调汇总。

## 准备证据

- 已读 AGENTS、CONTEXT、ADR-0005/0009/0010/0012、阶段 A 规格、原 08/28/29/34 票、冲刺/实施记录及 D09 唯一契约。
- 固定来源归档 SHA256 为 `1f8308959d8b9ac0783b6ce6ddbffe7a71cc60bc59332f309f0d62083efac078`；只读展开目录为原 `b01-tools/.cache/frozen`。本轮实际读取的 13 个相关来源成员与归档 manifest 的哈希全部一致，见 `preparation-binding.json`。
- 新建本树独占 `.venv`，实际 CPython 3.11.9 x64；按 `requirements-dev-win311.lock` 的 18 包哈希锁、只读 `wb-i06/.cache/wheels` 离线安装。锁 SHA256 为 `374c1af75ffda3ce284f2a5d2e6cd67af953cbd4133f1b929f8153f0dc8dc0af`。
- 三次准备命令均经外层清空环境启动器和 `tools/run.py`，HOME/config/TEMP 为合成状态；exit0、scan_hit=false。实际解释器/安装版本在 `raw/a04-prepare-environment-01/stdout.bin`；回执和原始字节保留于 `raw/`，使用 `-text`。
- 尚未安装阶段 A 产品、运行来源断言或构建产物；最终候选将先绑定源码提交、固定产物哈希、包成员与实际安装，再复用该不可变产物进行必要确认。

## 已交主协调的持久化接缝

唯一声明仍为 `session/contract.py` 的 Checkpoint；唯一写线程仍为 StorageWorker。`enqueue_checkpoint` 在接受请求前深拷贝候选数据并固定 digest，返回可查询状态/操作 ID 的 CheckpointHandle；取消 wait 不会撤销已接收的事务。压缩应以 prepare → 提交候选 → 确认后交换内存为顺序；未确认时不能继续副作用或把取消当回滚。

基线 Conversation.save 从当前 messages 中的 user 消息重新构造 accepted_inputs；压缩会使该方法删除原已确认输入并重新编号。主协调已确认采用独立的已确认输入账本和显式新输入登记，压缩后的 messages 只作为模型投影；无需另建 schema/数据库。新接缝候选须先独审，再让摘要路径消费。

Conversation.open 已对未决工具、待投递事件、缺失附件及 unknown run 阻断继续；压缩不得绕过此门槛，也不重放 journal。R1 恢复四项历史 token，但分模型费用仅当前进程，摘要、费用和预算必须准确说明不同统计范围。

Q2 压缩失败行为仍等待用户决定；本审查者没有替用户选择。真实模型/付费 API 调用 0 次；真实 Windows Terminal 与人工体验保持 pending。

## 输入账本接缝：通过，可供压缩接线消费

候选 `fa5815ac0202418b98ad184c8fd6eef9734f688e`，独立合并点 `bfced85cdae92a40498682459cc89cb326fb30e1`；产品目录、元数据及 build hook 与候选完全一致。本次只审 Conversation 与 runtime.accept_user 接线，不将该局部结论当作阶段 A 全部通过。

只读核对确认：accept_user 先准备新 UUID/单调 seq 的输入项和候选消息，提交确认后才更新账本、revision 和内存消息；replace_context 保留系统前缀并拒绝当前未配对工具，提交成功后才交换投影和重置上下文估算元数据。账本与 title 从 checkpoint 恢复，不再从压缩后的消息反推。任何提交等待异常（包括取消）均设置 blocked，后续 save/accept_user/replace_context/intent 被拒；取消不被误判为事务回滚。未修改 Checkpoint、StorageWorker 或 schema，未绕过既有未决恢复门槛。本接缝未发现剩余阻断。

独立从固定候选构建 wheel 并作非 editable 安装，SHA256=`41aa5981773c3b165b0f9a95a40b41e206aef4a860269f24aceee90b5d1dffb5`。66 个已跟踪包成员的源码、wheel 和实际安装字节全部一致，包实际版本 `0.1.0.dev0`，模块来自本树私有 venv 的 site-packages；完整清单/hash 见 `raw/a04-foundation-binding-01/stdout.bin`。

仅复跑主协调指定的两个已有用例：`tests/test_advanced_conversation.py` 的真实存储投影→保存重开→第二输入确认，以及 `tests/test_mvp_product.py` 的七工具/审批拒绝/正常重开/两轮文字交互，结果 **2 passed in 12.07s**。没有新增测试或故障矩阵。四份独立 build/install/binding/pytest 回执均 exit0、scan_hit=false，stderr 为空；命令已 joined。原始字节见 `raw/a04-foundation-*`。

该候选允许后续摘要使用 replace_context；失败策略仍不在本接缝中选择。取消/未知提交部分为现有公开接口的静态核对，不声称本次新增了相应故障执行证据。最终固定产物、全量回归和两轴审查等待完整候选，真实模型与人工体验仍未验。

## A03 三模块：通过，可集成

候选 `f73d237f57f6752397b0d18300a5def2add4c0cd`（产品 `f65d2bc`，含已审 fa5815a），独立合并点 `67270266414a5b1ad95f75351f9cd4b5a3e0f4b4`。只读审查 `agent/compact.py`、`session/context_window.py`、`session/cache_audit.py`，对照冻结 compact/cache_audit 源码与已有断言、index 窗口解析和 audit_switch；后两成员哈希额外与来源 manifest 绑定于 `context-frozen-members.json`，其余已在准备证据绑定。

成功摘要的系统锚、全量摘要无 tail、旧摘要逐字保留及新增拼接、活 Todo pin、图片占位与原消息保留符合来源。估算、廉价 hash、分歧位置/样本均使用 JS UTF-16 单元口径；cache sink 分桶、开关、main/distill 比对和报告保留来源职责。窗口解析沿提取的来源示例和拒绝边界，手动锁与入口写回由后续组合根消费。本子范围未发现剩余阻断。

复用实现者不可变候选 wheel，复制后独立核对 SHA256=`8f5c6a1d5e9fb32e79bb119361f2f13bcda79b0545d2853ca0171c65aacea8a2`，在本审查树独占 venv 非 editable 安装。69 个已跟踪包成员与本审查源码、wheel、实际安装逐字节一致；完整清单在 `raw/a04-context-binding-01/stdout.bin`。未重复构建同一产物。

只复跑三个已有 `test_advanced_context_{compact,cache,window}.py` 文件：**24 passed in 0.22s**，其中 17 条来源断言及 7 项既有必要适配确认。没有新增测试或故障矩阵。三份 install/binding/pytest 回执均 exit0、scan_hit=false，stderr 为空，命令已 joined；原始字节见 `raw/a04-context-*`。

Q2 仍未决定，摘要异常与取消透传，没有把来源失败硬截断的那条断言迁移成通过。成功路径可接线，但该局部复核不覆盖尚未编写的 loop/CLI/模型流/usage/持久化组合行为，也不关闭原 28/29 整票。最终固定产物、全量和两轴审查仍等完整候选；真实模型、Windows Terminal 和人工体验保持未验。

## A02 静态 Skills：通过，可集成

候选 `06b427df4dfc496bbaf91d26bc6d20e877c4d62f`（产品 `5c5e85f`），独立合并点 `03064450508410e3e7f03e77b6acc3c82bf1f397`。只读对照冻结 skills/skill/bundled 源码与来源断言；静态 frontmatter 子集、调用开关、slug/namespace 匹配、realpath/name 两层覆盖、目录根/参数/正文包装均符合本批约定。路径/兼容源装配、core 补入和普通 CLI 触发留给主协调组合根，不提前声称已经接通。

复用实现者固定 wheel，独立复制核对 SHA256=`9e3d38d15473113fdcd035e6abde4f06e79bc6d0ee50a02c58f7e627f1c68107`，在私有 venv 非 editable 安装。按候选自身的 `git ls-tree` 成员集核对 80 个源码/wheel/实际安装成员，全部逐字节一致；没有把另一独立分支的 context 文件混入此固定产物清单。绑定见 `skills-source-members.json` 与 `raw/a04-skills-binding-01/stdout.bin`。

独立通过 Node v24.15.0 直接执行冻结 bundled.ts 的八个模板字面量，运行时正文和 name/description/core/顺序均与 golden 一致；结果及逐正文 SHA256 在 `raw/a04-skills-ts-golden-01/stdout.bin`。TS 原始字节与 JS 运行时换行/转义语义分开核对，没有只比较 TS 文件哈希来代替正文校验。

复跑三个已有 `test_advanced_skills{,_tool,_bundled}.py` 文件：**20 passed in 0.21s**（19 项来源断言和 1 项既有完整 core 黄金断言）。安装资源由既有 golden 断言再绑定到该已核实的 TS 运行时文本。四份 install/binding/golden/pytest 回执 exit0、scan_hit=false，stderr 为空，命令均 joined。本子范围未发现剩余阻断；没有新增测试或更改来源/core 原文。

本结论不涵盖后续 CLI/注册/提示接线，也不把动态激活、安装、第三方自动转换、插件、完整 TUI 或原 34 整票记作通过。真实 API 调用仍为 0，人工状态保持 pending。

## project_doc：回修后通过，可集成

初始候选 `b499046` 的只读审查指出：`Path.absolute()` 保留 `..`，而冻结源 `path.resolve()` 会规范化，加载器另一侧的兼容 workspace 比较又使用 `abspath`，因此同一目录的含 `..` 输入可能漏掉显式兼容指令。原负责人以 `3c3e48846da8a0673749a43dff2082a56523b964` 改成 `Path(os.path.abspath(workspaceRoot))`；其前件 `e9d5e23` 使 workspace 身份核验与已有 compatibility loader 的 resolve 口径一致。

独立合并点 `c904764035465bc21619ea2d4af7a0f73a7b9adb` 包含已审 Skills/context 与该回修；目标模块及七条测试与 3c3e488 完全相同。独立构建此固定合并点的局部审查 wheel，SHA256=`3950fa43c71bb52f090a8ae2bec065b763ded7c4304451ebeea1bb42e69144fe`；84 个跟踪包成员的源码、wheel、实际非 editable 安装逐字节一致，见 `projectdoc-source-members.json` 与 `raw/a04-projectdoc-binding-01/stdout.bin`。它不是最终交付产物，后续共享接线会使该产物失效。

对照冻结 project_doc.ts 和六条来源断言，确认工程 AGENTS/CLAUDE 不自动成为产品指令，Git 文件/目录均作为停止边界，无 Git 时仅读 cwd，根到 cwd 及本层 local 的顺序保留；D09 用户/项目兼容源在本层原生前、来源标签和 trim 内容去重成立。显式源缺失/不可读的声明诊断由后续组合根负责，native 文件缺失继续沿来源忽略。

原 `tests/test_advanced_project_doc.py` 在全新仓库外 `--basetemp` 中 **7 passed in 0.08s**（六条来源及一条 D09 必要确认）。没有改断言来适应仓库内 TEMP；最终全量同样需要全新仓库外基目录。另仅复验主协调明确授权的已观察路径问题：`child/..` 与规范路径输出完全一致，兼容内容在原生内容之前，结果见 `raw/a04-projectdoc-path-01/stdout.bin`；没有扩展矩阵。

五份 build/install/binding/pytest/path 回执 exit0、scan_hit=false、stderr 为空且命令 joined。原路径差异已回修，无剩余模块阻断；普通 runtime/CLI 还未接线，不把该局部结论当作完整 70 票通过。原始失败和历史材料保留，真实 API 为 0，Windows Terminal/人工仍 pending。

## ContextManager：通过，可供主入口接线消费

产品候选 `2d0b2169a2bcc9d1b6bd49edead421598afd59fd`，证据候选 `0618cda220983f7fa2ce661b1aec77af6fbdf0d9`；独立树先合入稳定 `facc7dd` 再合入两候选，当前 Q2 已按 ADR-0012 确认为摘要失败保留原上下文并停止。本轮只读审查新 `agent/context_runtime.py` 与九节摘要资源，compact 模块及原测试仅变更 Q2 状态文字。

核对冻结 index.ts 的预算、窗口、摘要、熔断和命令段：有效正有限预算、MAX_TURNS 的 Number-or-Infinity、hard 严格等于 `1`、进程级窗口手动锁、摘要实际 model 选择和请求 extra 保留所选语义。摘要线程完成后，在业务循环以 onUsage 或返回 usage 二选一记一次，并指定实际摘要模型；失败/取消保留收到的用量且保存原上下文。失败、partial、空摘要、取消不生成成功替换；摘要结束后检查取消，候选通过已审 replace_context 先提交再交换。summary 审计沿来源空 sys/tools/tail，不传原对话或摘要正文。空摘要拒绝为实现者已记录的具体差异，不冒称用户逐项确认或来源硬截断测试通过。

复用固定 wheel SHA256=`96baaedf38441075ca64c4e7cfe37c311909cdee3aed7d1dc4d81aaadc36998f`，独立私有非 editable 安装，86 个候选包成员 source/wheel/installed 逐字节一致。Node v24.15.0 独立执行冻结 COMPACT_INSTRUCTION 模板，真实运行时文本与已绑定资源相同，SHA256=`329afeb2b7415551cd56f5f81518228e0238d329cb7d90cd0adcf063623787ee`。

仅复跑已有 `tests/test_advanced_context_runtime.py`：**9 passed in 0.25s**；这是来源提取及必要 Python 接线确认，不写成九条 DAO 原测试。四份 install/binding/prompt/pytest 回执 exit0、scan_hit=false、stderr 为空，命令 joined；原始证据见 `raw/a04-context-manager-*`。本模块未发现剩余阻断，没有增加测试矩阵。

主入口仍须单独复核：冻结 index.ts 的轮内与完成回合后主动触发均使用 `(lastPromptTokens or 0) >= window * .85`，而本候选 should_compact 只是 chars/3 粗估。独审已明确该接线差异会导致实际 85% 已达时漏触发；主协调回执称已让两处共用实际用量回调，后续完整候选再核验。粗估可用于展示和明确的估算用途，不能自动替代该来源触发。最终普通 CLI、hard 预算执行、主轮数执行、反应式压缩及真实保存组合路径尚未由这九条局部测试验收；真实模型/Windows Terminal/人工继续未验。

## 启动 Skills 装配及 walker：通过，可消费

候选 `c2662361de69e02c1ce8db30afc366845c9b2a40`（产品 `de80dce7de96c259a4337524fbdf1990a0a2a829`），含共享 walker 单行 `e74e96a`。独立合并点 `3d8aea4080c0d5d9395838fa7613784265fa397d`。只读核对冻结 index.ts:770–861 的装配与启动预扫描：D09 四层来源顺序、磁盘先抑制同名 core、原生 disabled 名单、no-skills、最多 4000 文件、命中克隆去 paths 且只出现一次均保留本批语义；运行期动态发现、禁用写回和安装未冒称已实现。

共享 walker 将 `.ruocun` 加入原有 `.dao/.codeds` 等忽略项，避免搜索及预扫描扫描自身原生状态；未删除来源忽略项，未另造局部过滤。八个 core 资源未改。独立 Node v24.15.0 直接执行冻结中文 skillsHeader 表达式，运行时 SHA256=`d6952057acda0c387ea94ea763a27cde01bc34371acae918860ab1460fb477a6`，与实际安装导出字符串的独立断言一致。

复用 wheel SHA256=`8844f4dd7eff29f6d862e80e0bdb5a82f1c255cbf799ad062709dd685e19d54e`，独立私有非 editable 安装。85 个候选成员与 wheel/实际安装逐字节一致；来源从候选 Git 归档读取，避免把独立 ContextManager 分支已修改的同路径文件错当作本候选源码。成员集见 `skills-runtime-source-members.json`，完整绑定在 `raw/a04-skills-runtime-binding-01/stdout.bin`。

只复跑已有四个 Skills 文件：**25 passed in 0.33s**（原 20 项及启动装配五项最小适配），没有扩大测试矩阵或重复构建同一产物。四份 install/binding/header/pytest 回执 exit0、scan_hit=false、stderr 为空，命令均 joined。本子范围未发现剩余阻断，已及时通知主协调可消费；最终入口仍另验。

## root 未提交接缝的只读预审

在主协调未提交的 Conversation/runtime/loop 差异中，原命令写入 accepted 输入账本、正文作为模型投影，两者沿同一 checkpoint 提交且确认后才交换内存；保留已审账本不变量。通用手动调用只把 body 作为 prompt，与冻结 index.ts:2470–2471 相符；Skill 工具调用仍保留资源目录/args 包装，不混淆两入口。

已交还主协调两项确定遗漏：`/effort` 仅改 env、主请求未带 reasoning_effort，无法实际生效；主审计把完整普通对话放进 tail，违反冻结 loop.ts:270–312 的 tail 恒空、msgs 独立 hash 口径，会把每轮正常对话误报为前缀变化并产生正文 delta。主协调回执称已在主请求注入当前 effort、摘要保持自有 extra，并改审计 tail 为空、msgs 为脱敏实际消息；在既有 CLI 用例补入后续真实 HTTP 字段断言。此处记录是静态发现和回修回执，不是对尚未固定入口产物的执行通过；最终候选仍需独审核验。

## 最终 r1 固定候选：已有路径通过，仍须回修

固定起点 `cb074ee15018aa5b477babfe63040134f4c4d838`，产品候选 `03893b3e5b7762557a23d3a0e869d5a1c209026b`。已核验 ref 和非空 diff；`git diff cb074ee...03893b3` 为两轴共同固定范围。先前两位实现者已完成，按 code-review 技能使用两个新的独立子代理并行审查；它们不是产品作者，连同主协调和本审查者同时最多四槽。没有用一轴结论覆盖另一轴。

复用主协调不可变 r1 wheel，独立复制核对 SHA256=`3f3cb8d371a8c3fff5925b2e14b46c05e11b0efd49ac612cce6e07ce1290b472`。全新仓库外 `C:/Users/PC/AppData/Local/Temp/ruocun-a04-final-01a1c4bc-r1/venv` 仅 pip、setuptools、ruocun，未安装 pytest/mypy/ruff。87 个固定候选 Git 归档成员与 wheel、实际安装逐字节一致，版本 `0.1.0.dev0`，实际模块来自该纯产品 venv；见 `final-source-members.json` 和 `raw/a04-final-r1-binding-01/stdout.bin`。

`final_outside_confirmation.py` 沿首版 M04 的纯 wheel 确认方式复用现有 `test_mvp_product.py` 产品函数，所有函数内断言不变；账本函数通过 AST 仅提取原函数体执行，跳过依赖 pytest 的文件级平台标记，Windows 平台先显式核验，函数所有断言同样原样保留。两份原文件执行前后 hash 一致。实际覆盖八工具、拒绝、指令隔离、Skill 目录/正文/手动投影、成本/窗口/effort HTTP 字段、两轮交互、压缩后继续、独立进程重开，以及原命令账本/正文投影/压缩/真实保存重开。`--version`、`--help` 退出 0；既有帮助文本检查按阶段 A 更新为 `/compact`，没有改产品断言。

两个原函数均通过；SQLite 实际 `3.54.1`、gate=met，DLL/source ID/VFS/解释器完整清单见 `raw/a04-final-r1-outside-product-ledger-01/stdout.bin`，非主线程 0。四份准备/安装/绑定/执行回执 exit0、scan_hit=false、stderr 为空且进程 joined。没有重复跑全量；全量及五入口由主协调负责。使用安装解释器 `python -m ruocun`，未运行受本机 4551 策略阻止的 console launcher，也未改变主机策略。

### Standards

独立轴原报告见 [final-standards-axis-03893b3.md](final-standards-axis-03893b3.md)：1 项 P2 工程记录硬违例，产品源码硬违例 0，smell 判断项 0。任务票、唯一对应表及验收矩阵仍与已交付阶段 A 局部结果不一致；要求同步局部事实/证据/未完成，保持原票和人工状态。

### Spec

独立轴原报告见 [final-spec-axis-03893b3.md](final-spec-axis-03893b3.md)：3 项 P2，范围外行为 0。依次为合法 emoji 描述在 UTF-16 截断后导致 Python JSON→UTF-8 请求编码失败、兼容来源没有实际生效/覆盖诊断，以及压缩保存未确认时先显示旧 revision 的“已保存”。没有发现数据丢失或未知工具重放。

Unicode 缺陷另在已绑定的 r1 仓库外纯安装中复用该轴捕获的同一单例确认，未增加组合矩阵：description 为 `219 个 a + 😀`，catalog 尾部为 `a\ud83d`，公开请求返回 failed/UTF-8 编码异常，禁止网络的合成 transport 调用 0 次。完整已捕获复现和实际模块 hash 位于 `raw/a04-final-r1-unicode-repro-01`；脚本进程 exit0 仅表示成功观察缺陷，不能记为产品通过。缺陷待原负责人修复后复用同一命令复验。

两轴汇总：Standards 1 项（该轴最高 P2）；Spec 3 项（该轴最高 P2）。r1 的现有路径通过不等于最终自动出口通过；回修、记录同步及固定新产物仍待完成，真实模型/Windows Terminal/人工体验保持未验。

## r2 前关键共享修复：只读接缝通过，待统一安装复验

已先独审 `ca91b6be31b29b5fd4af8bdd97878c91b99b054f` 的 JSON 边界：流式 HTTP、checkpoint canonical digest、SQLite JSON 文本均仅在 UTF-8 无法编码的代理项使用 backslashreplace 生成合法 JSON 转义，普通 Unicode 和既有可编码 digest 字节不变；未更改 schema、StorageWorker 或 Checkpoint 字段。静态发现同一备用 HTTP 序列化口 `client/resilient.py:478` 仍严格编码，已交原负责人补齐；本审查者已核对 root 未提交 diff 也采用相同一行修正，r2 须包含该第四处，不能只用 ca91 三处声称全部修复。

随后独审 Skills 诊断最小候选 `0fca63c2474a9ad9f29f982122b1ca1f9fbe0be0`：loadSkills 的 optional 容器只接收既有 gather 的原对象，未重读文件；loaded 持有全部对象，winner identity 不会因对象释放复用，按最终 disk 胜者、禁用和可见名字统计来源四类状态。正常返回值、覆盖顺序、paths 扫描和旧调用不变，无 Skill 新字段。原作者复用四目录 fixture 和原 25 项源码定向复验，本审查没有另建模块 wheel 或扩大矩阵；安装行为待 r2 整体复验。

独立合并点 `d02f428eaa27f41542acb20915a1907119a4ee76` 收录 ca91 与 0fca。root 当前未提交 project_doc 的 sourceStates 按真正注入、重复、空及不可读记录；profiles 使用既有 loaded selection；footer 在 blocked 检查前只呈现“最后确认保存点”，也已只读核对正确。它们尚未固定于本合并点，最终独立 Spec 仍须对 r2 固定源码确认关闭三项原发现。

已通知主协调可组成 r2 统一安装，再使用原 CLI/真实账本及同一 Unicode 单例复验；本节不是新安装或全量通过记录，原失败与两轴报告保留。

## 最终 r2：独立自动技术出口通过

固定产品 `bccbb57062a5518aad8ee4882eae4a1eef3429e6`。复用主协调 direct wheel SHA256=`d55dfac288d0638a5cd406daf65cf9dc01cab2eb9b93b8c99142c6361cb64de6`，独立复制后在原仓库外纯产品 venv 强制更新，仍只有 pip、setuptools、ruocun，未安装开发依赖。87 个 bcc Git 归档源码成员与该 wheel/实际安装逐字节一致；绑定见 `final-r2-source-members.json`、`raw/a04-final-r2-binding-01/stdout.bin`。

独立核对 `dist/advanced-a-r2` 的 sdist→wheel 与 direct 相同 SHA256，sdist SHA256=`996372ede852b5bed4fba0b97e306bbf45b26f6877ae448773e673597967b865`，见 `final-r2-artifacts.json`。没有为审查重复构建产物。固定解释器仍为 CPython 3.11.9 x64，包实际版本 `0.1.0.dev0`。

复用同一 `final_outside_confirmation.py`、原产品函数及原账本函数，在全新 `state-r2` 运行，所有原函数内断言不变且源文件执行前后 hash 一致。产品 fixture 已由原负责人加入原缺陷的 `219 普通字符 + emoji` 和兼容 profile/Skills 的覆盖状态断言；普通 CLI、真实 SQLite checkpoint 和 HTTP loopback 路径通过，原命令账本/正文投影/压缩/重开同样通过。实际 SQLite `3.54.1`、gate=met，非主线程 0；runtime 清单及原文件 hash 在 `raw/a04-final-r2-outside-product-ledger-01/stdout.bin`。未重复全量。

Unicode 注入 transport 单例完全复用 r1 命令：目录仍按来源保留 `a\ud83d`，流式及非流式备用请求均成功越过 JSON/UTF-8 序列化，各调用一次禁止真实网络的替身；最终 failed 只因该替身主动拒绝网络，不再有 surrogate 编码异常。初次读取结果时，本审查者误预期替身仅调用一次，已依据既有备用路径纠正为两次，不重跑、不改产品、不抹原输出；说明见 `final-r2-unicode-verdict.json`。这不是实际 API 调用，也不将预期的替身拒绝当作完整请求成功；端到端成功另由含同一描述的 CLI fixture 证实。

四份 r2 install/binding/product-ledger/unicode 回执 exit0、scan_hit=false、stderr 为空且命令 joined。旧 r1 wheel、失败单例、报告与所有合成状态保留，当前 venv 更新不改变历史回执。未运行本机受策略阻止的 console launcher，未修改主机策略。

### Standards

同一独立 Standards 审查者仅复核旧记录项和 `03893b3...bccbb57` 修复差异：原 P2 已关闭，新增硬违例 0、smell 判断项 0。六原票与两表同步局部事实及证据，原票状态/完整母案例/人工 pending 均保留，未用局部通过抢跑后续依赖。独立报告见 [final-standards-axis-bccbb57.md](final-standards-axis-bccbb57.md)。

### Spec

同一独立 Spec 审查者核对四处 JSON 边界、实际来源状态和 blocked 成功标记顺序：原三项 P2 全关闭，限定新 diff 未发现确定相关回归。产品/source-state 原对象覆盖与扫描不变，保存未知只显示旧可信保存点；未增加故障矩阵。独立报告见 [final-spec-axis-bccbb57.md](final-spec-axis-bccbb57.md)。

两轴最终汇总：Standards 剩余 0；Spec 剩余 0。本审查者负责的固定产物、纯安装和已有路径自动条件已满足；主协调另行汇总固定 r2 全量/五入口及公共交付状态。本结论不是原 82 票全部完成或人工 accepted，真实模型/Windows Terminal/人工体验继续 pending。
