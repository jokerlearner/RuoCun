# A02 私密文件端口：目录边界修复候选

**状态更正：初始 `02fcb71` 独立复核未通过，不能按下文17项旧绿验收。** `exclusive_write` 不能阻止 FILE_WRITE_ATTRIBUTES 句柄设置重解析点；保护文件的绝对 CreateFileW 也可能经短时 junction 落入替代目录后，目录恢复原状使后检误过。泛化 readonly 空目录同样存在缺口。后续修复和最终契约以 [r2补充](../sprint-platform-r2/README.md) 为准；下文保留首轮假设和失败过程，不再将其作为已证实结论。

2026-11-10；分支 `impl/07-store`，保存原未提交身份用例后合入启动记录 `092b1cc`。本目录只交平台子集独立审查，不关闭07，不解锁58；原历史探针与两个未知对象未读取内容、未改名、未删除、未重跑。

## 来源、根因与诊断循环

独立预期来自 REC-12、ADR-0005 和 D09「私有父目录→同目录临时→替换→目录同步」契约，且此前独立复核 `codex/review-platform07-r3` 已报告目录替换窗口。本次新测试重新创建全新 pytest 沙箱：私密目录、替代目录、旧合成值均位于该沙箱内；所有路径操作用普通绝对路径。未使用 NtCreateFile、原生相对重命名结构或历史探针。

`junction-red`：一次 `atomic_publish`，仅在系统 `os.replace` 边界注入目录改名与 junction。替代目录的 `old-synthetic` 实际变为 `new-synthetic`，0.34秒失败。这是最小红信号，不是“未抛异常”的弱断言。测试结束只用 `os.rmdir` 移除本次创建的明确 junction，未递归遍历它。

检验的假设及预测：

1. 瞬时路径检查缺少 I/O 全程绑定；不共享 DELETE 的句柄使叶目录改名返回拒绝。
2. 仅固定最后一级不能保护祖先；逐级持有目录句柄后祖先改名也返回拒绝。
3. 禁止删除本身不能证明禁止重解析元数据；用不可删除的零字节保护文件维持非空，真实 FSCTL_SET_REPARSE_POINT 返回145（目录非空）。
4. 空目录到首个文件之间仍有窗口；先用不共享 WRITE/DELETE 的目录 RW 句柄，再创建唯一 DELETE_ON_CLOSE 保护文件，最后转为允许目录同步的只读属性句柄。

修复采用 `PrivateDirectory`：逐级 `CreateFileW(FILE_FLAG_OPEN_REPARSE_POINT|FILE_FLAG_BACKUP_SEMANTICS)`，直接核验各目录句柄属性；全程不共享 DELETE；保护文件持有不共享 WRITE/DELETE 的句柄，关闭后由系统删除。保护文件不含内容。已存在目录只验证私密owner/DACL，不接管ACL。不能建立边界或关闭句柄未确认均明确失败。

微软原始契约：[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew) 的共享模式与重解析标志；[FSCTL_SET_REPARSE_POINT](https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/fsctl-set-reparse-point) 明确非空目录不能设置重解析点；[FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers) 要求写权限句柄。普通成功不构成断电保证。

## 可复验命令与结果

所有命令经 `tools/run.py --state .cache/sprint07`：显式环境白名单、合成HOME/APPDATA/TEMP；所有归档 command.json 的 `sensitive_match=false`。每次产品改动后先通过 `pip install --no-build-isolation --no-deps .` 安装候选，再运行测试。

```powershell
.venv\Scripts\python.exe tools/run.py --label independent-platform --state .cache/independent07 -- .venv\Scripts\python.exe -m pytest tests/test_private_files_windows.py tests/test_private_files_race.py -q
```

- `junction-red`：1 failed（准确捕获替换重定向）。
- `junction-green`：1 failed。此轮发现 venv 仍是旧安装副本，因此保留为环境偏差证据，不算修复结果。
- 安装当前候选后的 `junction-green-current`：1 passed。
- `junction-ancestor-metadata`：3 passed，分别叶目录、祖先与真实元数据路径。
- `platform-regression`：17 passed；此后增加句柄关闭错误报告。
- 重新安装最终平台候选后的 `platform-final`：17 passed，22.54秒。含原有ACL、占用、临时清理、同步失败、中断回执测试。

## 58 可沿用的契约

`ruocun.platform.windows.durable_file`：

- `ensure_private_dir(Path) -> str`：返回已验证私密目录的SDDL；已有不合规目录拒绝且不改ACL。
- `atomic_publish(Path, bytes, *, require_durability=True, sync_directory_fn=None) -> PublishReceipt`：参数与现有候选兼容，整个发布期绑定目录。`sync_directory_fn`仅为已登记故障注入seam。
- `AtomicPublishPreReplaceError` 保留原错 `__cause__`、`cleanup_error`、`retained_path`、`replacement_uncertain`、`publish_receipt`；替换调用抛错时不猜测旧值仍在。
- `PublishDurabilityError.receipt` 明确已可见、持久未确认；系统中断保持原异常类型并附回执。
- `PrivateDirectory(Path, readonly=False)`：长期I/O使用的上下文，供SQLite保持至连接关闭；58的单次原子发布不必直接使用。只读模式不创建目录或保护文件。
- `verify_private_file(Path) -> str`：拒绝重解析、非普通文件、硬链接及非私密owner/DACL，供SQLite库与sidecar检查；不替代保持目录上下文。

## 未验及资源

本候选是本机Windows x64产品平台路径测试，未做独立账户、断电、其他文件系统/平台、wheel/standalone最终产品或用户体验验收；不承诺抵御任意恶意同账户进程、驱动或管理员。未运行真实模型或读取真实秘密。新测试创建的子进程均等待退出；测试保护句柄关闭后保护文件消失。原异常对象和历史输出仍保留且不纳入提交。
