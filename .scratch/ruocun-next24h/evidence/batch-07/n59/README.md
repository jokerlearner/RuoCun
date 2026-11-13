# 59 定时路由

冻结来源`dao-f17e189-7ac654a0dc06`：src/schedule.ts:1–53及schedule.test.ts:4–17，src/tools/schedule_tool.ts/test.ts，src/tools/cron_tools.ts；目标范围按ADR-0010/W3及本票。单独src/ruocun/schedule.py供四个工具和操作员CLI共同调用，不增加Windows Task Scheduler/dispatcher或会话内Cron。

来源构造/转义、工具缺参各有red→green；4项紧凑来源/必要确认通过：纯crontab行、合成POSIX命令端口的add/list/remove及保留其它任务、Windows四工具的实际动作全部拒绝且后端零调用、真实受控命令先写合成effect后取消并确认进程句柄已退出且结果仍unknown。后者仅本测试独占Python命令，不调用系统crontab、不修改用户电源。Ruff、Mypy通过；原红/绿及命令环境见raw，scan_hit=false。

buildCronLine保留来源shell单引号转义、cron原谓词、工作区cd、日志和marker；写本项目~/.ruocun/schedule.log及# ruocun-schedule，不消费/删除旧DAO标记任务。Python标准包启动窄适配为精确解释器加'-m' 'ruocun'，避免到点只启动空Python REPL。公开ScheduleService注入runner/platform/environ仅是命令端口；普通单例使用真实平台，Windows的create/list/remove均返回明确Error而非成功/空表。操作员可按helper bool返回区分成功与拒绝。

两项来源已知不一致准确保留/说明：CronCreate省略durable实际走OS，显式false才拒绝；recurring=false仅在prompt中加手动删除提示，不会自动删除。描述与schema说明窄改为真实行为，未添内存调度或单次系统触发器。来源cron校验仍是5字段前缀谓词，没有增加不同语法/cron解析器。

已批准的信息保留差异：源readCrontab把所有错误当空表，可能将读失败后的旧任务覆盖。现在只有明确'no crontab for'的缺表结果可视为空，其它读失败在写前ToolRejected，旧任务不变；写入开始后的取消/非成功确认保持UnknownToolOutcome且不重放。命令取消收口拥有的进程/组；POSIX系统实际crontab触发和macOS/Linux实机未运行，不写为通过。

公共组合根由主协调注册scheduleTool/cronCreateTool/cronDeleteTool/cronListTool及CLI schedule add/list/remove，普通入口与独审另验。Status保持claimed，候选不代填整票结题、真实系统任务或体验通过。
