# 当前日常入口已更新到B-r3

日期：2026-11-13（Asia/Shanghai）。用户明确授权更新现用安装、保留配置和会话，并复验启动/压缩/重启原文回查。本票[10](issues/10-install-current.md)完成；原09的终端视觉/缩放验收状态不改变。

## 实际入口

桌面「若存 Code.lnk」仍指向 `C:\Users\PC\Apps\RuoCun\Open-RuoCun.cmd`。启动器只将解释器目录从`venv-b09-r7`替换为`venv-compaction-b-r3`，原工作目录、Windows Terminal参数和`open_ruocun.py`均保持。

新解释器：`C:\Users\PC\Apps\RuoCun\venv-compaction-b-r3\Scripts\python.exe`。实际安装固定B-r3 wheel（SHA256 `3b34d7366716c4ec14fd01ef2b629cf26ef84aa11273ac513012b3fb2808baa4`），314产品成员及6项元数据/许可逐字节核对一致，仅运行依赖、无pytest；旧环境完整保留。[安装证据](evidence/deploy-20261113/README.md)

启动器旧SHA：`c6217892e074bec62487f2a77bbdc9fba63ce3fe10744a4cc0297dbb45a554ee`；新SHA：`1cda047d31c9a8ec3a39dd22e9ca47d24109e821a599099bfff7e508b88f8e8f`。桌面快捷方式目标未改变。

## 配置与会话保留

私有备份：`C:\Users\PC\Apps\RuoCun\rollback\compaction-b-r3-20261113`。备份不纳入源码或公开日志，保留28个原文件、启动器/包装器副本和6份SQLite一致性备份；本次旧登记外部附件为0。[匿名化备份结果](evidence/deploy-backup.json)

6个现有会话均从storage1显式离线升级为3。升级前确认没有活动owner/runner或未确认执行。每库升级前后五张非meta业务表的有序行摘要及计数相等；原checkpoint、输入账本、owner、revision等meta不变，identity仅允许存储版本变化，允许新增归档meta。配置及非DB日志/材料共12个原文件核hash保持；数据库及其已知sidecar单独按逻辑快照审计。[六库迁移结果](evidence/deploy-migration.json)

原`config.json`、`settings.json`两文件在实际启动前后原字节均未改变。系统凭据没有导出、重写或删除，原keyRef沿同一Windows用户使用。

## 验证

- 新日常解释器的pip check、version、help和包成员绑定通过。
- 实际新日常解释器运行T06两案与Todo回归共3节点通过：两次压缩、旧摘要重整、关闭进程、重启、原文回查/导出、显式离线升级、任务pin保留及明确清空。[本地SSE合成案例](evidence/deploy-20261113/apps-t06-todo/command.json)
- 使用真实配置和已有真实会话，通过无头`/session`重开；另起进程分页`/archive read`，与升级前一致性备份中的一条原用户消息逐字比较相等。真实正文和凭据未输出到日志，验证进程禁止外部连接/DNS，外部网络尝试为0。[真实维护验证](evidence/deploy-verified.json)

压缩质量由本地确定性模型验证执行契约，未调用真实供应商模型或产生模型费用。本票不把无头启动/prepare-only当作Windows Terminal视觉与缩放通过。

独立复核已完成：当前Apps安装314产品成员全部匹配公开绑定清单；启动器新旧字节仅解释器字符串不同，包装器与旧备份完全相同，旧解释器仍在。维护脚本的六库比较、非DB文件保持、PIPE内存原消息比较及外网拒绝计数已复核，无未解决阻断；独审未读取真实配置/正文或再写真实会话。

初次验证脚本仅选第一空会话而缺少用户消息，后改为选择实际存在的原消息；首次全socket拦截又阻止了asyncio本地唤醒通信，后仅允许loopback、继续禁止外部连接/DNS。原停止回执保留于deploy-verify-state，它们是验证器前提问题，不修改产品或降低原文比较断言。

## 回退

旧`venv-b09-r7`与备份中的旧启动器仍保留。因会话语义已升为3，旧程序会拒写新格式；回退必须先停全部新旧进程，再根据私有清单恢复同一位置的原数据或一致性DB备份及必要材料，不能只切旧解释器，也不能把备份DB直接覆盖正在使用的WAL现场。本次未执行回退或删除用户文件。
