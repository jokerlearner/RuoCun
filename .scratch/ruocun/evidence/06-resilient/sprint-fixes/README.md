# 06 冲刺回修

本记录为实现者回修证据，不能替代独立复核或06结题。参考仍为冻结dao-f17e189-7ac654a0dc06；公开入口为streamChat，沿WIRE-07/08既定测试边界。

## 根因与修改

1. 流式setTimeout与非流式AbortSignal.timeout的参数接纳不同。原候选统一折成Node计时器值后发fallback，导致负数、小数、非有限及超过uint32的值仍发请求。按冻结client.ts在fetch前建AbortSignal.timeout的次序，fallback先校验整数0..4294967295；流式计时器原语义保持。独立审查者已亲跑Node22界限，含2^32-1接受与2^32拒绝。
2. Retry-After采用JS Number，不是Python float；复用已有_jsNumber解析，保留有限/非负过滤及原上限。十六/二进制零的429现在能够重试。
3. yieldedAny以实际StreamDelta判断；只有id/arguments的工具片段尚未可见输出，不能让内部累积对象阻止重试。runStreamAttempt的StreamDisconnected路径也以实际delta判断，已产出名称等delta仍保留partial不重复。
4. fallback失败使用自己的异常状态码，JSON解析失败没有HTTP status，不继承前一流式429。独立记录其状态，避免上层误判限流；fallback自身401仍保留401。

## TDD与回归

所有命令从tools/run.py启动，外层启动器也清空父环境并使用合成HOME；CPython3.11、既有venv及已核验公开wheel闭包。新测试使用合成transport/固定clock，无真实模型、密钥、网络端点调用；完整既有套件含本机HTTP/DNS/TLS测试。

| 回执label | 结果 |
| --- | --- |
| sprint06-invalid-red | 7 failed / 3 passed，非法timeout错误发出fallback |
| sprint06-invalid-green | 10 passed，增加合法0/1/uint32上限正对照 |
| sprint06-boundaries-red / red2 | Retry-After与未渲染工具片段失败，后者覆盖两种异常类型 |
| sprint06-boundaries-green | 16 passed（timeout及六条重试边界） |
| sprint06-fallback-status-red | 1 failed / 7 passed，解析失败错误继承429 |
| sprint06-allfix-green | 18 passed，含fallback自身401正对照 |
| sprint06-final-pytest | 319 passed / 3 deselected，无skip/xfail |
| sprint06-final-ruff / mypy / build / offline | 均exit0；mypy32文件；offline仍为既有4个工程子例 |

安装步骤sprint06-invalid-install、sprint06-boundaries-install、sprint06-allfix-install均exit0。原始stdout/stderr/command.json保存在[raw](raw/)；所有回执scan_hit=false，未把命令标签或失败历史覆盖为通过。

源码变更后已重装产品到当前专属venv；构建及安装仅用已核验公开wheelhouse。仓库外wheel、独立边界和完整复核由另一worktree的审查者执行。真实模型、完整来源oracle、WT人工、其它平台与最终standalone未在本轮执行，既有CPython私有socket/连接工厂及测试证书限制继续保留。测试进程已join，合成状态留存；未清理任何历史探针或未知对象。
