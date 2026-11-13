# 批次05共享接线与集成回归

来源输入和公开接口沿本批逐票及独立复核记录；这里只收主协调共享接缝回执，不新增一般测试矩阵。tools/run.py均用显式环境白名单、合成HOME/配置/会话；所有收录command.json敏感值扫描均false。原红与诊断保留，不能用绿覆盖历史。

- 注册/搜索MCP：`b05-registry-red`原实现缺接口，1 failed/11 passed；`b05-registry-green`12 passed；恢复精确visibility接线后`b05-registry-resume`12 passed。
- Monitor与注册接线：`b05-monitor-seam`13 passed；独立实际进程/取消/owner丢失由[46独审](../../review/b05-monitor-review.md)另证。
- 已有普通入口组：`b05-entry-legacy`真实10 passed/2 failed，两个失败都在模型请求前退出71/AtomicFileError。读取实际路径发现，非必要维护cleanup向原有公开项目配置目录写stamp，原私有写端口拒绝。
- 按diagnosing-bugs保存区分性探针：`.cache/b05/diagnosis/test_skip_cleanup.py`由原by-definition用例复制，唯一改变为临时跳过maybeCleanup；`b05-cleanup-discriminator`原失败1项通过，其余5未选。它是诊断实验，不代替产品修复。
- 产品`927fd910`仅在既有best-effort cleanup异常边界补AtomicFileError。原生配置写ACL保持；修复后`b05-cleanup-regression`原两项2 passed/5未选。原组其余10项不重复；最终集中全量另列实际结果。
- 暂停只读重开窄修`1cfdf479`：复用独审普通SIGINT/SQLite/latest探针，补读重开退出后的原checkpoint，仍paused/not done；`b05-paused-readonly-preserved`退出0。原真实终端按键/视觉体验不据此代验。
- MCP运行依赖闭包采用37个官方hash wheel；SDK1.30.0及Pydantic2.14.2/core2.50.2。`b05-runtime-lock-fixed`生成锁；空环境按hash锁安装、import、pip check分别见对应raw。官方依赖回执见[固定依赖](../dependencies-fixed/wheels.json)；最初未采用版本收据保留在[旧解析收据](../dependencies/README.md)。

白名单和合成服务没有真实模型请求/费用。共享接线的来源测试与真实CLI独立证据参见[批次记录](../../../batch-05.md)。固定安装全量与产品262成员字节绑定在[集中交付](../integration/README.md)另记。
