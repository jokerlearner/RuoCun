# D19首次独立合并复核

主分支未快进。候选提交b1b15b5，合并助手提交60404b8均保留。
pytest 2 passed、12场景及全部进程退出已复核，但8个强杀句柄PID与ready/runtime记录的事务worker PID不同。
CPython venv launcher的子Job可能连带终止worker；此差异不直接证明注入无效，但尚缺强杀目标身份与立即退出的绑定证据。
原始证据不改。安排fresh修正子代理补齐独立身份断言并重新执行，再由fresh merger复核。原始脚本/全局Python保持不变。
复核快照在同目录三份文件；本记录不是D19解决或产品验收通过。
