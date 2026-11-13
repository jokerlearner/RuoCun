# 15 Windows IPC transport候选

本候选只负责Windows具名管道与专用transport helper，执行runner、Shell Job、存储和业务epoch由其它负责人维护。15原票保持未完成。主线14已通过后派发此接缝，公开API已与runner实现者协商。

## API及职责

`PipeServer(pipe_name, capability, handler, *, helper_command=None, environ=None).start(deadline)` 启动独立server helper。公开helper_pid/helper_identity/private_sid/pipe_acl、alive/error，close()核实际helper退出。handler(payload, peer)返回dict，运行在此transport的串行服务线程，调用方负责业务状态锁。PeerIdentity包含helper_pid、OS直接parent_pid、核验一层venv转发shim后的owner_pid，以及helper_identity/owner_identity两个真实ProcessIdentity。

`request(pipe_name, capability, payload, *, expected_server_pid, deadline, helper_command=None, environ=None)` 每次使用短生命周期client helper。平台不重试、不重发start。helper_command是完整argv，不追加参数。角色、capability及配置通过私有匿名stdin，token不放argv。默认同版本`python -I -X utf8 -m ruocun --ruocun-ipc-helper`，组合根只分发helper_main，不进入账户/SQLite业务入口。源码验证目前使用显式helper_command定位本worktree。

原生OVERLAPPED仅在helper角色执行，API入口做角色检查。controller/runner侧使用公开subprocess.Popen、明确拥有者的stdio读写线程和绝对期限，不采用第二个原生stdin reader。线程只搬运有限帧，业务端按B已协商的to_thread外观消费。此处为D08公开子进程管道路线的同步外观适配，最终同包角色入口仍待root装配验证。

## 来源与边界

原生创建、提交前强持有、CancelIoEx后确认完成及pending fail-stop复用D18 `experiments/durable-io/probe.py`已接收核心。每次连接使用当前SID独占DACL、拒远端/首实例及不继承handle，客户端最小权限不含创建实例。实际读取DACL并严格比较。随机capability为32字节、每连接新挑战，双方HMAC分别绑定版本与请求/响应，响应不复用请求MAC。客户端实际GetNamedPipeServerProcessId核helper PID，server实际GetNamedPipeClientProcessId及OS父链核调用者身份。run/control_epoch、DB owner和启动许可由runner判断。

长度前缀以UTF8字节计，整帧上限262144，长度先核再分配、严格JSON/UTF8解码，不按chunk解码。握手总期限仍3秒，原生等待预留取消完成时间。client在总期限内预留最后0.5秒给helper确认退出，原生等待另预留0.25秒。取消未完成则保留OVERLAPPED/buffer/event/handle，poison禁止复用，由helper自身最外层finally原生fail-stop。外层保留真实helper进程HANDLE并核创建时间，处理venv shim后确认实际退出及stdio线程收口。未确认保留句柄，下一次启动必须先确认旧helper退出，才能放行新transport。parent退出清理不对Shell Job宣称效果回滚。

## 诊断与实际验证

所有命令用tools/run.py显式白名单和合成HOME，来源API及产品模块只从本worktree指定src加载。敏感环境值扫描无命中。初次pytest失败显示随机合成capability，收录副本已脱敏，原始摘要与忽略缓存位置见redactions.json，原失败保留。

初始实际PipeServer.start三秒失败。diagnosing-bugs用同一公开start入口和边界耗时定位，发送config之前remaining已为0，排除首帧发送本身。单次identity_cost回执显示parent首次OS/CIM身份查询2.407秒，旧helper首次查询2.250秒，含子解释器启动两端串行4.828秒。现按D18首帧只报告PID/创建时间，父端OS核完整ProcessIdentity并持handle，再经私有父子stdio复用已核同主机boot；helper仍逐次OS核PID/创建时间/父链。helper start实际0.235秒，3秒上限未放宽。源码没有DEBUG日志或生产轮询扩测。

最终n15-ipc-submit共4项通过，保留此前红回执、静态顺序/注解回修回执。n15-ipc-submit-ruff和submit-mypy均通过。必要确认覆盖UTF8字节帧、合法来源Unicode边界、跨字节分片/连续多帧、空/半帧/非法UTF8/超长拒绝、真实私有管道大Unicode往返、OS peer/owner身份、匿名真实拒绝5、首实例拒绝、错误HMAC/错误server PID拒绝后继续服务，退出后实际重开端点返回2。

另外复用D18已捕获submit-raise故障，仅注入一次实际997返回后的KeyboardInterrupt，证明产品helper在原生提交前已持有buffer/OVERLAPPED/event，Internal为259时目标入口自身finally fail-stop。未到达外层target-returned标记，调用者仍存活且retained handle确认helper退出。此为原生适配边界注入，不能写成真实坏驱动取消失败已验。

独立账户、远端机器及真实坏驱动未验证。runner/Job生命周期、持久grant/claim、control_epoch和最终固定包角色入口须由15集成继续验证，以上transport通过不替代整票resolved。

## owner强杀后的transport收口回修

15源/集成用例要求runner owner强杀后收口旧transport。仅当server helper在空闲连接循环中发现父runner已死，才可释放旧pipe。首候选漏了这项观察：`n15-ipc-owner-exit-red` 用真实父controller的os._exit复现，对本次helper真实创建身份持handle等待1.5秒仍为258。该失败的测试finally只终止该已核身份helper并确认退出，未操作其它进程。

修复后helper由私有stdio owner信息核OS父链与创建时间，持owner真实进程HANDLE，每次接入前和空闲循环检查它。owner退出后正常完成/取消当前有界native I/O，关闭pipe并退出，不留孤立listener。owner句柄关闭异常也不能绕过最外层pending fail-stop。`n15-ipc-owner-exit-green` 共5项通过，ruff/mypy通过，单项红回执保留。该检查覆盖真实controller异常退出，并不冒充跨系统重启/注销或坏驱动已验。
