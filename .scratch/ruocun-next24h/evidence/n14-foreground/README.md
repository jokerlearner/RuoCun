# 14 前台输出与受管进程树候选

本票接续13普通入口独审后实现，保持 claimed，等待主协调onShellOutput接线独审。当前主线的真实任务状态与最终固定包出口由主协调维护。

前台端口保留已批准的不可变argv/cwd/环境/native commandLine。stdout/stderr分开增量解码，Windows按BOM、UTF-8/OEM候选处理各行，未知或不合法字节用转义保留并给诊断。每个ForegroundResult保存stdoutRaw/stderrRaw内存字节和decodingDiagnostics。工具最终字符串也包含解码诊断，模型可见。任意外部程序在同一行混用未知编码无法可靠自动判断，候选明确记录该限制，不宣称普遍自动识别正确。产品未新增原始字节落盘框架。

PowerShell5.1真实Write-Error确认输出CLIXML。适配识别该流、读取错误/警告等文本、解开协议转义，保留原始结构字节，非法CLIXML保留原文并提示。普通输出继续实时发出，CLIXML文本在帧完整后提交。没有改变全局codepage或改写已批准Shell command。

onShellOutput(stream,text)的回调与signal在handler启动前固定。读取线程仅排入原事件循环，EOF分别发空text。取消后停止新回调，返回前收口reader及进程树。POSIX用os.read避免BufferedReader等待完整缓冲，Linux/macOS实际运行仍未验。观察回调异常只记录类型和保留完整工具结果，避免事件循环抛带原始输出参数的日志。

来源测试继续复用exec_shell原断言和既有Windows Job端口。原Windows取消case加入持续写ticks的真实孙进程，确认handler返回后两个进程句柄均signaled、文件字节稳定、回调数量稳定。四项必要适配检查覆盖分片UTF-8/OEM/无效字节保留、native argv双/单引号与中文环境、PS5.1可读CLIXML，以及中文空格.cmd、管道、批内换行、% ! ^ $参数/环境。

- n14-output-red为初始测试字符串转义错误，red1修正该测试后记录缺解码模块失败。
- n14-output-green1初始两项适配通过。
- n14-clixml-red记录实际PS5.1原始CLIXML问题，green通过解码及真实Job确认。
- 最终n14-regression-final为46项通过（14适配4、13计划8、原Shell/Windows28、技能安装公开调用方6），n14-submit-output为格式化后4项通过，mypy/Ruff通过。

所有验证经tools/run.py白名单环境、合成HOME/配置/临时目录，源码从当前worktree/src加载。原始失败与命令回执保留在raw，秘密扫描false并经人工审查，仅有合成值。来源及候选哈希见manifest。

本候选等待真实产品入口的增量可见、取消generation和跨chunk已知凭据脱敏独审。pwsh未执行实机确认，未安装解释器。15持久runner/恢复未启动，本票不代填后台或最终用户终端体验通过。

候选后续修正将CLIXML转换限定为实际PS stderr。通用native stdout和字面协议文本保留原文，避免把数据当作协议改写。同一适配用例补字面保留断言，4项定向复验及mypy/Ruff通过，回执为n14-clixml-scope-*。
