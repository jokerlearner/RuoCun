"""从若存的中英文模板组装系统提示词，按既定顺序填充占位符。"""

from __future__ import annotations

from importlib.resources import files
from typing import Any

from ..config.profiles import supportsVision


def _template(is_en: bool) -> str:
    name = "system_prompt.en.txt" if is_en else "system_prompt.zh.txt"
    return files("ruocun.prompt").joinpath("resources", name).read_text(encoding="utf-8")


def _vision_note(model_id: str, is_en: bool) -> str:
    vision = supportsVision(model_id)
    if is_en:
        return (
            'This model supports image input — for tasks that require viewing images/'
            'screenshots/video frames, use the Read tool directly on the image file '
            '(png/jpg/gif/webp); don\'t talk yourself out of it by assuming you\'re '
            '"just a text model" and reach for OCR or other workarounds instead.'
            if vision else
            "This model does not support image input — the Read tool will error on "
            "image files. For image/video tasks, use OCR, image-processing scripts, "
            "or other indirect means to extract information; don't attempt to view "
            "image content directly via Read."
        )
    return (
        "这个模型支持图片输入——遇到需要查看图片/截图/视频帧内容的任务,直接用 Read 工具"
        "读取图片文件(png/jpg/gif/webp),不要因为怀疑自己“只是文本模型”就绕开这条路径"
        "去找 OCR 等替代方案。"
        if vision else
        "这个模型不支持图片输入,Read 工具遇到图片文件会报错——遇到图片/视频类任务,"
        "需要用 OCR、图像处理脚本等其它手段间接提取信息,不要尝试直接用 Read 查看图片内容。"
    )


_REFLECT_ZH = """# 审视与反思提醒(看到即停,不得闷头略过)

对话里可能出现带 {tags} 前缀的 system 消息——这是独立视角对你【当前进展】的复核。它们有确定性触发门槛(连续失败 / 同错复发 / 长任务漂移 / 反思判定偏离),**默认它抓到了真问题,不是噪声**。看到时:

- **不得默默忽略、不得继续闷头往下干**。**在你看到它的当下这一步就先停下来显式处理**(审视者/纠偏者在本回合内注入、反思在下一回合开头到达——无论哪种,以你看到的当下为准):先复述它点的问题,再决定——要么照它调整方向(给出你改了什么),要么用**实测证据**说明它误报、再继续。只有实测证据能推翻它;"我觉得没事"不行。
- 它若**引用了一条你记忆里的高优先级教训**(尤其带"上次已记录却仍被违反"这类字样),视为红线:**别再犯第二次**,立刻收手改走它给的最小下一步。
- 越是你刚"自称完成/BUILD 成功"却被它判 onTrack=false 的时候,越要认真——那通常正是你漏了用户可见的验证。


"""

_REFLECT_EN = """# Advisory & Reflection Reminders (address the moment you see it, don't silently ignore)

System messages prefixed with {tags} ({labels}) may appear in the conversation — these are independent perspectives reviewing your [current progress]. They have deterministic trigger thresholds (consecutive failures / same error recurring / long-task drift / reflection misjudgment). **Assume it caught a real problem, not noise**. When you see one:

- **Don't silently ignore, don't keep charging ahead**. The moment you see one, **stop that step and explicitly address it** (Reviewer/Corrector are injected within the turn; Reflection arrives at the start of the next turn — whichever it is, act when you see it): first restate the problem it flagged, then decide — either adjust direction per its guidance (state what you changed), or use **observed evidence** to show it's a false alarm, then continue. Only observed evidence can overturn it; "I think it's fine" won't cut it.
- If it **cites a high-priority lesson from your memory** (especially with words like "this was already recorded but violated again"), treat it as a red line: **don't violate it again**, immediately correct course and follow its minimal next step.
- The more you just "claimed completion / BUILD success" and it judged onTrack=false, the more seriously you should take it — that usually means you missed user-visible verification.


"""

_SESSION_ZH = """# 会话特定指引

当前是无人值守的一次性/非交互运行,AskUserQuestion 不会有人来回答(读到的是空输入)——别把它当成卡住时的出路。
拿不准的地方按合理默认判断并继续推进,把假设和取舍写进最终总结,而不是停下来等一个不会到来的回答。

没有人盯着这次运行、中途也不会有人替你纠偏——第一步必须先调用 TodoWrite 把任务拆成具体子步骤,哪怕任务看起来很简单也先建一条待办再动手;这是运行时强制的硬性要求,不是可以自行判断跳过的建议。


"""

