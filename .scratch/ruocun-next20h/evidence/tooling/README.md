# N0类型检查工具环境收口

原固定mypy2.4.1编译wheel在三个私有环境均于import阶段被Windows应用控制阻止，没有产品类型诊断。失败回执保留，未改系统策略或移动被阻止DLL。

采用[官方PyPI同版本纯Pythonwheel](https://pypi.org/project/mypy/2.4.1/#files)，[官方源码说明](https://github.com/python/mypy#readme)明确支持解释运行。通过PyPI JSON元数据取得文件URL/SHA256，下载后重新核对SHA、Name/Version及wheel内零pyd/dll/so；具体供应源在[mypy-pure.json](mypy-pure.json)。版本、其它17包及产品运行依赖均保持，本次只为原mypy检查选择官方另一个发行包。

主协调私有venv非索引/no-deps替换该已核验wheel后，原`python -I -X utf8 -m mypy`正常完成：77源文件通过（此时图片存储/Read候选尚未集成），不是最终N0全量类型结论。原编译hash与新纯Pythonhash均纳入同一固定版本锁；独立环境可用[mypy-pure.lock](mypy-pure.lock)及明确wheel文件选择纯Python版本，无共享可写venv。

命令均经外层清空环境及tools/run.py、合成HOME/config/temp，真实模型API0调用。下载/安装/原失败与纯Python检查raw见根`.cache/sprint-root/raw/n0-{root-mypy-1,fetch-mypy-pure,install-mypy-pure,root-mypy-pure}`；最终批次证据统一收录。没有把ENV失败改写成原编译版通过。
