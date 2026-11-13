# 记忆来源标签召回修复：独立复核

日期：2026-11-13（Asia/Shanghai）

结论：本次修复范围内未发现阻断问题。独立验证确认，反思写入的 `source: user_stated` 和 `source: inferred` 能在首个进程结束后，由第二个全新普通 CLI 会话从磁盘召回并注入模型请求的系统提示。两条标签原样保留；未增加渲染语义，也无需迁移既有记忆文件。

## 职责和范围

- root 修改产品文件 `src/ruocun/memory/validate.py` 及格式测试 `tests/test_n4_memory_format.py`。
- 本复核者仅新增 `tests/test_memory_source_recall.py`、执行独立验证并编写本报告；未修改产品代码或格式测试。
- 复核范围为来源标签与文件路径的区分、有效期优先级、文件来源的既有校验，以及跨进程启动召回。其它已有工作区改动不在本报告的质量结论内。

## 失败复现与独立通过证据

1. 修改产品前运行新增端到端测试：`entry-red/stdout.txt` 为 **1 failed**。首进程成功完成普通回答和一次同步反思，两域的 Markdown 已正确保存来源标签及正文；第二进程未恢复旧会话，首个模型请求仅含系统消息与新的用户输入，仍缺少已保存偏好，断言为 `fresh startup omitted persisted user_stated preference`。
2. root 修复后独立运行同一测试：`entry-green/stdout.txt` 为 **1 passed in 4.04s**。用户域的明确偏好及项目域的推断事实同时出现在第二进程的系统提示中。
3. 独立运行格式测试：`review-format-green/stdout.txt` 为 **19 passed in 0.13s**，覆盖两标签、已过有效期、真实文件缺失/变化/未变、同名文件下的标签不计算哈希，以及 `./user_stated`、`./inferred` 显式路径仍按文件处理。
4. 三个相关文件的 Ruff 检查通过：`review-scoped-ruff/stdout.txt`。产品与格式测试的 `git diff --check` 通过。

修复后独立入口命令：

```powershell
& '.venv/Scripts/python.exe' -I -B -X utf8 '.scratch/memory-source-recall-20261113/run_checks.py' 'entry-green' pytest 'tests/test_memory_source_recall.py'
```

每组完整 argv、工作目录、退出码均保存在各自的 `command.json`；端到端合成请求与两个 CLI 进程的输出分别保存在其 pytest 临时目录中。`entry-red` 的命令还记录明确白名单的完整合成环境。证据目录仅使用一次，不覆盖红证据。

## 源码审查判断

- `validate.py:28` 仍先检查 `validUntil`，因此标签不会绕过明确的失效日期。
- `validate.py:30` 仅对两个精确标签跳过文件验证，其余来源仍进入原路径解析、读文件及哈希比较。
- `validate.py:48` 使这两个标签不因工作区碰巧存在同名文件而获得文件哈希；需要引用同名文件时可使用显式相对路径。
- 存储模型、frontmatter 读写及反思持久化流程未修改；已有记忆中的这两种字符串在读取时直接兼容，原来源值不被删除或重写。
- 未扩展解决反思文件来源的其它哈希补齐问题，本结论不覆盖该独立疑点。

## 环境与证据限制

外层 pytest 及两个 CLI 子进程均采用明确环境白名单，HOME、配置、会话、缓存与临时目录指向合成目录；导入固定到当前仓库源码。模型服务为测试进程内的本地 `127.0.0.1` HTTP/SSE fixture，无请求函数 monkeypatch，无真实模型调用，无真实用户配置或记忆读取。测试验证持久化、重启、校验和注入接缝；不证明模型能够自行正确识别用户偏好或作出可靠推断，也不代表 Windows Terminal 体验验收。

## 复核时文件绑定

| 文件 | SHA-256 |
| --- | --- |
| `src/ruocun/memory/validate.py` | `DCE2C929FF250FD396EE5E3AB2C6D667FE7712023A73B02EEFE3A73CE808403C` |
| `tests/test_n4_memory_format.py` | `DA9280D9B5C5FCDFD521E7E3A47915ED79E1CE9C280E9FC81A8B17F36115EF54` |
| `tests/test_memory_source_recall.py` | `7B0AAE1C4514913F7A8FE3A4E44FC78370F10652207AE87B20F4B158AB697076` |
