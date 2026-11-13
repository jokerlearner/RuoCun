# 10 Edit / Write 来源补齐

派发基线 `5afc65f`。`edit_file.py` 保留原读前检查、基线复核和同路径锁，补齐来源
findActualString、diagnoseMismatch 和 buildEditHunk。诊断长度与位置按 UTF-16 单元。
`write_file.py` 保留整写验证规则和原子替换，补齐来源提示和英文结果。

四段中英文描述从冻结源的字面量拼接提取，经过实际 registry 序列化断言。
现有 Edit 9、Write 10 项继续适用。新增迁移 mismatch 16、hunk 3、锁 4、原子写 2 项。
锁测试沿同 key 串行、不同 key 可并行、抛错解锁和透传断言，采用现有线程锁接口。
ADR-0011 的空 old_string 拒绝、Edit 基线检查和区外审批继续适用。

`n2-edit-support-red` 保留缺少源接口时的失败。`n2-edit-metadata-red` 保留四项
描述或英文结果失败。`n2-edit-source-green` 含 44 项来源路径和 5 项既有适配，共 49 项。
定向 Ruff 与 mypy 两个源文件通过。测试经既有白名单启动器在私有环境显式导入本树源码。
产品、测试、归档成员与 raw 证据 hash 见 `source.json`。REC-05 恢复另有提交。
