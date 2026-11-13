# 66/63关键接缝独审

基线对齐 `6d74070`，src/tests无候选外产品改动；另收用户明确选择的当前账户删除 `40849dd`（ADR0016）及通知dotenv修 `45a478c`。不读系统凭据/剪贴板，不调用真实或付费模型，不构包、不全量。以下回执均经白名单/合成HOME与合成账户，scan false；有重叠不合计成独立案例总数。

| 独立实际运行 | 结果 |
| --- | --- |
| b02-review-n66-approval-owner | 既有审批队列/危险无always/Esc/同批Enter所有权：1 passed in0.68s |
| b02-review-n66-account-runtime2 | 普通TTY真实账户与模型面板切换→HTTP请求；post-publish不明确保存→停且重开blocked：2 passed in9.26s |
| b02-review-n66-active-delete | 只延长上条正常场景核ADR0016：删除当前账户后下一请求沿旧连接，手动切换后用新连接：1 passed in5.79s |
| b02-review-n63-env-disable | 通知工具实际消费冻结execution env的禁用值而非旧全局环境：1 passed in0.36s |
| b02-review-n66-test-style2 | 新增接缝夹具Ruff仅整理import后通过，无行为修改，不重跑已绿项 |

## 66

审批模态串行复用同一owner/锁；当前批按键完成后下一事件循环才归还主草稿，y/a/n、危险/noPersist屏蔽a、Esc清当前及排队审批的源码路径已核。既有实际定向覆盖危险无always、a+Enter不下溢提交主草稿、并发下一批与Esc；未把普通source全组重复一遍。掩码凭据输入与已解码VT清洗沿既有回执。

新增 [test_b02_account_runtime.py](../../../../../tests/test_b02_account_runtime.py) 只做上述必要普通入口合成验证。真实InputBroker选择账户、选择回环返回的模型列表；捕获实际HTTP地址、Authorization、model并与流请求provider/options逐一对应。账户切换后新key/provider/base/model一致；配置真实写回。MemoryKeychain无调用，不接系统凭据；两个合成key未刷UI。

保存不明确场景在真实saveProfiles发布后注入DurabilityUnconfirmedError：配置已可见，不将其误称未执行；当前会话exit74/blocked，不发新账户后续模型请求。实际重开相同会话仍blocked，未决AccountMutation意图保留，不自动重放。

按用户ADR0016，删除当前work后配置选personal，当前进程下一实际HTTP仍用work的原provider/key/model；显式切换personal后才实际变为personal。保留旧连接的提示已出现，没有替用户改成自动切换。兼容源的凭据删除仅在origin明确属于原生服务时执行，来源只读边界已核源码，不拿内存替身冒充真实系统凭据验证。

首次 `b02-review-n66-account-runtime` 的两个失败是独审夹具错误：写错确认文案；同一进程换合成HOME触发受控SQLite DLL门禁。改为按真实状态确认且各场景沿原TTY惯例独立子进程，原失败保留，不声称产品缺陷红绿。第一次Ruff仅import排序失败同样保留。

结论：**审批/账户动作/写确认关键子出口当前0阻断，可供69消费**。66整体及真实终端体验仍由主协调按批末实际记录验收，不以fake-actions代替后续真实请求。

## 63

只读核标题栈push/pop、ST结束、C0/C1/DEL清洗、同owner控制队列、focus/真实按键清注意状态；次要标题/提示sink失败不置业务render_error。NotifyUser仅终端best-effort，不执行桌面命令，不声称用户已看到。普通source7项/旧owner3项/静态沿A对应冻结回执复用。

发现普通runtime的.env只进入受控env而工具notifier读全局os.environ，冻结DAO对应dotenv进入process.env，故项目禁用通知值会漏接。`45a478c`让ToolContext携带notificationEnv，并显式传给notifier；默认None保留原调用行为。只跑上述禁用窄例复验，无新矩阵。当前源码接缝0阻断；实际WT标题恢复/焦点/提示与77整体体验仍待集中记录。
