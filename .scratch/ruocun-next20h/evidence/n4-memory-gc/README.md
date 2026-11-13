# 32 原生维护存储与 GC

冻结归档、来源文件和原始回执摘要见 `source.json`。白名单环境、私有 Python 3.11 venv 和显式源码导入，无真实或付费模型调用。

## 存储接缝

冻结 `memory/store.ts` 和 `memory/consolidate.ts:174–188` 的 Markdown 与 `.last-consolidation` 标记使用同一原生目录。维护端口仅处理原生作用域，条件写入和删除根据真实文件路径、原字节摘要及锁定状态重新核对，沿用既有进程内锁、私有数据目录和原子发布。

`test_n4_memory_maintenance_store.py` 验证手改字节、锁定和显式兼容原件不被写删，标记缺失返回 0，坏标记不覆盖。原格式/CRUD 回归随存储接缝定向执行。

- `n4-maint-store-red01` 两项缺方法。
- `n4-maint-store-green01` 新接口与原 CRUD 定向共 22 项通过。
- `n4-maint-store-ruff01`、`n4-maint-store-mypy01` 通过。

## GC

冻结 `memory/gc.test.ts` 的 26 项迁移到 `test_n4_memory_gc.py`，含日期、留存、墓碑、类型保护、宽限期与实际删留。两项原用例复用锁定保护断言，覆盖墓碑和过期取代条目。沿 ADR-0013，一项原生删除回执适配验证实际第二次删除后同步失败，只报告第一项已确认删除，第三项保留，并停止本作用域。配置可传小数宽限天数。

- `n4-maint-gc-red01` 缺模块，原红保留。
- `n4-maint-gc-green01` 27 项 GC 与原审核 8 项，共 35 项通过。
- `n4-maint-gc-ruff02`、`n4-maint-gc-mypy01` 通过。首次 Ruff 格式失败保留。

普通启动编排、蒸馏和合并属于主线组合验证。未运行真实模型、全量或打包。

## 合并替换的恢复副本

`publishExpected(..., preserveOriginal=True)` 在显式维护替换已有条目时生效。完成候选格式校验、旧条目元数据与字节摘要核对后，在同一私有目录耐久发布 `.〈文件stem〉.〈12位随机十六进制〉.bak`，回读原字节并重验当前条目，再替换 `〈文件stem〉.md`。已确认替换可清理该次副本，未确认则保留。正常加载只读 `.md`，副本不参与后续记忆查询。

需恢复时先停止该作用域的维护，核对现有 `.md` 与对应 `.bak`，确认取用旧版本后以副本原字节恢复到同目录对应 `.md`。维护入口不自动回滚或重试未确认替换。

`n4-maint-preserve-red01` 在原端口真实替换后注入目录同步失败，确认旧正文副本不存在。`n4-maint-preserve-green01` 保存首次候选的 Windows 长路径失败。缩短文件名后 `n4-maint-preserve-green02` 通过 23 项维护与原 CRUD 检查，证实已替换但未确认时保留含 CRLF 的准确旧字节，已确认替换清理本次副本。`n4-maint-preserve-ruff02` 和 `n4-maint-preserve-mypy02` 通过。
