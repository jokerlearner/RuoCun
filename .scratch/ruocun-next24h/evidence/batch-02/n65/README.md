# 65 批内增量证据

65保持claimed。按batch-02/ADR0015复用既有会话、worktree和合成环境，不逐票build/full。冻结出处与逐文件SHA见source.json；参考DAO不写入，无真实模型调用。

## 基础展示切片

width、双背景语义theme/capabilities、Markdown（表格按CJK列宽折行）、app/format、spinner_words/tips及完整i18n/messages已按原MM目录实现。字典保留243个对称key及22条原tip/语言，记录来源SHA；展示时只替品牌/原生路径，并不宣传已排除plugin和系统schedule提示。

以原width/theme、markdown、format/spinner、i18n公开测试seam迁移来源断言，真实缺模块red分别保留；foundation-final为10项通过及Ruff/mypy12源通过。所有tools/run raw均明确白名单、合成HOME/config/temp、敏感扫描false。仍需事件/输入owner装配和对应源用例，不能把纯函数切片当作65整票完成。

语言readUserLang/writeUserLang/switchLang接受显式userRoot，写原生settings.json、合并保留其它字段；字段保存采用同目录排他临时写入、flush/fsync及replace，不接管普通settings目录ACL。read损坏返回None；write遇损坏或非对象保留文件并抛错，成功后才切当前语言，是已批准ADR0013保留信息失败规则的应用。没有声明该非凭据设置写入具备07私密文件/目录持久确认契约。

原cli-highlight由无新依赖的常用语言词法着色替代，未知语言仍整体dim兜底；源码文本/围栏内容保留。此为Python语言绑定替代，未声称高亮token与cli-highlight逐个等价。

## 事件与同owner渲染切片

render.py保留TurnEvents与plainEvents职责，Python async generator的最终消息显式传给consumeStream/renderStream（Python不支持JS式async generator return value）。app/app.py持有完成转录和有界live状态，reasoning先于assistant、工具意图/概要、Edit/MultiEdit红绿diff（含源结果行号块）、Todo复选项、8行工具/6行reasoning默认折叠、Ctrl+O最近完整项与后续展开、完整历史恢复均按冻结App对应分支迁移。只改展示，不改模型看到的工具结果。

InputBroker仍唯一读stdin。emit_event同步更新展示状态，静态输出进入同owner有序队列；只有完成边界使用run_in_terminal写原生scrollback，流式增量留在最多12视觉行的ptk动态区。drain_render/close把未收到saved事件的取消/失败partial按一次展示边界保留，不冒充业务持久化成功。原文去除VT/C0，SGR只由渲染层生成；known-key脱敏由组合根先执行。

configure_terminal接受冻结环境和显式owned_viewport；默认共享shell不清scrollback。宽度变化由ptk已有render回调接收，无新增reader。仅owned窗口在200ms稳态且epoch仍有效时重放逻辑转录，草稿/光标/live不变；关闭取消迟到重建。主题/语言只更新UI状态，状态指标由set_status_info纯内存端口供给。主题未显式配置时先沿COLORFGBG线索，否则dark；主动OSC/系统背景探测尚未在本切片声称实现。

events-app-red是缺模块真实red；app-final为18项定向通过（10基础、3render/App/tail、2来源owned/shared resize适配、3已有输入owner），Ruff及6源mypy通过。owned/shared用受控ptk输出验证重放许可、流式/草稿/光标保留与共享无3J；不是实机WT视觉验收。普通runtime装配与其来源回执由主协调接续，65尚不自行resolved。

## D10固定Rich与背景接缝补齐

核对D10§3.1后由主协调补固定Rich14.1.0及其D06已核传递包。Markdown保留原表格/块结构，只将最初简词法高亮替换为Rich Syntax离屏StringIO capture；未知语言/失败仍dim，不用Rich Live，不持终端。主协调负责公共元数据/锁。

background属于65启动颜色选择的前置，68只消费结果。现已按源MM755补env>同reader OSC11>AppleTerminal>dark顺序；Windows OSC250ms，未应答正常dark兜底。复用现有Reports/ParserGate，在同ptk reader解析分片OSC11并剥离迟到回包，不新增stdin reader或模式owner；paste内相似协议原样保留。AppleTerminal分支仅对应OS/TERM_PROGRAM才启动有限osascript，其实机未验。

background-owner-red真实复现“已有owner未发OSC、仍dark”；补接后background-rich-final为8项通过（同owner分片白底回包并保留普通草稿、Markdown2项含真实Rich已知语言着色、旧Reports5项）。首次green命令文件名误写导致exit4/no tests ran，保留原回执，不算通过。final的mypy发现Pygments无typed stub，窄注释后background-rich-checks为4源Ruff/mypy通过，测试已过部分未重复运行。无新增产品测试矩阵、build/full或实机窗口操作。
