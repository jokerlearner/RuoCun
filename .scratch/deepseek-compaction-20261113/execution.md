# B 方案执行记录

启动：2026-11-13，用户指定 TDD 并明确要求根据 spec 完成计划。
基线：`381f73d7eea7bc25eeba6c08bff7f3aae0564875`，共享 integration/ruocun-migration 工作区；既有改动按文件副本与哈希保留，不整体提交。

## 文件归属与接缝

- root：T01公共记录、ContextManager、Conversation、主/子运行时接线、归档命令/工具、导出/生命周期及最终集成。
- compact_audit：T02的compact.py、新compaction_policy.py、摘要资源与对应公开策略测试。
- memory_audit：T03的archive/upgrade、StoragePort契约、DurableStore、StorageWorker及存储测试。
- harness_provenance：只读独立复核、既有定向复验及白名单测试启动器，不实现被审产品。

测试边界已由用户根据spec启动指令确认：普通CLI/本地HTTP/跨进程为主，既有公开策略接口与StoragePort/Worker为必要补充。每片先红后绿，不一次性铺全测试。

## 保存点

- T01完成：接口冻结、ADR-0020、23文件副本/指纹；环境复验既有2项通过，不计B新增验收。
- T02完成：22项策略定向、Ruff/Mypy通过；独审亲跑22项通过（reviewer-t02-policy）。
- T03完成：归档/原子提交/丢确认/取消/备份升级/旧writer拒写通过；细分独审后释放T04。附件/branch闭包/cleanup增量独审3项通过（reviewer-t03-lifecycle）；见evidence/t03-delivery.md。
- T04/T05进行中：主最终请求preflight、typed rewrite、prefix/clear/branch、ArchiveRead固定scope、完整/当前投影导出、用户分页查询已接。mr3主账户/会话/预算等15项、cr1上下文/工具19项通过；子同步/后台裁剪回查与摘要后输出原文由独立文件owner接线。
- T06独立实际CLI验收：reviewer-t06-cli-r2两次压缩/重整/重开/原文回查通过；reviewer-t06-upgrade-r4缺失账户配置时公开离线升级入口通过。最终候选需重新绑定同版源码与安装包。
- 独审修复：同model不同provider窗口缓存（rv1r→rv1g）；后台scope在流式导出期间变化时拒绝发布（ex1r→ex1g）。全量及固定包尚未执行，未宣称整体通过。

## 集中验证进行中

本节保留迭代过程；最终状态：**B-r3自动实现、验证与独审完成，用户体验待验**，权威汇总见[delivery.md](delivery.md)。

- B-r1完整构包输入指纹：`e4a12606737e3234bb7804d48b7377a1caa09d8312054e0476f5a717ccf8fd61`；[构包与314成员绑定](evidence/t07-r1-delivery.md)。仓外QA及无pytest的pure均已安装，同一两个公开CLI跨进程案例分别通过（reviewer-t06-installed、reviewer-t06-pure）。
- QA集中Ruff（fst）、Mypy291源码（fmt）、pure统一offline驱动4案例（off1）通过。
- 全量首启动f1因临时根仍在checkout内，违反无Git夹具前提，已中止、终止自有进程树且确认无残留；不计任何完整通过数。f2使用`D:\rcb-dd7453\src-tests`外部专用根运行，产品文件在整轮期间保持B-r1不变。
- 人工终端辅助准备经真实CLI发现新空工作区`/export`未创建`.ruocun`父容器而失败（manual-prepare、manual-prepare2）；预建容器的诊断对照不作为产品通过。R1全量结束后修此确定缺陷并构B-r2，复用未变化材料，不隐藏R1失败。
- 技术体验辅助脚本仅准备合成资料与公开命令，不自动操控终端UI；Windows Terminal视觉/缩放和用户验收保持pending。
- R1完整f2实际结果：`1734 passed, 1 failed, 4 deselected in 470.42s`。唯一失败为旧52项命令计数；适配保留原52来源项并单独验证native archive后，R2已安装包受影响B05/目录/package/private-files共25项通过（r2-target）。
- B-r2修正新空工作区导出创建父容器四行，314成员绑定与pure同两案通过。R1其它字节不变，按ADR-0015保留原全量与差异证明；R2作为中间候选不替代最终R3。
- 后续确证US09缺口：压缩归档TodoWrite后重启，ctx为空导致下一次压缩移除旧pin。独立真实两场景red为`keep=false/explicit_clear=false`，修复后green为`keep=true/explicit_clear=false`。R3仅在context_runtime新增共用pin读取helper，不反解析显示文本为结构化清单、不重放工具；正式controller两例与实际CLI共14项通过（todo-final），独审reviewer-todo-green通过。
- 实际规模：新增5个产品模块810行、新增5个测试文件1093行；有逐文件原副本的15个产品文件新增1245/删除138行（后续R2/R3再随最终统计更新）。不将其余既有用户Git差异计入本批规模，详见evidence/change-size.json。

## 最终保存点

- B-r3输入指纹`5f530430e385fef8b05837f06165d5c8cdd3c308cc70c87bdd52bfcab0744486`，314产品成员在snapshot/sdist/两种wheel/实际pure安装逐字节一致。
- 全仓Ruff、Mypy291源及最终安装controller回归通过；独立pure-r3公开T06两案＋Todo节点共3 passed/17.33s（r3x），模型命令严格`-I -m ruocun`、无源码注入。
- 独审最终核对root323构包输入和27被审安装文件与R3一致，无未解决阻断。最终文档校验20份、139本地链接、323输入无漂移，见evidence/final-validation.json。
- R1完整f2与R2/R3差异/定向复验按ADR-0015保留引用；未额外重复无关全量，未改写原失败。最终wheel/sdist SHA复验匹配。
- 主票02和09为awaiting-user，09 Automatic exit=passed；T01–T06 resolved。Windows Terminal视觉/缩放与用户体验pending，真实模型质量not-run；合成验收脚本已就绪。
- 未Git提交，原有改动完整保留；未升级真实会话、未替换日常安装、未调用真实供应商模型。

## 已确认的旧测试差异

- 无操作压缩不再允许重新发送同一份服务端超限请求（r1r原3次→r1g为1次）。loop旧替身改为产生真实缩小投影，来源流式/配对断言保留。
- 近期原文保留可能令很短历史无需摘要；原MVP摘要夹具增加真实旧段及显式小近期预算，避免把没有安全旧段误判压缩失败。
- branch只携带当前可见来源闭包的附件；未被任何可见消息引用的任意父附件不再全量继承，避免扩大读取范围。
- session_product死owner测试内层子进程补显式同版loader，消除storage1旧安装包与storage3源码混用，不放宽版本门禁。
