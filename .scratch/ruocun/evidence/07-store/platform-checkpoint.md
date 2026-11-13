# 07 私有文件平台检查点（未结票）

范围：`ruocun.platform.file_contract` 与 `ruocun.platform.windows.durable_file`，供 07 和 58 后续使用。当前仅为候选，需要独立复核，不代表 07 完成或安全验收完成。

## 来源与边界

- D09 唯一 StoragePort/文件路线、ADR-0005、REC-12，以及 D18 最终独立复核所保留的 Win32 私有 ACL/同目录原子替换实验。
- 文件接口仅接受实际固定本地卷，不跟随已存在的重解析路径；新目录使用 Win32 创建时显式指定当前用户 SID 的受保护 OI/CI DACL。既有目录只检查，不调整 ACL；未达到私密条件则拒绝。具体检查是保守子集，不声称接受所有可能安全的 DACL。
- 临时文件在写入之前核验其继承 ACL；`os.replace` 后目录同步失败返回已发布但持久性未确认，不声称断电不丢。

## 自动检查

2026-11-10，Windows x64，项目独立 CPython 3.11 开发 venv；通过 `tools/run.py` 的环境白名单和合成 HOME/AppData/TEMP，以合成路径、合成内容运行。日志输出未命中本机敏感环境值；不提交机器身份或原始环境。

- `acl-existing-red2`：已有普通目录的 ACL 不应被修改，旧实现测试失败；后续候选在 `acl-existing-green` 通过。
- `acl-boundaries-1`：`python -I -X utf8 -m pytest tests/test_private_files_windows.py -q -p no:cacheprovider`，5 项通过。覆盖既有目录 ACL 原样保留、新目录与文件继承 ACL、真实占用目标拒绝替换且旧值不变、注入目录同步失败后确认新文件可见并返回未确认回执、真实 junction 拒绝写入。
- `postreplace-oserror-red`：替换后注入 `OSError` 时原候选未返回未确认回执；修正后 `platform-final2` 运行同一测试文件共 6 项通过，分别覆盖 `AtomicFileError` 与 `OSError` 的同步失败出口。
- 独立复核指出替换后还可能出现其它普通异常。`postreplace-general-red` 确认 `RuntimeError` 未携带回执；修正后 `platform-final3` 共 9 项通过，覆盖 `RuntimeError` 和 `KeyboardInterrupt`/`SystemExit` 注入。普通异常包装未确认回执，终止类异常保留原类型并附 `publish_receipt`；这不是异步/进程强杀可捕获的保证。
- 独立复核指出替换失败后的临时文件清理错误不能吞掉。`temp-cleanup-red` 首次失败；修正后保留原 replace 异常为 `__cause__`，并通过 `retained_path` 与 `cleanup_error` 报告合成临时文件可能残留。
- 独立复核指出现有 DACL 检查不能推断对象 owner。新增真实 Win32 owner 读回，仅接受当前用户 SID；`owner-check-red` 暴露原实现缺口，`platform-final4` 共 11 项通过，包括注入不同 owner 和 owner 查询失败的负例。负例在 OS 读回边界合成注入，并非独立账户实测。
- 第二轮复核指出 fsync 中断可能遗留临时文件、replace 调用中断不能断言旧文件仍在。`prereplace-interrupt-red` 与 `rename-interrupt-red` 保存对应失败；`platform-final5` 共 14 项通过。前者保留中断异常及清理结果，后者保留中断异常并附 `replaced=None` 的结果未知回执；模拟 replace 后立即抛异常属于注入，不能宣称观测到真实 Ctrl+C 时序。
- `recovery-private`：真实受控 SQLite 下，本票合成会话经独立进程保存、退出、恢复通过；仅说明文件候选能支持该具体路径，不代表全量恢复。

不在本检查点覆盖：独立用户账户访问、设备断电、恶意同账户进程、所有文件系统与每类底层 I/O 错误；Windows 平台最终门禁和用户体验验收仍待后续任务。
