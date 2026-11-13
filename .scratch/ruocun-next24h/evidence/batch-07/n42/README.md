# 42 反思核心候选

仅本负责人纯模块与记忆写入接缝；普通入口、持久反思 Controller、取消/压缩/恢复独审由主协调另行绑定。本材料不代替该出口，不自行 resolved。

冻结来源为 dao-f17e189-7ac654a0dc06/source.zip；归档及原始模块/测试的 SHA256 在 source-binding.json。未修改 DAO，未调用真实模型。

## 实现与接口

- `1c9e6c64`：cadence、轮内 health/错误签名、容错 JSON result、机器提取的 challenger/refocuser 提示。
- `d3bca842`：`async reflect(messages, *, options, call, existing=(), fork=False, reasoningEffort='max', signal=None)`；fork 复制转录和工具但仅收反思结果，不执行返回工具；冷请求只发摘要材料、禁用工具/思考。组合根依来源显式启用 fork，并给 call 绑定同一取消信号。
- `applyReflectResult(result, store, *, today, origin=None, signal=None)` 顺序 upsert → corrections → confirmed；复用 MemoryStore 的私有目录/CAS，返回实际 added/merged/corrections/confirmed。任一后项失败保留已写前项并向外抛出，交已批准 unknown/人工恢复，不吞为“反思无输出”。不引入第二套执行账本。
- `cc3b6c24`：reflected/corrected 审计及源报告；消费 `touchConfirmed`，locked 内容和状态不改，允许刷新 lastUsed（对应冻结 persist）。

模型分析失败的 quiet、稳定 intent/result id、ready 元数据、安全注入及恢复去重由 root 的 reflection_runtime/Conversation 组合；本 helper 不冒充该持久成功。

## 来源语义与最少回执

核心三条压缩用例覆盖来源 cadence 退避、单轮 health/challenger/refocus、错误签名、宽容解析/分段丢弃坏项。pipeline 两条覆盖 fork/冷请求、前30正文/全部标题、记忆价值/secret/feedback 筛选、真实 MemoryStore 的新增/纠错/锁定确认。审计用例覆盖 reflected/corrected、节奏跳过/明细/最近 note 和开关。

`raw/` 保留工具白名单命令、合成 HOME、退出码及已审合成日志。核心 missing-module red → 3 passed；pipeline missing-module red → 与核心合并 5 passed；audit missing-port red → 反思/audit/旧维护共9 passed；静态0。根秘密筛选补丁修复了“中文紧邻合成 AWS key 不匹配”的真实接缝，已用同一来源样本复绿；未展示任何真实凭据。

测试入口均为根 `.venv/Scripts/python.exe -I -X utf8 tools/run.py --state .cache/b07 --label <绑定标签> -- .cache/b06/venv/Scripts/python.exe -I -X utf8 -c <显式插入本树src并pytest>`；完整 argv 在各 raw/command.json。没有全量测试、构包或终端体验结论。
