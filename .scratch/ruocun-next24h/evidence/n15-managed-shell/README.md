# 15 独立 Shell runner 候选

本候选在14普通入口独审通过后实施，任务保持 claimed，等待主协调普通入口装配、独立owner强杀/接管与同包安装出口。来源只读冻结ZIP，哈希见manifest；未调用真实模型、未产生模型费用。

`ManagedShellManager(session_dir, session_id, store)`复用唯一Conversation/StorageWorker的prepare/commit/recover。DB先将Bash intent关联唯一RunRef与launch，私有目录保存签名manifest/capability；真实runner bootstrap身份确认后，先持久grant-possible，再发grant；runner排他创建并同步start.claim、持久started，随后走已有suspended→自有Job→resume。grant可能发出以后失联不重启业务。grant前已证实未授权的失败保存failed-before-grant、runner.log与可配对错误结果；bootstrap晚到由已持launcher收口或30秒未授权自停，未知清理不冒充真实closed。

runner和controller默认均从当前解释器的同版本包内部角色启动；manifest核版本和关键角色/进程/IPC文件指纹。源码测试只以n15_role_loader选择本worktree/src，再进入真实ruocun.__main__/CLI角色分派；未将该源码定位器当作仓库外安装证明。正式默认入口仍为`python -I -X utf8 -m ruocun --ruocun-shell-runner <private-run-dir>`。

Windows IPC复用A线已独审的私有具名管道与监督helper，HMAC不替代当前SID ACL。OS核helper和真实owner身份，业务层核run/launch/plan/control_epoch。接管先提交新的控制租约；helper退出确认后才换随机端点并增加epoch，业务runner与命令保持原身份。失联、身份错误、可能已grant或收据不明均保持unknown，不以重spawn兜底。

显式background或前台detach先持久保留决定、确认runner接受，再返回同run的ack。正常close尊重已确认detach；其它运行请求cancel并等待真实进程树及日志关闭。owner恢复时，已许可后台接管同run；未保留的原前台先接管并取消，拿真实收据后记录“原前台已停止，未重启”。旧未知副作用继续阻塞，不自动解释用户决定。

runner拥有命令Job并逐块保存stdout/stderr原始字节与解码文本，默认内存输出收集在该角色关闭，日志无10MB停止限制。取消后日志继续排空；独立onLogOutput持久接收与UI的onOutput signal屏蔽分开，UI无迟到回调。终态在Job active=0、真实句柄/输出关闭并fsync后写签名receipt，绑定原身份、退出码、全部日志大小与摘要；再持久发布终态。自然完成与取消相撞保留真实结果。已完成附件缺失或签名身份错误停止恢复，保留DB终态和现场；该选择遵循用户已批准的保留信息失败策略，与来源将缺附件标unknown有明确差异。

UI观察与BashOutput消费使用不同游标，detach后模型仍能读到此前仅UI显示的输出。前台响应最多保留每流10MB文本并给完整日志指针，进程不会因此被杀。BashOutput按来源每流20k JavaScript UTF16单位首60%尾40%裁剪，推进至本次观察末端，30秒内running空输出给节流提示；全文仍在私有run目录。KillShell只请求终止，真实closed后才返回canceled，不把请求当成退出。后台自动完成通知属16，本候选不虚构该承诺。非Windows原前台端口继续保留；持久runner实际证据限Windows，不宣称Linux/macOS验证。

## 来源用例及真实回执

| 来源断言 | 当前验证 |
| --- | --- |
| managed_shell真实完成、断开后导入、去重、不重复启动 | `test_real_detach_reconnect_logs_and_once`：真实命令写starts一次，前台实时before→同run detach→新Conversation恢复→完成/重复恢复；同case核UI不消费模型游标及20k首尾保留 |
| grant前bootstrap崩溃诊断、恢复保留已知失败、下一命令不阻塞 | `test_before_grant_failure_retains_diagnostics_and_unblocks_next`：真实内部启动候选退出23、无grant/claim/副作用、原runner.log留存；新Conversation恢复已知失败，真实后续命令成功 |
| 取消请求持久、真实close才canceled；缺失附件/错配run拒绝 | `test_real_cancel_receipt_and_missing_attachment_no_relaunch`：真实持续写入→取消→64位receipt→止写，原始/文本ASCII日志完全一致；签名run错配及删除附件均拒绝恢复，无第二次执行 |
| runner丢失有限重连、unknown、不重启 | `test_real_runner_loss_stays_unknown_and_does_not_restart`：OS核原runner身份后强杀，Job子孙止写，重复poll/restore为unknown，无伪造close收据，starts仍一次 |
| Unix TMPDIR/socket端点异常四排列 | Windows使用私有具名管道，不使用TMPDIR选择socket；当前SID ACL和实际端点由n15-ipc独立证据覆盖。未把Unix filesystem排列伪计为已跑Windows测试 |

n15-real-initial是首轮真实闭环通过，未将其写成red。n15-lifecycle-source1为真实取消竞态红：终态已写但RPC关闭导致cancel错误返回unknown（2通过1失败）。修复为错误时优先核验真实terminal，n15-cancel-green定向复绿；后续三项及完整回归均绿。保留实际红/绿回执，不补造先测的历史。n15-source-runner-loss单项真实通过。

