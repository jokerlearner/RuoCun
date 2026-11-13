# N0／08集成记录

Status: complete / automatic-exit-passed（08；34另列）
启动f5bc444，共享类型92ddc62，root唯一拥有loop/runtime/types；Read候选1ac88d2、图片持久候选8d29155均已由独立1c29514复核后消费。首轮时34及后继未解锁；最终08出口通过后的领取读取末节及计划，当前验证仅下列真实子路径。

## 来源与实现

- 冻结loop.ts/test.ts的reasoning空截断提示、low effort/256000重试档、FORCED_TOOLS、tool_choice拒绝回退全量工具、正常请求恢复；两次有界空重试；恢复历史只清洗坏arguments而保留其它字段。收敛提示从冻结JS字面量运行时提取，SHA256=`1cc77860e8e55f761f6f4da3cb88a6a1635aa267fffd99e023fe69cbae44b636`。
- headless沿冻结index的argvPrompt而非任意管道判定；普通一次性入口注入todoWriteRequired，新会话首批需TodoWrite，恢复既有会话不重拦首批。execute.test五条按原条件迁移，现有CLI用例复用来源read-first三请求链。
- Read恢复图片及完整中英描述/schema；TodoWrite中英描述/activeForm及完成提示恢复来源。Todo元信息从Node24字面量提取，中文SHA=`d5cdea88e6e11154647de87dfab6990fd5989110e760f902c67577b9aafdfecc`，英文SHA=`2d0288b157bdfa2a0a55aec3b8ff630c8d9795030f3390458aef921357f76298`。
- 图片结果使用既有StorageWorker和ToolRecord完整消息，旧str兼容读取；无物理schema/version变化。源码／元信息／12项存储及28项Read模块证据见相邻目录。只承诺新代码读旧str，不承诺旧二进制恢复新增图片packet。
- 执行器每次清空/消费图片槽，持久结果确认后记录tool.imageData；批末user图片和imageDelivered同一checkpoint确认后交换；主API token值保留。恢复不因tool pair已存在漏图，也不从压缩掉的旧record重新注入。内联图像在私有存储作为opaque字节保真，普通文字/参数/远程URL继续脱敏。

## 实际验证

沿已批准DAO语义seam迁移，必要Python图片接线单列，不扩竞态/压力矩阵。外层清空环境＋tools/run.py，合成HOME/config/temp、私有CPython3.11.9，付费/真实模型API0。

| 回执 | 实际结果 |
| --- | --- |
| n0-empty-red → empty-green | 原入口缺onEmptyTruncation；接线后14项循环通过 |
| n0-resume-red → resume-green | 缺续写清洗入口→16项通过 |
| n0-headless-red → headless-green | 普通CLI确实错误读到print(old)；补ctx首批规则后17项通过 |
| n0-image-cli-red | 旧安装Read仍拒绝图片，非最终接线red |
| n0-image-wire-red | 已恢复Read后，后续模型请求仍以tool结束、缺user图片，明确证明接线缺口 |
| n0-image-wire-green | 命令误写不存在test_n0_image_store.py，pytest exit4／零用例，记ENV，不作通过 |
| n0-image-wire-green-2 | 原CLI（1px有效PNG）＋loop/真实图片重开20 passed in13.44s，图像字节、user注入、内部字段剥离和重开一次性均确认 |
| n0-loop-source-all | 22 passed in0.24s，含原五条headless及forced工具轮后恢复正常请求 |
| n0-integrated-mypy / ruff-2 | 78源文件mypy与全仓Ruff通过；mypy采用已核验同版本纯Python发行包，原DLL ENV记录保留，见[工具环境](../tooling/README.md) |
| n0-client-truncation-red → source-green | 独审用真实SSE发现客户端遗漏通知；冻结client.test.ts:447同例通知0→1，客户端＋loop源码定向52 passed in4.52s。只在完整正常流、length且无正文/有效工具时通知 |
| n0-final-pytest-r1 | 固定895/r1：685 passed、1 failed、3 deselected；失败是Todo旧MVP自写提示断言，原DAO完成提醒已恢复，原case同步恢复冻结verify断言，不增加用例或修改产品来迎合旧断言 |
| n0-final-build/direct/install/bind-r2 | 固定70c7464（产品908cd14同字节）；direct与sdist重建wheel相等，90包成员源码/安装/产物绑定，实际SQLite3.54.1。摘要见[artifacts.json](artifacts.json)/[runtime.json](runtime.json) |
| n0-final-mypy/ruff/offline-r2 | 三项退出0；mypy src为70文件，随后default配置完整78文件通过；全量687 passed、3 deselected in367.16s |

原始命令/失败收录本目录raw，首轮旧产物绑定保留在相邻n0-integration-r1目录。r2 wheel SHA256=`0cde376cc91c92db98964342f0381d26f5979bfed000147c6453d70672c89692`；未完成的回执不会由绑定脚本代填。root全量687 passed、3 deselected；Ruff、默认mypy78、offline及固定构建/安装全部通过。独审09e372d已集成，剩余问题0，真实客户端通知P2已独立关闭。2026-11-11 04:54后登记08 resolved；34与其它后继仍按自身完整前置和出口判定。真实模型、Terminal与人工仍pending。
