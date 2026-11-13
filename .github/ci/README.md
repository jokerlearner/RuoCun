# 本地与持续集成入口

Windows x64 用 CPython 3.11.9。当前目录为仓库根，`--state` 保存原始命令、输出与 JUnit。`--work` 可指定全新的仓外目录，便于检查安装环境。省略时会在系统临时目录建立独立路径。每次使用新的状态目录，以便保留上一次的回执。

```powershell
python -I -X utf8 .github/ci/windows_gate.py --state .cache/ci/local-001
```

入口使用已有哈希锁准备开发环境，运行 Ruff、mypy，构建 sdist 并由它生成 wheel。在仓外纯 venv 安装并核对包路径、版本、帮助与 `pip check`，然后另用一个拥有 pytest 和 `tests/support` 的环境运行同一 wheel 的默认 pytest。测试中的 `python -I` 子进程也可导入这些工程依赖。Git 的绝对路径从调用端解析，只把该目录加入 pytest 的白名单 PATH。产物、摘要和回执留在 `--state` 中。

可用 `--stage static` 复跑静态检查，`--stage package` 构建或验证安装，`--stage full` 跑安装冒烟和默认全量。已准备的开发解释器可用 `--dev-python` 显式传入，入口保留它的原有安装。已有固定 wheel 可用 `--wheel` 复用，配合包含相应锁全部依赖的 `--wheelhouse` 可离线执行。`--installed-python` 接受已准备好的纯安装解释器，和全量阶段一起使用时需传入同一 wheel，供另建 QA 环境。提供 wheel 时，纯安装的产品文件及 `METADATA`、`WHEEL` 元数据逐字节匹配后才继续冒烟与 QA。

GitHub `ci.yml` 在 Windows 执行同一入口。Ubuntu、macOS 任务核对 Python 3.11 语法、来源导入和原生 Shell 适配，记录独立平台结果。Python 分发包目前带 Windows x64 标签，POSIX 任务是适配核验。`package-candidate.yml` 手动触发，构建 Windows 标准包并保留工作流产物，发布权限为只读。Windows 两个任务只在成功时上传产物，失败原始回执留在执行环境的状态目录。[GitHub Python CI 文档](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
