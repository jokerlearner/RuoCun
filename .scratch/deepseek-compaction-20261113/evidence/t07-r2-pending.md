# B-r2 隔离候选与最小修复

历史状态记录：本文件记录R1全量运行期间的**pending-root**准备阶段。主协调随后应用相同四行，根全部包输入已与R2相等；正式身份见[t07-r2-delivery.md](t07-r2-delivery.md)，原pending清单保留为[t07-r2-inputs-pending.json](t07-r2-inputs-pending.json)。

根来源为已绑定B-r1快照，R2副本为`D:\rcb-dd7453\r2`。仅修改`src/ruocun/session/log.py`两导出入口：

```python
if not directory.parent.exists():
    ensure_private_dir(directory.parent)
ensure_private_dir(directory)
```

每入口只增加两行；既有父容器不更改ACL，最终exports目录继续原私有目录/原子发布约束。其余受控源码、资源、README/许可/锁与R1逐字节相同。

- [派生过程](t07-derive-r2/command.json)与[输入清单](t07-r2-inputs.json)；来源明确为`derived-from-b-r1-pending-root`，`root_applied=false`，不宣称根工作区漂移0。
- `D:\rcb-dd7453\artifacts-r2`含sdist及重建wheel，`direct-r2`的直接wheel与其SHA相同。
- [绑定](t07-bind-r2-pending/command.json)及[314成员报告](t07-r2-artifacts-pending.json)：R2副本、sdist、两个wheel及实际pure-r2目录精确相等；新旧R1安装未被覆盖。
- pure-r2：`D:\rcb-dd7453\pure-r2\Scripts\python.exe`，仅runtime哈希依赖，无pytest。
- qa-r2：`D:\rcb-dd7453\qa-r2\Scripts\python.exe`，官方哈希dev/runtime依赖、R2 wheel和实际非editable测试支撑wheel。两环境pipcheck通过。
- [manual helper预制检查](t07-r2-manual-prepare/command.json)：全新`D:\rcb-dd7453\manual-r2/workspace`，仅创建workspace，**没有预建`.ruocun`**，公开压缩/会话/当前投影导出链通过。该模式不启动真实终端，不标记视觉或缩放通过。
- source-free T06两案交独审在pure-r2定向复验；不重新执行无关集成。

待主协调R1全量结束后应用相同四行，再核根全部受控输入与R2相等；通过后才发布正式R2输入身份及交付副本。R1原失败、包和回执保持可查。
