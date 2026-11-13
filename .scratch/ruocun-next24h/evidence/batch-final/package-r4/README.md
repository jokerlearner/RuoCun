# 最终批次画面修复候选 b09-r4

固定构包源码 `fcde3a921ba42aa1b52844757b343291fc073d21`。Windows x64 CPython 3.11 wheel 和 sdist 在 `dist/b09-r4/`，wheel SHA-256 `cd9724366ddd1dcb449c53321daff4048ffa967244fa96b83e54411ad131e139`，sdist SHA-256 `a1ffcc6a5681c9b086cac725b2f7ec713b8127a5f1a8023c0cbd7a5cc5bb104e`。实际安装的 309 个产品成员与固定 Git、sdist 和 wheel 一致，R3 到 R4 只有六个产品 Python 文件变化。依赖锁、资源、包配置及安装帮助一致。[包绑定](artifacts.json) · [独审](../r4-review/README.md)

修复真实输入拆分的 UTF-16 代理对、普通入口专属窗口声明、专属重放顺序与原图恢复，以及共享窗口宽度变化后的局部擦除。合成窗口缩小时按可见空间回退。原生控制台模式退出、分批原生输入的表情转录与放大后重放在已安装包实际复验。[控制台](raw/r4-native-console/stdout.bin) · [ConPTY](raw/r4-native-emoji/stdout.bin)

同一 R4 安装的定向组首轮 60 通过、1 项重绘测试失败。夹具在画面完成前改变宽度，导致假设的 Win32 光标坐标与旧帧不同。同步到真正渲染后精确复跑 owned/shared 两个原节点通过。该夹具变化 `2d57674b` 与实际构包源码的产品输入字节相同，技术证据绑定在该验证提交。[定向首轮](raw/r4-installed-terminal-fixed/stdout.bin) · [精确复跑](raw/r4-installed-resize-exact/stdout.bin)

仓外恢复首次检查读取时未见 runner-state 发布，随后工作目录占用，保留原始失败。重跑固定包的实际探针通过同一 Shell run、一次启动、真实取消和三个提交工具结果。[首轮](raw/r4-recovery/stderr.bin) · [重跑](raw/r4-recovery-retry/stdout.bin)

已有未受影响的自动回执按差异逐项复用。最终真实 Windows Terminal 画面及重新登录由各票实际反馈确认。[自动出口](../../../../ruocun/evidence/b09-r4-automatic/README.md)
