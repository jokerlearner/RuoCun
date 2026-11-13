# A 独审修正：严格 JSON 常量

独审发现 Python `json.loads` 默认接纳 `NaN/Infinity/-Infinity`，冻结 `JSON.parse` 拒绝。
权限配置、trust receipt、approval 表读取现统一拒绝非 JSON 常量：读侧按来源返回空配置/
不可信/空集；写侧抛出异常并按 ADR-0013 保留原字节。身份与引擎的直接参数解析也拒绝同类
输入，避免与源 API 语义分歧（普通 Registry 入口本来已拒绝这些常量）。

只复用原 `missing_and_bad` 与损坏文件保留 fixture，验证包含有效 bypassMode 的坏整文不会启用
模式，且三种坏文件不被修改。未扩大边界矩阵，未重跑 A 全部 392 项。
`n1-a-json-review-red` 为两项确定失败，green 修正后通过；Ruff 与 mypy 5 源文件通过。
原始命令和输出及本次修改产品 hash 保存在 `json-review/`。
