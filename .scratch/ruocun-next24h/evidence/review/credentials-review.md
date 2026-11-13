# 58 系统凭据与配置保存独审

受审候选为 `ea25fdd`（集成 `cbd73e4`）与普通入口 `99fc3ed`，独审树 `b196c5a`。本票模块与普通入口接缝可集成，剩余审查阻断 0。

对照冻结账户/凭据来源以及 D09/D17 已确认契约，内联 key 优先、keyRef 精确解析、服务来源 provenance 和原始 profile 名称均保留。新服务 TargetName 用原账户 UTF8 hex 区分大小写；旧服务只读。CredRead 返回内存由 CredFree 在 finally 释放，凭据对象 repr 隐去秘密。普通入口只解析当前激活账户，没有枚举其它 target。

明确系统成功才记 system，明确拒绝才允许文件 fallback。超时、写后异常与未知删除保留未决，不自动写另一份文件或重放。同实例原生槽在迟到调用完成前保持占用；8 秒等待上限不能证明 Win32 调用停止。此边界的实际超时结果由既有窄端口合成断言验证，没有冒称真实系统调用已停止。

Windows 配置保存复用原 07 私有目录和原子发布端口，重名 profile 在系统写入前拒绝，损坏或不可读旧配置保留原文件并报错。普通 ACL 目录不能默改为私有。该失败保留规则已由 ADR-0013 接受，来源内容断言及必要平台适配分别记录。

独立复跑凭据存储、Windows 窄端口、原 config_credential/config_store 和普通 TTY，共 **69 passed in 4.67s**。4 源文件 mypy 与定向 Ruff 通过，原回执均 exit 0、scan_hit=false。

另以 [keyref-runtime.py](keyref-runtime.py) 创建当次新 UUID 合成凭据。写前只对该精确 target 回读，确认 1168；原生系统保存后私有 config 仅含 keyRef。普通模块入口实际读取该 keyRef，向本次回环 SSE 服务发送两次请求，服务仅保存 Authorization 与模型是否匹配的布尔结果，均为 true。标准 CLI 正常退出，输出没有该合成秘密。finally 精确删除当次 target，CredRead 再次返回 1168，pending_targets 为空。秘密只留下 SHA256，没有读取、枚举或修改历史真实凭据。

全部过程使用明确白名单与合成 HOME/config/TEMP，已锁依赖、独审源码、回环模型响应，没有真实或付费模型请求。Linux/macOS 实机、最终打包安装和完整终端用户体验继续由对应出口验收。
