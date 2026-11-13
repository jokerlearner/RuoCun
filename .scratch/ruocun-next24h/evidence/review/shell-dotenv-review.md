# 普通 Shell 项目环境缺口回修独审

受审修复 `cf506ac`，独审树同时收录实际能力说明 `a45b7c6`，当前树 `5681265`。此已确认来源缺口关闭。

冻结调用链为 `index.ts:198–200` 加载 cwd/.env，`config/env_file.ts:35–41` 把缺省键补入 process.env，`exec_shell.ts:185–189` 启动实际子进程时传 scrubbedEnv，`safe_env.ts:5–10` 从该环境筛除敏感键。Python 原 runtime 只补局部 env，ShellExecutionPlan 却读取全局 os.environ，导致普通入口丢失项目特有的非敏感环境。

复用 [shell-runtime.py](shell-runtime.py) 增加单一 `--dotenv` 场景。父环境断言没有 SYNTHETIC_DOTENV_VALUE，只有合成 workspace/.env 提供 from-project-dotenv，真实获批 cmd 将它重定向到中文空格文件。修前得到字面 `%SYNTHETIC_DOTENV_VALUE%`，修后同一命令得到 from-project-dotenv。两次实际回执分别 exit 1 与 0，scan_hit=false。最初旧观察包装器尚未接受 14 的 onOutput 参数，先按现有签名补转发，原无效回执另存，未误当环境缺口证据。

修复沿独立可选 executionEnv 传完整环境快照。None 保留旧直接调用的全局环境行为，原用于配置与 trust 的 env 映射含义不变。PermissionRuntime 构造时复制环境，prepare/build 再筛敏感键并冻结。普通入口显式传已完成父环境优先级与 .env 补缺的局部映射，未修改全局 os.environ。

原 13/14、权限 runtime、trust 与普通 TTY 定向复验 **19 passed in 11.57s**。3 个受影响源码 mypy 与 Ruff 通过。现有 ProgramData 高层绑定、部分配置 env 直接调用与敏感环境过滤原断言保留。真实来源修复没有增加组合测试矩阵。
