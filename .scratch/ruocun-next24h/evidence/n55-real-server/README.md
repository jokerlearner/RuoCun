# 55 真实服务器验证环境

准备者`/root/n24_permissions`，仅为55准备隔离外部语言服务器，不改产品runtime依赖、根venv、系统安装或DAO。最初创建的pylsp私有venv为空，未下载其依赖；实现者核对冻结`src/lsp/client.test.ts:12–20`使用TypeScript服务器后，采用同类服务器以复用9操作的原断言。

官方元数据与缓存压缩包已核：

- [typescript-language-server 5.0.1](https://registry.npmjs.org/typescript-language-server/5.0.1)，Node>=20，Apache-2.0，无runtime子依赖。
- [typescript 5.9.3](https://registry.npmjs.org/typescript/5.9.3)，Node>=14.17，Apache-2.0，无runtime子依赖。
- 现有Node为`D:/all_enviroment_software/node.exe`，实际v24.15.0；npm11.12.1仅作私有前缀安装器，不调用全局安装或npx。

通过tools/run.py显式白名单、合成HOME/配置/TEMP，npm使用显式空user/global npmrc、官方registry、固定版本、ignore-scripts/no-audit/no-fund。两个tarball的官方SHA512 integrity、SHA1 shasum与npm缓存实际字节逐一匹配；package-lock版本/integrity与已安装package.json匹配。官方metadata和核验记录见official-metadata.json/verified-packages.json，真实版本回执见raw。仅本地依赖下载，无模型、付费API或产品通过结论。

可执行配置：

```json
{
  "command": "D:/all_enviroment_software/node.exe",
  "args": ["D:/java supplement/Firstcode/RuoCun/.worktrees/b04-hooks/.cache/b06-real-lsp/node/node_modules/typescript-language-server/lib/cli.mjs", "--stdio"],
  "extensions": [".ts", ".tsx"]
}
```

workspace为`D:/java supplement/Firstcode/RuoCun/.worktrees/b04-hooks/.cache/b06-real-lsp/node/workspace`，其中sample.ts逐字节取自冻结`src/lsp/testfixtures/sample.ts`，tsconfig显式include sample.ts。node_modules位于该workspace祖先私有目录，符合原client.test.ts的TS解析前提。

## 实际产品验证

以主协调`88c9ba67`中的客户端候选`8234c7a2`运行，实际client.py SHA256为`9c88cb8ed2c3726116bb07bba02ba59092b01b9418641adaa59d4b6282de97e8`，运行前后相同。exercise.py从指定源码根导入产品LspClient；只在私有外部Node服务器前加入透明stdio字节记录器，输入/输出原字节照常转发，预期不由记录器构造。真实TSLS及其tsserver子进程仍在产品创建的同一个Windows Job内。完整帧见actual/wire.jsonl，结果与活进程HANDLE确认见actual/results.json。

原`client.test.ts:27–88`的9操作及编辑同步断言全部实际通过：definition跳1行、references含4行、hover含greet、documentSymbol/workspaceSymbol命中、接口implementation到9行、prepareCallHierarchy命中inner、incoming包含outer、outgoing包含inner；scratch文件前插空行后definition变为2行，wire实际含didChange。scratch执行后删除，原sample未修改。

调用后尚活的独占进程树实际保留6个OS HANDLE，记录PID/父PID/创建时间；产品dispose返回后逐句柄零等待检查全部signaled且exit_code非STILL_ACTIVE，产品client_returncode=0。wire最后包含shutdown/result/exit，真实语言服务器自然exit0；其仍活子树由既有Job收口，收据中部分子进程exit1不伪称全部自然退出。包含九操作、一次编辑同步和关闭的本次实际运行约1.484秒。工程命令退出0、scan_hit=false；提交前另扫描完整实际日志不含调用环境秘密。

此结果是55单个真实第三方服务器与来源样例的技术证据，供独审复用；普通入口、协议异常/URI/取消等既有独立fixture另由A/R验证，不代填最终终端体验，也不扩张成所有语言/实机通过。整票状态仍由主协调验收。
