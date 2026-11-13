# 任务 06 合成 DNS 测试的系统代理事件

2026-11-10，`codex06-http-supervised2` 与 `codex06-dns-repeat1` 的一个 DNS 阻塞测试使用 `http://synthetic.invalid:<合成端口>`。尽管 `tools/run.py` 清空父环境并提供合成 HOME，Windows 上 `urllib` 仍可能读取系统代理配置。测试实际经系统代理返回 502；复现日志中的三次请求均使用合成域名、合成提示和 `synthetic` 占位凭据。**未请求真实模型；这不符合该测试原定的仅本机范围。**

两条原始运行记录保留在本 worktree 的 `.cache/boot/raw/<label>/`，runner 的 `scan_hit` 均为 false；测试代码及预期输入已核查为合成值。父进程的真实凭据、配置和环境变量未传入测试子进程，未发现真实凭据进入日志。不能据此推断代理外部服务的内部处理情况。

修正：本机测试在 pytest 进程中显式将 `urllib.request.getproxies` 替换为空映射，并将阻塞解析测试域名改为 `localhost`；生产程序及真实代理语义不做这一修改。代理验证使用显式指定的本机合成代理，禁止依赖宿主代理配置。事件及原始记录保留，后续测试前先验证使用的代理和出口。
