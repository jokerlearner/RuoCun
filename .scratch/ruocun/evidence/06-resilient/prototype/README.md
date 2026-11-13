# 任务 06：受监督 DNS helper 合成原型

状态：**仅独立原型通过，不代表产品实现、任务 06 或跨平台通过**。执行日期 2026-11-10；Windows / CPython 3.11.9。生产网络代码未由本原型修改。

## 已验证

1. `resolver_probe.py` 启动每个 helper 的独立 `Popen`。在 helper 内用合成 `getaddrinfo` 等待事件模拟解析卡住；确认其已进入阻塞后分别触发取消和 200ms 超时，父进程对所属句柄执行 `terminate`、`communicate`、`wait`，确认非零退出。两个阻塞 helper 同时存在时，仅终止一个，另一个仍活着；最后由测试回收它。正常 `localhost` 解析结果及地址顺序和父进程的实际结果一致。
2. `network_probe.py` 在每个 HTTPConnection / HTTPSConnection 对象上覆盖 CPython 私有 `_create_connection`，将解析交给新 helper（本实验仅把约定的合成域名映射至本机）。真实本机 HTTP 302 使 POST 转 GET、按顺序分别解析两个合成主机；本机代理收到正确的 HTTPS CONNECT 目标，helper 只解析代理地址。代理在 CONNECT 后模拟目标 TLS 端点：可信的合成证书与对应 SNI 成功，不信任证书和可信证书主机名不匹配均被拒绝，错误主机名也按原值传作 SNI。
3. 所有 helper 为该实验独立创建并被等待；本机监听器使用 `shutdown`/`server_close`，主线程 join。两个原型从 `tools/run.py` 白名单环境启动，helper 再使用显式环境白名单。仅访问本机，不访问真实模型或账户。此范围不包含任意平台 DNS 服务器卡死、真实企业代理、生产证书、重定向安全策略或完整生命周期并发压测。

## 原始证据与复现

`raw/` 为 `tools/run.py` 原始 stdout、stderr 和 command.json；各次 `scan_hit=false`。`codex06-dns-proto-cert` 记录未显式提供配置导致的失败，`codex06-dns-proto-cert2` 记录使用合成配置成功。证书私钥属于一次性合成材料，未提交；可在隔离的测试目录重新生成（必须通过项目 runner 启动）：

```powershell
openssl req -x509 -newkey rsa:2048 -sha256 -days 1 -nodes -keyout synthetic-key.pem -out synthetic-cert.pem -config synthetic.cnf
python -I -X utf8 resolver_probe.py
python -I -X utf8 network_probe.py
```

运行前将上面两个 pem 文件放到这三个原型文件所在目录；使用明确的 openssl/Python 绝对路径、`tools/run.py --label <唯一标签> -- <命令>`、合成 HOME/TEMP 运行。原始验证依次为 `codex06-dns-helper-owned-v2`、`codex06-network-prototype`，实际参数在对应 `command.json`。合成私钥不能用作任何真实凭据。

## 最小候选接入边界与限制

- 给每个 HTTP/HTTPS 连接自身设置可注入的解析/连接工厂，不修改全局 `socket.getaddrinfo`。以 urllib 实际交给连接构造器的主机作为解析对象；代理情况下它是代理地址，CONNECT 目标由 `set_tunnel` 及 TLS SNI 沿用原实现。每次重定向须重新调用同一工厂，按标准库原语义处理方法和请求头。
- helper 应接收明确的合成/产品输入，执行与 `socket.create_connection` 等价的地址排序与错误语义；超时或取消仅终止所属 helper，并确认 wait、句柄和管道回收。原型仅证明合成故障下的最小行为，未证明进程池、并发竞态或真实系统 DNS 故障。
- `_create_connection` 和当前 socket 强制关闭均为 CPython 私有接口；未来 Python、Linux/macOS 以及不同 socket/TLS 组合必须分别验证。其他解释器不应默认为受支持。
- 目前 `sys.executable -I <脚本>` 只针对常规 Python 解释器；冻结的 Windows 独立程序中 `sys.executable` 可能是产品程序，不能假设支持 `-I`。任务 80 须提供打包后的 helper 路由/可执行文件并验证，不能把开发环境原型当作独立产品支持。
- 还需在产品实际路径构造可控阻塞 DNS、取消、超时、重试及进程身份隔离；验证合成 CONNECT、证书、SNI、重定向与异常退出/资源回收，再由独立 merger 复核。