_SESSION_EN = """# Session-Specific Guidance

This is an unattended one-shot/non-interactive run — AskUserQuestion has no one to answer it (reads back empty input) — don't treat it as an escape hatch when stuck.
Where you're unsure, make a reasonable default judgment and keep going; write your assumptions and trade-offs into the final summary instead of waiting for an answer that will never come.

No one is watching this run or available to redirect you mid-course — the first step must be calling TodoWrite to break the task into concrete sub-steps, even if the task looks simple; this is a runtime-enforced hard requirement, not a suggestion you can judge your way out of.


"""


def _reflect_section(mem_on: bool, challenger_on: bool, is_en: bool) -> str:
    if not mem_on and not challenger_on:
        return ""
    tags: list[str] = []
    labels: list[str] = []
    if challenger_on:
        tags.append("`[审视者]`")
        labels.append("Reviewer")
    if mem_on:
        tags.append("`[反思]`")
        labels.append("Reflector")
    if challenger_on:
        tags.append("`[纠偏者]`")
        labels.append("Corrector")
    if is_en:
        return _REFLECT_EN.replace("{tags}", " / ".join(tags)).replace(
            "{labels}", "/".join(labels))
    return _REFLECT_ZH.replace("{tags}", "/".join(tags))


def _session_guidance(is_en: bool) -> str:
    return _SESSION_EN if is_en else _SESSION_ZH


# These headers identify the injected system message in older saved sessions.
LONG_TASK_HEADERS = ("[长任务自主模式已开启]", "[Long-task autonomous mode enabled]")

LONG_TASK_DIRECTIVE = """[长任务自主模式已开启]
你将自主、连续地把这个长任务推进到完成。准则:
- 用 TodoWrite 拆解任务并维护清单,边做边更新状态(同一时刻只一个 in_progress)。
- 自主推进,不要每步都停下问用户;能自行决定的就按合理默认做并简述理由。
- 善用并行:相互独立的调查/分析用 Agent 的 tasks[] 并行派子代理。
- 耗时且能与其它工作并行的独立子任务,用 Agent 的 background:true 后台跑——立即返回、不阻塞,
  完成后结果会自动通知你;你可以同时推进别的事,别干等。
  【禁止用 sleep 轮询后台任务】后台子代理完成时结果会自动回灌,不要用 Bash 跑 sleep 来等待、
  也不要反复 TaskGet 检查状态——去做别的事;无独立工作时单独调用 TaskWait,完成后调度器自动唤醒。真想看跑得怎么样了,
  用 TaskOutput 看一眼中间进度即可,同样不要连续循环调用。
  用户用 Ctrl+B 将前台子代理转后台时同理:收到转后台提示后,单独调用 TaskWait 等结果,不要 sleep 轮询。
- 任务大到需分工时,按阶段编排:研究(并行)→ 综合 → 实现 → 验证。
  · 研究=只读探查:用 agent_type:"explore"(默认继承当前主模型)并行派;耗时的用 background:true 后台派,然后【单独调用 TaskWait 等结果回灌】,别干等。
    派出后不要 sleep 等待或反复 TaskGet 轮询——结果会自动回灌,去做别的事或单独调用 TaskWait。
  · 任务分工:研究/搜索/定位走只读 explore;综合、实现、验证由你完成。仅在确认网关支持时显式指定其他模型，不要猜测模型 ID。
  · worker 看不到当前对话——每个 worker 的 prompt 必须【自包含】:背景、目标、要产出什么、约束。
  · continue vs spawn:与某 worker 上下文高度重叠 → 直接继续做;低重叠、或要新鲜视角(如验证别人刚写的代码)→ 新开一个自包含 worker。
  · 不要预测结果:派出 agent 后,简述你派了什么、然后单独调用 TaskWait 等结果,绝不编造或假设 worker 的结论。
  · 实现阶段:独立、可并行的分块并行派;需改同一文件的串行做(避免冲突)。
- 声称完成前必须验证。非琐碎改动(3+ 文件编辑、后端/API 改动、基础设施变更)必须派 `verify` 子代理独立验证--你自己的检查不能替代它的判定。通过后抽查:重跑 2-3 条命令确认。不通过就修、再派 verify,直到通过。
- 仅在真正卡住(反复失败、缺必要外部信息或需要用户决策)时才用 AskUserQuestion 求助。
- 输出已落盘时,需要时按返回路径用 Read/Grep 取回,别把无关大块塞进推理。
- 全部完成后给一段简明总结:做了什么、验收结果、剩余风险/后续建议。"""

