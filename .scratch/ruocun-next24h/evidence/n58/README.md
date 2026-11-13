# 58 原生凭据与私有配置候选

从当前主线接续，原433d980候选的 `.worktrees/wb-i58` 未修改，两处未跟踪材料保留。提取其Win32窄端口及已捕获问题修复，原demo未移入、未运行。普通runtime接线由主协调维护，本候选保持58 claimed等待入口验证与独审。

## 实现与来源

冻结 `config/credential.ts` / `keychain.ts` / `profiles_store.ts` 及对应测试提供激活账户、inline优先、keyRef解析、系统失败后文件fallback的断言。D09唯一凭据映射规定原生服务ruocun-api-key、account原始名称UTF8hex、旧服务精确只读与provenance。ctypes CredRead/Write/Delete/Free沿D17已验窄端口及433d980候选，不新增依赖。

`credential.createKeychain(environ, *, backend=None, timeout_seconds=8.0)` 给普通入口注入KeychainPort，尊重现有RUOCUN/DAO USE_KEYCHAIN优先级及0/off关闭规则。非Windows或明确不可用返回UnavailableKeychain。`WindowsCredentialStore.last_lookup`记录同一次读取，root可调用模块函数`credential.describeFailure(lookup)`显示具体失败，无需第二次读取。现有resolveCredential签名保持。

原生设置/删除只允许新服务，旧服务明确只读。已确认系统成功才返回system。超时或写后异常保留unknown并抛CredentialWriteUnconfirmed，禁止自动落另一份文件或重放写入。端口同实例最多一个在途原生调用，8秒超时不是原生停止证明。若原生调用迟到，调用者必须保留未决现场并停止该操作，不能宣称资源已回收。

Windows saveProfiles复用07 PrivateDirectory/verify_private_file/atomic_publish，在持有私有目录边界时读取并原子发布。已有普通ACL目录拒绝写入且不自动改ACL，已有inline账户读取仍沿旧loader。2个旧写回测试仅将合成fixture放到私有native目录，来源内容断言保持。读取既有配置失败时保存操作保留原文件并报错，按用户已接受ADR0013失败规则记录这一相对DAO的差异。发布后同步失败保留07原异常/回执，不盲删或伪报未写。

## 实际验证

所有进程沿tools/run.py白名单、合成HOME/配置/TEMP，根venv的-I入口显式加载本worktree/src。命令原始回执在raw，敏感值扫描无命中。产品和测试摘要在source-members.json。

- n58-storage-red的3项已捕获问题在原实现失败，分别为重名写前保护、私有配置和损坏旧配置保留。
- n58-storage-green复验44通过/2失败，2项为旧来源fixture使用普通ACL目录。按平台前置调整fixture后保留原内容断言。
- n58-selected-green有2个从旧候选抽取测试遗漏构造helper的NameError，补用同一公开构造器。
- n58-selected-final共68通过，包含既有04来源配置/凭据测试、旧58候选窄端口断言与必要Windows文件确认。
- n58-final-ruff、n58-final-mypy通过。初次import顺序失败及修复回执保留。
- n58-system-uuid及final均在本机真实Credential Manager只操作当次新UUID的Profile/profile两个合成target。实际写入system、读取内容匹配、大小写不覆盖、原生ref配置在私有ACL中保存。每个target精确删除后实际CredReadW返回1168，pending_targets为空。秘密仅留SHA256，真实/付费模型调用0。final为最终probe脚本的回执。

普通python模块入口使用系统keyRef产生合成HTTP请求尚待主协调装配验证。实际SDK调用拒绝/超时分支目前由既有fake断言覆盖，未把它们写成本机真实超时或停止验证。Linux/macOS实机与最终组合验收后续记录。
