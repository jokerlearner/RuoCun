# Edit 失败路径与账户选择器的小范围简化

- Type: task
- Status: resolved
- Blocked by: none
- Scope: current
- Assignee: root
- 用户体验验收：not-required（保持现有行为的内部简化）

## 授权与范围

用户确认执行上轮只读检查第1、2项，保持原行为，运行相关现有测试，最后分模块统计代码量。
只改 tools/edit_file.py 与 tui/app/app.py；保留此前工作树中的其它改动，不处理demo入口或其它架构候选。

## 验收条件

1. Edit 匹配失败后直接抛出相同 ToolRejected 消息；保留 findActualString、diagnoseMismatch 独立接口、精确/形近匹配、唯一性、锁、读基线、原子写和回调顺序。
2. 账户选择器仅删除冗余 adding 状态及不可达退出；保留列表选择、删除模式取消、切换返回、新增步骤和全部 await/异常顺序。
3. 相关现有测试、定向Ruff/mypy通过，不改测试断言、不增加用例矩阵。
4. 报告当前 src/ruocun 各一级模块的Python文件数和代码量；源码、注释、空行与资源分开说明。

## 验证证据

已完成两处简化。对比本轮474个Python文件的改前哈希，仅两个授权源码文件变化，测试未改，合计减少6物理行。

相关现有测试61 passed in 34.95s；两个源码的Ruff检查及mypy通过；独立静态复核通过。

实现状态：resolved。自动验证：passed。用户体验验收：not-required；未将自动结果表述为真实Windows Terminal验收。

详见 [本轮交付记录](../README.md)、[范围校验](../scope-verification.json)、[统计快照](../code-metrics.json) 和 [原始回执](../evidence/)。未提交Git。
