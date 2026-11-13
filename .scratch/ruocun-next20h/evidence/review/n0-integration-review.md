# N0 集成候选独审

固定起点 `f5bc444f72cdffd5560af2cf851d4f5660dd1774`，首轮产品候选 `895f4ac0894f4cc4eea99e0f5fa988b5927ee2ef`。本树干净后 fast-forward 到候选，差异非空。按关键接缝单独审查，未启用子代理，不改产品或断言，不扩矩阵。

## 首轮发现

**[P2] 真实 SSE 没有通知 reasoning 空截断。** `agent/loop.py` 虽传入 `onEmptyTruncation`，但 `client` 包只有类型声明，实际 `runStreamAttempt`／`streamChatResilient` 均未调用。冻结 `src/client/client.ts:406` 及 `client.test.ts:447` 明确要求 `finish_reason=length`、无正文／工具时通知一次。现有 loop 测试主动调用回调，不能证明真实客户端接线；普通产品路径因此只作普通空重试，不会注入收敛提示或使用 low effort／256000／required。

直接复用原来源单例的 reasoning-only SSE 帧，在本树实际 `client.streamChat → streamChatResilient → runStreamAttempt` 注入 transport，无网络：一轮请求、content=null、reasoning 保留、finish_reason=length，但 notified=0，原预期 1，exit=1。原始回执 `raw/n0-review-client-truncation-red-01`；已及时反馈 root，未写产品修正。

root 以 `908cd1488869ad04ea0a14246ecdda90e35c56ef` 最小回修：先构建已过滤无名称片段的最终消息，仅正常 complete 收尾、length、无正文／有效工具时调用该回调。与冻结最终消息的判据一致，不把断流／取消冒充正常空截断。独立复跑原来源单例迁移 `test_client_wire.py::test_reasoning_only_length_notifies_caller_once`，**1 passed**，回执 `raw/n0-review-client-truncation-green-01`。该 P2 关闭；固定产物及安装出口另列，不从源码单例推定最终包通过。

固定 r2 根 `70c7464b1a14a35c1796dad598c131866681c11e` 产品字节与 908 相同，仅将原 Todo 完成提醒用例的三处缩减文本断言恢复为冻结 `todo_write.test.ts` 的 `verify 子代理`，独立只读核对来源相符；没有新增 case 或为当前实现重写预期。root 的 r1 全量旧断言失败保留为历史，不写成 r2 失败或环境失败。

## 已审接缝

- 图片槽在每次工具调用入口和 dispatch 的 finally 清空，成功结果先确认 journal，缓存完整 packet 深拷贝后与新结果同批投递。
- 批末仅生成当前 history 的候选；图片 user 与 imageDelivered 同一 checkpoint 确认后交换，显式 `reset_prompt=False` 保留主 API 的实际 lastPromptTokens／lastSentLength。
- 首批 Todo 拒绝与五条冻结 execute 断言一致。`args.prompt` 定义 headless，恢复既有会话 done=True 与冻结 index 的 durable state 条件一致；管道输入不自动冒充一次性首批。
- reasoning 重试的 low effort、256000、productive 集合、required 被拒后的全量工具回退，以及成功工具轮后恢复正常选项，与来源条件一致；实际触发仍受上项客户端缺口阻断。
- resume 清洗仅归一坏 arguments，保留 reasoningContent／responseItems 等完整历史字段；更新后由既有保存接缝提交。

固定 895 的既有 loop 来源断言独立 **22 passed in 0.20s**，见 `raw/n0-review-loop-source-01`。未把该通过写成真实客户端 reasoning 通知通过。

## 来源资源

独立 Node v24.15.0 仅对已审冻结字面量表达式求值，直接比较产品资源，没有执行冻结模块或写参考树。Todo 中英 description 和空截断提示全部逐字相等。输出和原文件指纹见 `raw/n0-review-runtime-strings-01`。

| 资源 | UTF-8 SHA256 |
| --- | --- |
| Todo 中文 | d5cdea88e6e11154647de87dfab6990fd5989110e760f902c67577b9aafdfecc |
| Todo 英文 | 2d0288b157bdfa2a0a55aec3b8ff630c8d9795030f3390458aef921357f76298 |
| 空截断提示 | 1cc77860e8e55f761f6f4da3cb88a6a1635aa267fffd99e023fe69cbae44b636 |

## 固定 r2 产物与仓库外安装

只读复用 root 统一构建的 `dist/n0-r2/ruocun-0.1.0.dev0-py311-none-win_amd64.whl`，未自行重建模块或产品。独立先核验 wheel SHA256=`0cde376cc91c92db98964342f0381d26f5979bfed000147c6453d70672c89692`，再以 no-index／no-deps／force-reinstall 分别装入本私有开发 venv 与原已核验的仓库外纯产品 venv。两个环境各自独占，没有共享可写环境。

从固定 70c7464 使用 git archive 导出全部包成员，独立对照 sdist、wheel、仓库外实际安装及实际目录成员集合，**90 成员逐字节一致，无遗漏或安装旧残留**。direct wheel 与 sdist 重建 wheel 同 hash；sdist SHA256=`479b3625c717151db63440a0aaf498b1b51d2223cf5475100fefe65859f15047`。平台标签 py311-none-win_amd64、Root-Is-Purelib=false、无产品依赖，sdist 不含 tests／.scratch／.worktrees。完整逐成员指纹与实际导入位置见 `n0-r2-artifacts.json`／`raw/n0-review-r2-binding-01`。

沿阶段A已有纯安装确认 helper，在新建仓库外合成状态目录复用固定候选的原产品与输入账本函数；另按原函数 AST 执行既有三项图片／持久化函数，断言体原样保留。唯一省略的是测试文件 pytest 导入／平台 skip 标记；实际先断言 win32，未省略任何产品条件或断言。该纯环境只含 pip、setuptools、ruocun，没有 pytest／mypy／Ruff。

实际结果：原产品（含 headless 首批 Todo 拒绝、Read 图片 wire、保存重开一次性、静态 Skills、压缩及文字交互）、已确认输入账本、图片合并候选、worker 可变 payload 快照及真实图片 journal／checkpoint 重开与压缩不重注入，**五个既有函数全部通过**。图像 opaque 保真及普通字段脱敏断言仍保留。`--version`／`--help` 通过，受控 SQLite 3.54.1 gate=met，结束后非主线程 0。原测试文件运行前后 hash 不变；回执 `raw/n0-review-r2-outside-confirmation-01`。未重跑全量或模块全套；root 另负责固定 r2 全量／静态出口。

## 结论与边界

本次单独源码审查、来源资源、受影响原断言及固定安装确认已完成，已发现 P2 经独立红→绿关闭；剩余规格／工程规范阻断 **0**。该结论覆盖约定 N0 图片／Read／Todo／空截断／恢复接缝，不据此消费尚未完成的 34 或后继产品。

沿外层环境白名单启动器／tools/run.py，私有 venv、合成 HOME/config/TEMP，全部命令 joined、scan_hit=false。真实／付费模型 API 0；仅既有合成 loopback HTTP／注入 transport。08 整票状态由主协调结合统一自动出口登记，本独审未改 resolved；人工／真实 Terminal 与真实模型质量仍 pending。