最终n15-final-regression为37项通过：本票4项真实来源生命周期、共享DB接缝1项、14输出4项和既有Shell/Windows28项。mypy7源及Ruff通过。全部经tools/run.py明确白名单、合成HOME/配置/会话、当前worktree源码运行；日志只含合成输入，秘密扫描false并人工检查。raw未包含能力密钥、私有run目录内容或SQLite会话文件。已知坏驱动、独立账户、注销/重启、任意宿主Job逃逸与非Windows实际后台未验。

本候选不代填16/17、终端视觉体验或最终全量固定包出口。普通产品入口与正式同包安装须由主协调在同一冻结候选完成；独立强杀controller后的已许可后台接管也等待独审，不能用本票runner-loss代替它。


## 完整日志消费后的CLIXML缓存边界

候选后复查发现14的CLIXML整帧缓存原本由10MB采集上限间接限制，15取消内存采集上限后需显式保持该展示缓存边界。现decoder增加可选clixmlLimit，仅runner无内存采集时使用已有OUT_CAP的10MB；14默认None兼容。超过后按原协议文本持续完整落盘，给模型可见诊断，不截断原始字节、不终止命令；已有小帧可读转换保持。shell_output.py也纳入真实同包关键文件指纹。

只沿既有14解码断言加小输入边界，不新增压力矩阵。n15-clixml-budget-red实际先报缺少参数；实现后n15-clixml-budget-green为14+15共8项通过（36.47s），3源mypy/Ruff通过。该适配不宣称任意CLIXML都能完整语义解析，超限明确选择保留原文以限制展示缓存。


## 冻结工具提示、schema与双语消息对齐

BashOutput/KillShell的export const defineTool之后的中文描述、descriptionEn和id字段，从同一冻结ZIP的src/tools/exec_shell_poll.ts、src/tools/exec_shell_kill.ts精确提取。产品resources/exec-shell-poll.json与exec-shell-kill.json保存原始整段中英描述、id原文、MIT出处与源文件SHA256，同时逐条保存窄适配from/to；产品提示由这些原文经列明替换形成，未整体缩写原使用指导。id恢复原文“Bash 返回的后台进程 id”。

当前必要差异仅为：15尚未消费16后台完成自动通知，提示改为间隔确认真实状态；Windows使用受管Job而非声称SIGTERM进程组；状态配合实际exitCode；旧.dao/bg路径改为BashOutput回执所示运行目录中的解码文本stdout.txt/stderr.txt，原字节仍为stdout.log/stderr.log。因此handler在实际观察回执显示[logs]目录。原stdout/stderr分开、只返回新增输出、exited后取尾部、20k首尾裁剪、长构建/测试及watch清理等指导保留。源KillShell声明auto但冻结/当前权限引擎的auto名单未含KillShell，故保留auto元数据和已批准任务清理意图，同时说明实际调用继续遵守会话权限规则；未修改权限gate或新增放行。

handler按ctx.lang保留中英状态、空输出节流、未知/未绑定后端与KillShell请求/不存在id消息。取消请求仍不当成退出确认；普通控制失败不被“id不存在”友好提示掩盖。

n15-tool-contract-red为实际缺descriptionEn/id原文及英文handler失败（2失败）；green第一轮保留一处新增英文句型与断言不一致（1通过1失败），调整未绑定提示后green2共2项通过。测试分别核冻结export原文/源SHA与显式适配后的完整描述一致、原id/schema/auto元数据，以及既有handler双语分支。mypy2源/Ruff通过。没有重复原生生命周期，没有新增16功能，原37项及CLIXML8项证据继续保留。


## unknown恢复后的finally关闭守卫

公共runtime接入后会在blocked74分支照常执行manager.close。diagnosing-bugs用真实Conversation/SQLite的最小restore→close入口复现：无控制材料的_Run占位仍走cancel，缺manifest时先写canceling再KeyError(version)，坏terminal则签名格式异常；都会覆盖原有保留停止出口。候选按优先顺序区分“空manifest盲提交”“坏附件校验先于unknown守卫”“旧owner/epoch控制未认证”三个假设，未加入广泛故障排列。

当前cancel在改写取消意图前区分已知终态、已证实grant前失败和可认证现场。未知现场必须有完整且仍匹配的私有capability/签名manifest、已知原runner身份、活的原执行器与当前controller，以及同一已确认owner/epoch，才允许请求原run取消；材料或租约不明直接返回unknown reason，不写DB、不写cancel文件、不重grant/重放。正常已认证取消仍使用原Job与真实收据路径。close对已许可但未知后台保留现场；返回tuple未确认notice供root统一脱敏输出，不覆盖blocked停止结果。坏附件的既有终态保持原记录，close只报告附件未确认。KillShell收到reason也明确未发出请求，避免给模型错误的“已请求”回执。

原red夹具漏resume参数，red1修正后得到目标KeyError但第二项外层GBK解码遮挡异常；red2固定UTF8捕获，真实复现缺材料与坏terminal两条故障。green两项实际SQLite断言：restore后未知记录经close及显式cancel完全不变、cancel_requested仍false、返回未确认notice。n15-unknown-close-regression为6项通过，含原真实取消/runner-loss和双语契约；沿原取消case补坏签名/缺附件后close报告且原canceled终态不变，n15-bad-terminal-close-green单项通过。KillShell消息旧承诺在原语言case补断言先红，再修为准确未发送，final-green4项通过；最终2源mypy/Ruff通过。没有修改terminal的长路径归一或启动16/17，也未把不可认证unknown伪装成已停止。
