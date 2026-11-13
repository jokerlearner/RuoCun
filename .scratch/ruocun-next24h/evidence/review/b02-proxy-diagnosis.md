# 固定包全量后：代理TLS计数断言诊断

仅修改 `test_resilient_http.py::test_product_proxy_connect_tls_sni_and_certificate_failures` 及本证据，不改产品/固定包，不全量、不构包。按diagnosing-bugs，全部调用白名单+合成环境，raw均敏感扫描false。

## 反馈与判别

原全量出现请求成功但 `len(helpers)==1` 得2；该列表来自本次ResilientContext.on_resolver_start，不是全局Popen spy。原case独立第一次运行 `b02-review-proxy-original` 实际1 passed in7.37s，证明需区分正常重试与串进程。

探测前按序提出可证伪假设：首轮失败/超时后正常retry/fallback；一次attempt重复解析；回调误收其它请求/线程。首个假设预测只延迟首轮握手就会出现两次本请求helper和两条attempt；第二个预测helper数大于attempt；第三个预测出现不属于该请求角色/线程的helper。

[隔离诊断脚本](b02-proxy-diagnose.py)复用原case，仅首轮本地server TLS握手延迟3.15秒，并记录合成helper PID/线程/角色和attempt摘要；未换DNS/HTTP/TLS实现。`b02-review-proxy-delay-red` 精确重现原计数失败：两个MainThread的真实 `_dns_helper`，第0轮stream/retry、idle=true，第1轮stream/complete；watchdog=true、fallback=false。两个helper属于这一次请求的两次尝试。**原全量当时没有attempt trace，不能声称已证明那一次具体也是idle原因。** 此回放证明原“整次调用永远一个helper”假设会拒绝合法重试。

## 最小测试修复

只把整次调用固定数量改为“每个stream attempt一个helper”。无重试时仍严格等于1，成功helper真实exit0，所有先前尝试helper也必须已经退出。原成功content、CONNECT目标、TLS SNI、错主机名证书失败、未信任证书失败及最终全部helper/服务线程清理断言保留。没有改同文件其它HTTP/SOCKS测试。

最终结果：

- `b02-review-proxy-original-final`：原case **1 passed in7.20s**，exit0。
- `b02-review-proxy-delay-final`：相同延迟回放exit0；合法两次尝试通过，原错误证书/不信任证书断言也继续实际执行并通过。
- `b02-review-proxy-static`：该测试文件Ruff通过。

中间 `delay-green` 标签实际仍exit1：首次替换误落到同文件相邻的同文字断言，及时撤回，目标原断言当时未改；`original-green`当时通过只能作未修目标的普通回放，不能算修复完成。原始回执全部保留，最终diff仅本目标case。

产品无诊断trace或延迟插桩；临时探针只保存在上述明确隔离的证据脚本，MonkeyPatch在进程结束前恢复，回环服务关闭并join。已有正确的按请求context seam，无需架构重构。预防点是在重试测试中按attempt核资源归属，而不把整次请求当成单次连接。
