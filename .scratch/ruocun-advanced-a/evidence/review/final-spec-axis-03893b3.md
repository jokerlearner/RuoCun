# 阶段 A 最终独立 Spec 轴

固定范围：`cb074ee15018aa5b477babfe63040134f4c4d838` → `03893b3e5b7762557a23d3a0e869d5a1c209026b`。只读审查产品与来源，未修改产品/测试；真实模型/API 0 调用。Standards 由另一审查者负责。

1. **[P2][实现错误] 合法 Skill 描述可能使请求发送失败。** 规格 `spec.md:11` 要求“静态Skills发现/frontmatter子集……可用；启动只放目录”。`src/ruocun/skills/skills.py:37–38` 在第 220 个 UTF-16 单元切断 emoji 时生成孤立代理项；与 `client/client.py:420` 的严格 UTF-8 编码组合后不可发送。最小确认：描述为 `'a'*219+'😀'`，目录末尾变成 `a\ud83d`；现有 `streamChatResilient` 返回 `failed/UnicodeEncodeError`，合成 transport 调用 0 次。已安装模块 SHA256 `cf62a2ee86016ffd772bba73c11597e1820c0b0811488d9fa10d5a99e8b555ed` 与固定源码一致。DAO 的 `JSON.stringify` 能转义该代理项；需补齐 Python 编码适配。

2. **[P2][部分缺失] 兼容诊断没有生效/覆盖结果。** D09 唯一契约 `.scratch/ruocun-discovery/research/09-storage-extension-route.md:127` 要求“界面/诊断显示……是否生效/被覆盖”。`src/ruocun/agent/runtime.py:119–129` 仅读取路径，统一报告“可读取；具体覆盖按本资源规则”。同名兼容 Skill 被原生项覆盖、兼容 profiles 被原生 config 遮蔽时，用户仍无法从诊断辨认实际采用者。

3. **[P2][实现错误] 压缩保存未确认仍显示已保存。** 规格 `spec.md:13` 要求“压缩取消/未提交均保留可信保存点”，D09:77 要求“返回新revision后才内存ack”。`Conversation._commit:142–145` 在等待异常时置 `blocked`，压缩控制器将异常转为停止结果；`src/ruocun/agent/runtime.py:358` 却先打印旧 revision 的“已保存”，359–361 才声明保存未确认。应在 blocked 检查后发当前回合成功标记，或明确只是旧保存点；未发现数据丢失或工具重放。

范围外行为：0 项。旧全票未结题、未来 N0、真实模型和人工体验 pending 均未计为本批缺陷。其余入口、输入账本、未决工具保护、费用/预算 R1 口径及实际 effort 字段未发现本轴确定问题；没有扩大测试矩阵。