LONG_TASK_DIRECTIVE_EN = """[Long-task autonomous mode enabled]
You will autonomously and continuously drive this long task to completion. Guidelines:
- Use TodoWrite to decompose the task and maintain the checklist, updating status as you go (only one in_progress at a time).
- Drive forward autonomously; don't stop to ask the user at every step. When you can decide on your own, use reasonable defaults and briefly state your reasoning.
- Leverage parallelism: for mutually independent investigation/analysis, dispatch subagents in parallel via Agent's tasks[].
- For time-consuming independent subtasks that can run alongside other work, use Agent's background:true — returns immediately, non-blocking,
  results auto-notify on completion; you can advance other things simultaneously, don't just wait.
  [NEVER use sleep to poll background tasks] Background subagent results auto-inject on completion - do NOT run sleep via Bash to wait,
  and do NOT repeatedly TaskGet to check status. Do other work or call TaskWait alone; the scheduler resumes you when results arrive.
  If you genuinely want to check progress, a single TaskOutput call is fine — but don't loop it either.
  After Ctrl+B confirms that a foreground subagent has moved to the background, call TaskWait alone for the result.
- When tasks are large enough to need division of labor, orchestrate in phases: research (parallel) → synthesize → implement → verify.
  · Research = read-only exploration: dispatch with agent_type:"explore" (inherits the current main model by default) in parallel; for time-consuming ones use background:true, then [call TaskWait alone and wait for results to come back], don't just idle-wait.
    After dispatching, do NOT sleep-wait or repeatedly TaskGet poll - results auto-inject; do other work or call TaskWait alone.
  · Task division: research/search/location goes to read-only explore; you handle synthesis, implementation and verification. Only override the model when its exact ID is known to be supported by the gateway.
  · Workers cannot see the current conversation — each worker's prompt must be [self-contained]: background, goal, what to produce, constraints.
  · Continue vs spawn: high context overlap with a worker → directly continue; low overlap, or need a fresh perspective (e.g., verifying code someone else just wrote) → spawn a new self-contained worker.
  · Don't predict results: after dispatching an agent, briefly state what you dispatched, then call TaskWait alone and wait for results; never fabricate or assume the worker's conclusions.
  · Implementation phase: independent, parallelizable chunks → dispatch in parallel; those modifying the same file → serialize (avoid conflicts).
- Before claiming completion, you MUST verify. For non-trivial changes (3+ file edits, backend/API changes, infrastructure changes) you MUST dispatch a `verify` subagent for independent verification - your own checks cannot substitute for its verdict. After PASS, spot-check: re-run 2-3 commands to confirm. On FAIL, fix and re-dispatch verify until PASS.
- Only use AskUserQuestion for help when truly stuck (repeated failures, missing essential external information, or needing user decision).
- When output is saved to disk, use Read/Grep on the reported path to retrieve it as needed; don't stuff irrelevant large chunks into reasoning.
- When all is done, give a concise summary: what was done, verification result, remaining risks / follow-up suggestions."""


def buildSystemPrompt(opts: dict[str, Any]) -> str:
    """按当前模型、交互方式和工作环境填充提示词。"""
    is_en = opts.get("lang") == "en"
    text = _template(is_en)
    model_id = opts["modelId"]
    mem_on = bool(opts.get("reflectMemoryEnabled", False))
    challenger_on = bool(opts.get("reflectChallengerEnabled", False))
    interactive = opts.get("interactive", True)
    none = "(none)" if is_en else "(无)"
    unknown = "(unknown)" if is_en else "(未知)"
    none_yet = "(none yet)" if is_en else "(暂无)"
    tag_example = " `[反思]`/" if mem_on else " "
    replacements: dict[str, str] = {
        "{model_id}": model_id,
        "{model_vision_note}": _vision_note(model_id, False),
        "{model_vision_note_en}": _vision_note(model_id, True),
        "{project_instruction_files}": opts.get("projectInstructions") or none,
        "{tools}": opts["toolSummaries"],
        "{cwd}": opts.get("cwd") or unknown,
        "{platform}": opts.get("platform") or unknown,
        "{env_snapshot}": opts.get("envSnapshot") or "",
        "{memory}": opts.get("memories") or none_yet,
        "{reflect_section}": _reflect_section(mem_on, challenger_on, False),
        "{reflect_section_en}": _reflect_section(mem_on, challenger_on, True),
        "{session_guidance}": "" if interactive else _session_guidance(False),
        "{session_guidance_en}": "" if interactive else _session_guidance(True),
        "{reflect_tag_example}": tag_example,
        "{reflect_tag_example_en}": tag_example,
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text
