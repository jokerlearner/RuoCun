# 21 用户问答与可见消息工具候选

本票经主协调按24小时计划的独立备选任务派发，前置11已通过。工具源码写入冻结对应表指定的 `tools/ask_user.py` 和 `tools/send_message.py`，共享runtime/schema/types由主协调维护。

来源为唯一冻结快照 `f17e189 / 7ac654a0dc06` 的 `src/tools/ask_user.ts`、`ask_user.test.ts`、`send_message.ts`、`i18n/messages/zh.ts` 和 `en.ts`。两工具的中英文描述按来源字符串保持，schema保留选项/问题数量、字段描述、必填和常驻属性。AskUserQuestion read/auto，SendUserMessage plan/auto。

Ask保留单问和多问二选一、结构化选项转label-description、单/多选回调、空白未回答及缺回调失败。多问题的讨论意向会标记未问后续并停止弹出。只有明确signal已取消才返回中断文字，空白答案仍为来源未回答。Send保留原message与附件内容返回、工作目录相对路径、读取失败文字、4000 UTF16单位截断及proactive的100单位notifyUser回调。当前范围的notifyUser仅为终端提示。

## 实际验证

使用既有 `tools/run.py` 白名单和 `.cache/n21` 合成HOME/配置/TEMP，根venv的 `-I -c` 显式加载本worktree/src并运行本worktree测试。命令及stdout/stderr保存raw，敏感值扫描无命中。

- `n21-source-initial` 实际10通过/1失败。handler来源断言通过，失败明确定位共享schema未实现minItems/maxItems。保留失败，待root补齐并复验。
- `n21-tools-ruff` 两工具和测试检查通过。
- `n21-tools-mypy` 两工具严格类型检查通过，类型字段来自主协调48cc6fb。

完整普通入口的工具注册、同owner问答选择与取消、模型续轮、用户可见正文/附件以及独立审查仍待主协调接线验收。不会用工具层返回值测试代填用户可见或实机结果。21保持claimed。
