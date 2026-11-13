# 79 仓外安装独立复核

复核候选 `12209627b58294796cc1e527c09bb724af505fc5`。同一 Windows x64 CPython 3.11 wheel 绑定产品 `0252fe7f3d51a89e166a716bc1991929cb8d9a09`，SHA-256 `142afa7757e6d29ae9b9ed908e4521a5ca6e9f483729b4c915fb4d8142c61cb9`。使用现有仓外纯运行 venv，在独立仓外目录复制同一 wheel 和探针，合成 HOME 与状态由工具白名单启动。 [包成员与自动出口复核](../../../../../ruocun/evidence/b09-automatic/independent-review.md)

实际安装的 `ruocun.exe` 普通入口创建后台 Shell，并在已确认保留后台的情况下退出。实际安装的 `python -I -m ruocun --continue` 接管同一 run 与 runner，业务启动标记只有一次。签名终态为 `canceled`，原 Unicode 日志可读取，Bash、BashOutput、KillShell 三条实际结果已写入受控 SQLite。按已核身份读取的实际进程命令行显示默认同包 runner/helper，两角色与候选版本和签名代码指纹一致。五次模型请求均发往本机合成服务。业务进程、runner、helper 和服务完成清理，临时项目已删除。 [命令](b09-review-n79-installed/command.json) · [真实输出](b09-review-n79-installed/stdout.bin)

17 个资源与许可安装成员重新逐字节匹配 wheel。SQLite 的固定运行库实际解包并进入普通持久化路径。来源外部 PNG 和生成 manifest 的缺项沿用 E-02 记录。79 技术复核通过。 [资源与试验边界](../README.md)
