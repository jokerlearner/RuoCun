# 03 同步既有维护测试夹具的请求识别

- Type: task
- Status: resolved
- Blocked by: none
- Scope: current（验证所需最小夹具修复）
- Assignee: root
- 用户体验验收：not-required

完整回归发现模拟服务还匹配旧记忆维护提示词，当前产品提示在本轮开始前已经改变。
改前源码快照复现同一等待事件超时；只把请求识别子串同步为当前提示的“记忆提出合并计划”。
82个assert的AST、等待时限、模拟响应与并行验证逻辑逐一保持，独立Spec审查确认。

实际结果：新包QA中原3个失败项19.06s全部通过；原全量及中间复验的失败回执保留。
见[交付记录](../README.md)和[断言保留核对](../evidence/fixture-preservation.json)。
