# 平台复核反例修复：绝对名称原子拒绝重解析

2026-11-10；A02/07平台子集，仍待独立复核，不关闭07/58。原探针和未知对象保持原样。本轮未使用相对创建、相对重命名或原历史输出；未改已有真实目录ACL。

## 反例及修复

独立review实际证明了首轮假设错误：共享模式不限制纯属性访问。默认写分支的空目录→guard窗口中，第二进程可设置junction，原CreateFileW在替代目录创建guard；第二进程撤销tag后，PrivateDirectory错误地成功进入。另有readonly空目录反例。首轮17绿仅覆盖其原测试，不能冲销这些失败。

经root确认本次内部实现方向，改用 `NtCreateFile` 的**绝对本地NT路径**，`RootDirectory=NULL`，`OBJ_DONT_REPARSE|OBJ_CASE_INSENSITIVE`。系统在一次名称解析中遇重解析即拒绝，不允许先检查后跟随；`FILE_CREATE` 唯一创建零字节guard，`FILE_DELETE_ON_CLOSE` 交由同一持有句柄清理。没有任意用户数据写入此原生辅助口。`FILE_SYNCHRONOUS_IO_NONALERT|SYNCHRONIZE` 强制同步完成，不引入悬挂OVERLAPPED或原生异步材料。

`UNICODE_STRING`、`OBJECT_ATTRIBUTES`、`IO_STATUS_BLOCK` 按官方结构自然对齐；实际调用前限定Windows x64，检查指针/结构尺寸 `(8,16,48,16)` 和关键偏移 `(16,24)`，并核验返回NTSTATUS、最终IO_STATUS_BLOCK及 FILE_CREATED/FILE_OPENED。没有变量长度内联名称结构。官方依据：[OBJECT_ATTRIBUTES及OBJ_DONT_REPARSE](https://learn.microsoft.com/en-us/windows/win32/api/ntdef/ns-ntdef-_object_attributes)、[Nt/ZwCreateFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-zwcreatefile)。

readonly不创建目录或guard，必须显式提供一个既有的单段 `anchor_file`，用相同原子拒绝重解析路径打开；保持 FILE_READ_DATA 权限的句柄以启用共享检查，但不读取内容。没有anchor、空目录、缺失文件、重解析/硬链接/非私密owner/DACL均失败。仅属性权限的句柄经实际测试不能阻止anchor被删除，因此此轮新增删除回归先红，再补FILE_READ_DATA后转绿。锚文件不共享DELETE，目录在只读操作期保持非空；逐级目录pin仍禁止改名。

## 新反馈环

`tests/test_private_files_race.py` 的系统边界代理只暂停实际 `NtCreateFile`；真正第二进程以FILE_WRITE_ATTRIBUTES在本次明确的 sibling `private/alternate` 沙箱上设置junction，系统调用实际执行后，仍经第二进程的同一目录句柄撤销tag并确认退出。

- 写guard窗口：必须抛 AtomicFileError，PrivateDirectory不成功进入，原目录与替代目录均无新增对象。
- readonly锚窗口：先删除本次合成anchor，再由第二进程设置junction；原子打开必须拒绝，未读取/创建替代材料。
- readonly空目录明确拒绝；有效anchor在持有期不能删除，关闭后原字节不变。
- guard自身在持有期不能删除，退出后由系统清除。

`native-window-green` 首次为4 passed/1 failed（anchor可删，保留原失败）。修正访问权限后 `native-window-anchor-green` 5 passed；增加只读创建窗口后 `native-both-window-green` 6 passed。`platform-r2-all` 旧平台与新窗口共20 passed，24.07秒；之后只补关闭失败时保留原错和可重试句柄、整理导入。重新安装最终候选后 `platform-r2-boundaries-final` 6 passed，`platform-r2-mypy` 和 `platform-r2-style-fix` 通过。所有归档运行器均为白名单+合成状态，`sensitive_match=false`。

## 精确API

`ensure_private_dir(Path)->str`、`atomic_publish(Path,bytes,*,require_durability=True,sync_directory_fn=None)->PublishReceipt` 及所有既有错误/回执字段保持不变。

内部兼容扩展：`PrivateDirectory(Path, *, readonly=False, anchor_file=None)`。写模式使用临时guard；只读模式必须指定既有文件锚，例如SQLite传 `anchor_file="session.db"`。只读目录层不创建保护文件，不等同SQLite WAL读连接绝无锁元数据变化；数据库层另做实际证据，不能从本子集推论。`verify_private_file`契约保持。

未验：独立账户、断电、其它卷/平台、产品安装产物及用户体验；恶意同账户任意权限修改、管理员/驱动不在本子集实测范围。新子进程均communicate确认退出、tag同句柄撤销、guard关闭后消失；历史材料仍保留。最终是否接收以独立复核结果为准。
