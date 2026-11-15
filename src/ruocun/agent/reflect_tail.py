"""为轮末反思提供系统指令，规定如何提取记忆候选和核对任务进度。"""

REFLECT_TAIL = """复核本次对话，交给若存一份结构化记录。只返回一个 JSON 对象。

先找值得下次继续使用的信息。检查用户纠正、重复要求、对验收的追问或确认，以及从实际失败中查明的解决办法。区分用户明确要求、跨轮观察和从运行证据得出的技术结论。把规则和适用条件留下，一次性操作、容易查到的目录与历史、临时情绪、无用的重复信息略过。不要记录凭据或其他秘密。

现有条目：
{existing}

- 每项写 title、text、type、importance（1 到 10）、confidence（0 到 1）、source 和 mergeInto。type 可以是 feedback（协作规则）、user（用户偏好与背景）、semantic（稳定的项目事实）或 procedural（可复用步骤）。
- feedback 的 text 先写规则，再写“为什么:”和“怎么用:”。明确的纠正或重复要求可用 0.8 以上置信度。推断的偏好用 0.3 到 0.6。实测确认的技术经验可用 0.7 以上。source 用 user_stated、inferred 或实际文件名。
- 确实扩充已有条目时，mergeInto 填它的完整 title，text 填合并后可独立使用的内容。新条目填 null。
- 某条现有记忆被实测推翻或需要修订时，在 corrections 写 target、action（supersede 或 revise）、可选 newText、reason。confirmed 只列本轮实际依赖并再次验证的已有标题。

然后比较用户的目标和眼下进度。从对话中找一到三个可核实的迹象，例如同一故障复发、错误的定位前提、验收遗漏、范围偏移、未核实的断言。刚开始或者按目标推进时设 onTrack 为 true，advisory 为 null。证据表明已经停滞或偏离时设 onTrack 为 false，advisory 用八行以内给出证据和一个可执行的核验步骤。note 用一行写正在做的事和判定依据。

返回键为 memories、onTrack、advisory、note、corrections、confirmed。没有记录时数组留空。"""
