# 批次02独审：16事务P1与65来源展示

固定审查树对齐 `cf00bb7`，`src/tests` 与该候选无差异。16事务为 `3facf21`，65基础/owner/普通入口及Rich/OSC为 `f997f62`、`3be7fff`、`19e5786`、`0060ecc`、`cf00bb7`。按ADR0015复用已有来源回执，不构包、不全量、不重复普通MVP/TTY。

## 16事务P1

实际独立定向 `b02-review-n16-storage-p1`：`tests/test_n16_background_storage.py` 两项与 `tests/test_n15_shell_store.py` 一项，**3 passed in 14.53s**。白名单、合成HOME/配置/TEMP，exit0、scan false；原22项来源/worker/Conversation与静态回执复用实现者对应记录。

共享 `_save_shell_run` 继续校工具意图/执行绑定、control epoch、端点变更、runner身份与终态receipt，保留已有真实Bash结果，不被后台ack替换。run+event同事务；溢写先私有原子发布，再附件hash登记。消息、delivered标志、checkpoint及operation receipt同事务，成功后才内存ack。实际rollback注入确认未写消息/未消费事件，撤回consumed后同批重试一次；pending或提交不明不据此重放。旧checkpoint的background=None不改变原请求digest。

P1所交事务切片当前无阻断，可以供P2继续消费。16整票仍claimed：TaskWait、loop/scheduler唤醒、manager实际观察及普通入口尚不据此完成。已向实现者指出P2需维持的调用边界：ExecutionSnapshot与实际RunRecord同一kind/status，且终态已保存而事件尚未发出时的恢复应由真实manager材料补事件，不能只沿旧background_execution运行态。后续依固定P2实际调用核验，不扩静态矩阵。

## 65普通源码与资源

只读核freeze source及已有来源回执。`b02-review-n65-resources` 实际机器核对中英各243 key与22 tips逐项等于冻结TS；同时核zip成员来源SHA及Python SOURCE_SHA256。原文保留，品牌/原生路径只在展示层转换；不逐字符串重复模型审阅。

语言坏文件读降级、写保留且失败后不切内存语言符合ADR0013；写正常合并其它字段。/lang无参切换、/theme仅本会话变更基本契约与冻结来源对应。Rich Syntax只捕获StringIO内容，不取得终端owner。背景优先env→同reader OSC11→AppleTerminal→dark，250ms查询、分片与paste隔离、关闭时取消清理均已读；已有来源/同owner回执按对应SHA复用。

发现具体VT展示问题，保存 `b02-review-n65-decoded-vt-red`：JSON原文先clean_text，随后loads让`\\u001b`重新变成ESC，Edit的解码path/old_string未再清洗，caps.none输出仍含VT。最小脚本[b02-decoded-vt.py](b02-decoded-vt.py)实测unsafe=true并exit1，scan false。实现者正在只修展示字段；65因此尚未独审收口。没有改实际工具参数/结果。

回修 `243e9f1` 仅清洗解码后的展示字段、工具名与最终label。独审沿同一脚本 `b02-review-n65-decoded-vt-green` 实际exit0/scan false，unsafe=false；额外断言原call逐字段相同，未更改工具实际参数。没有重跑普通组。该具体展示缺陷已解除，65已审候选当前无源码阻断；整票技术/集中终端与最终验收由主协调按真实记录收口。

## 后续固定包接缝

Rich固定依赖加入后，纯安装运行依赖从2项扩为6项；旧`outside_confirmation.py`仅按项目三项直接依赖匹配installed distributions，会误拒markdown-it-py/mdurl/pygments三个传递依赖。最终批次唯一固定包时须按runtime锁的完整闭包核对，不能删除这些合法依赖或伪报额外包。当前未构建/安装新包。

## 16 P2与普通入口：实际阻断

P2 `5984ef8` 与组合 `2ad6ad8`/`70dbf8b` 已按固定提交应用。独立 `b02-review-n16-p2-risk` 为 **5 passed in 14.04s**：ready结果精确ack、真实Shell观察且保BashOutput游标、持久等待恢复、loop单独yield/混批与事件/用户唤醒；没有重跑55组。runtime的manager.restore→background.bind→refresh_recovery顺序、按轮wait_scope、scheduler注入delivery、退出先stop/await observer再close manager/DB已读。

但[普通CLI单闭环](b02-background-cli.py)实际失败，label `b02-review-n16-cli` exit1/scan false。第一轮按headless原要求TodoWrite+Bash background取得真实run UUID；紧接第二轮单TaskWait，工具结果不是等待JSON而是 `Error: 工具读取失败（ValueError）。`。第三轮虽然CLI返回最后合成回答且exit0，不能据此误称等待成功。

`b02-review-n16-cli-inspect` 使用受控SQLite只读同次DB，确证Bash ack成功、TaskWait错误结果，两项均result_committed。源码显示started登记由250ms observer异步完成，Bash ack与立即TaskWait之间可能尚无runtime snapshot。已报告主协调与执行实现者核查；不添加sleep掩盖，不解锁16或后继。原脚本及只读检查脚本、raw保留，待固定修复后沿同脚本复绿。

## 16最终收口

竞态修复 `af28ece`（主线 `e242f2d`）增加同步background绑定，ack前await同一真实run的登记；周期observer与ack共用每run publication_lock。独审原脚本 `b02-review-n16-cli-green` 实际exit0/scan false：仅3次必要模型请求，TaskWait确为waiting，随后同run事件一次唤醒/通知，TodoWrite/Bash/TaskWait三对工具配齐，执行一次，CLI正常退出0。本次仅原失败一条复绿，未重跑普通组。

进一步最小diff审查发现ack刷新已变unknown时仍可能返回普通成功。修复 `e1661e3`（主线 `310057b`）统一确认helper：发布完成且无fault后，只允许running/canceling或真实terminal返回ack，unknown保留事件并抛错。沿原runner-loss，仅将失去runner的时点移到detach后ack刷新前；独立 `b02-review-n16-unknown-ack-green` **1 passed in 7.60s**，exit0/scan false，真实同run unknown、Bash结果缺失、unknown事件1项与会话blocked均保留。实现者原红回执继续保存，未将此前碰巧通过的竞态重放当红。

最后guard只拒未确认状态，不改上述已确认running/terminal成功分支，因此沿用已绑定CLI绿回执，不再重复CLI/5项/55项。已核本地runtime/manager与主线 `310057b` 相同。**整16当前已审技术路径剩余阻断0，可供17/63消费**；来源其它kind预留不冒充尚未交付的多代理实现，真实模型与整体77体验不据此完成。没有构包或全量。
