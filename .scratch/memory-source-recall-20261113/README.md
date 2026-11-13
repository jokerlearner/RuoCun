# 记忆来源标签召回复现与修复

日期：2026-11-13。范围及授权见[任务票](issues/01-source-recall.md)。

## 已确认原因

反思提示和解析允许 `source=user_stated` / `source=inferred`，原校验逻辑却把所有非空来源作为文件路径。
反思写入成功后，下一次启动因找不到对应文件而将记忆判为 `stale`，启动提示未包含用户偏好。

## 最小兼容修复

`memory/validate.py` 将这两个精确值识别为非文件证据标签，跳过路径和哈希检查，保留有效期检查。
其它字符串仍为文件来源，包括显式 `./user_stated`、`./inferred`，仍检测文件修改和删除。
不改 Markdown、数据模型、存储/锁定规则和反思开关；旧标签记录无需迁移或重写。

## 原始失败

- [格式回归 red](evidence/format-red/stdout.txt)：4 failed、15 passed；两标签被误判 stale，两同名文件造成标签被误计算哈希。
- [普通入口 red](evidence/entry-red/stdout.txt)：1 failed；第一进程成功完成模型回答和同步反思写入，第二进程全新会话的首个 HTTP 请求缺少偏好。

## 修复后验证

- [记忆与反思回归](evidence/memory-reflection-green/stdout.txt)：146 passed。
- [Ruff](evidence/ruff/stdout.txt)：通过。
- [Mypy](evidence/mypy/stdout.txt)：1 个修改源文件通过。
- [跨进程普通入口](evidence/entry-green/stdout.txt)：1 passed；第二个全新进程的首个模型请求包含已持久化的用户偏好与项目事实。
- [独立复核](evidence/review.md)：亲跑普通入口 1 passed、格式 19 passed、Ruff 与 diff 检查通过；无本范围阻断。

回归覆盖来源有效期、文件来源哈希/删除、记忆存储/工具/注入/清理/合并/蒸馏，以及反思流水线、恢复保存点和普通入口。
仅复跑受影响入口，没有重复全量构建与安装；本次没有更改依赖、包元数据或启动入口。

## 重跑

使用仓库已有 `.venv/Scripts/python.exe`，以 `-I -B -X utf8` 执行本目录 `run_checks.py`。
参数为未使用过的证据目录名、`pytest` / `ruff` / `mypy`、对应测试或检查参数。
例如：

```powershell
& '.\.venv\Scripts\python.exe' -I -B -X utf8 '.scratch/memory-source-recall-20261113/run_checks.py' 'entry-recheck' pytest 'tests/test_memory_source_recall.py'
```

启动器使用白名单环境和合成 HOME/配置/会话/临时目录，并将工作区 `src` 置于导入首位。
端到端测试使用两个独立产品进程和本地 HTTP/SSE fixture；第二进程不开反思、不继续旧会话。
测试确认偏好进入新请求上下文，不测量真实模型遵循偏好的质量；真实模型调用为零。

原始失败与合成运行状态保留。本次工作区原有大量未提交改动，修复也保留未提交状态，不混入其它文件。
