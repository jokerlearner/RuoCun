# 62 电源路由

冻结来源：src/tui/wakelock.ts:1–18，主调用方src/index.ts:1524–1534；目标范围ADR-0010/W5。产品保持tui/wakelock.py归属。acquireWakeLock返回可调用release对象，普通每轮开始取、finally释放由主协调接线；可读status/reason及getWakeLockCapability供准确呈现，不把进程启动当系统实际持锁证明。

Windows边界先红后绿：明确unsupported、无防自动休眠保证、后端零调用，release可重复不假称持锁。另两个紧凑来源/必要用例验证：macOS caffeinate -i、Linux systemd-inhibit的原argv（品牌why改ruocun）、NO_WAKELOCK仅'1'禁用及RUOCUN空值阻止DAO fallback、缺少binary真实unavailable退化；一次获取只释放一次、等待后资源结束。独占合成Python进程作为spawn端口实物，不调用caffeinate/systemd-inhibit或用户电源设置，release返回时process已退出。最终3项通过，Ruff/Mypy通过，raw白名单scan_hit=false。

默认支持平台电源helper在独立进程组启动，释放TERM后有界等待，必要时KILL再等待；缺后端不抛业务失败，退出仍未确认时status=unconfirmed并保留准确reason，不伪称released。Windows不申请电源锁、不启动原生线程或helper。macOS/Linux实际系统是否持锁未实机验证；本票不承诺Windows系统不会休眠，也不延伸后台owner/防休眠服务。

公开接口：acquireWakeLock(*,environ=None,platform=None,spawn=None)->WakeLock，WakeLock可调用或release()，另status/reason；getWakeLockCapability(*,platform=None)返回supported/guaranteed/platform/reason。平台/命令注入仅用于既有独立验证端口，普通调用由真实平台与显式环境决定。主协调组合根使用每轮try/finally，取消/异常同样释放；若需避免阻塞事件循环，release可asyncio.to_thread调用，其默认等待最多两段3秒，仅用于自己创建的进程/组。

普通运行接线及独审另收口，当前不自行resolved、不代填最终体验、没有新增费用/系统安装、全量或构包。
