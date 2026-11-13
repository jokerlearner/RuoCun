# N24 当前批次固定产物

当前批次已收口。固定N24-r2源码为 `31208a95bef737c9e6bfbfb861695c84f2f90276`，wheel位于 `dist/n24-r2/ruocun-0.1.0.dev0-py311-none-win_amd64.whl`，SHA256为 `c12ead3d1174a2b6099431a1984a30cd50edaae13b7d1dfb013650d9a9b6baa9`。

## 实际出口

- r1全量为1445 passed、4 failed、3 deselected，用时414.15秒。4项均为15测试夹具把源码loader定位到已安装环境不存在的tests目录。修正后在实际安装r2上原4项通过，用时37.24秒。原失败回执保留，汇总为1449项已有通过证据，3项默认未选中。r2没有再次整套全量，复用范围按[ADR-0015](../../../../docs/adr/0015-batch-validation-and-packaging.md)和下述逐成员证明。
- r1完整Ruff、mypy（151源码）、offline通过。唯一测试夹具修正的定向Ruff通过。r2源码运行代码与r1固定Git源码相同，实际交付只conversation.py的350处CRLF转LF。
- r2 sdist重建wheel与direct wheel相等。Git归档、工作树、sdist、两种wheel、实际安装168成员严格逐字节绑定通过，运行依赖与锁、metadata相符，实际SQLite3.54.1。机器结果见[artifacts.json](artifacts.json)和[runtime.json](runtime.json)，另有[独立逐成员检查](../n24-package-bytes/README.md)。
- [仓库外纯安装独审](../review/pure-r2-review.md)确认168成员、pipcheck及默认模块入口的真实owner强杀、同run接管、取消收据和孙进程止写。普通七工具/重开及受控TTY沿用r1b成功证据，并实际证明r1→r2仅纯换行差异。
- 用户在[真实WT](../n18/wt/runs/20261111T044203Z-514e10/README.md)对所列五项回复“全部正常”。机器记录exit0、无强停、前后mode503/7相等。18文本技术前置已解除，65可排程。77整体体验、IME候选窗、图片及完整渲染范围保持对应任务状态。

r1换行绑定失败、夹具失败及独审命令cwd错误均保存。所有产品测试使用合成配置与本地响应，真实/付费模型调用为0。

## 原始执行参考

以下保留最初r1的准备命令和环境核对。未来验证时按ADR-0015选择对应影响范围与独立label，实际本轮结果以上述出口及raw回执为准。

复用上一轮 [N5 绑定](../../../ruocun-next20h/evidence/n5-integration/README.md) 的 Git 归档、工作树、sdist、direct wheel 和实际安装逐成员对照。新 [bind.py](bind.py) 使用独立 N24 目录及回执前缀，运行依赖从冻结提交的 pyproject 与实际 wheel metadata 逐项核对。旧 N5 绑定及产物继续保存。

## 可复用材料

本机已只读核对根 `.venv` 中 build 1.6.1、Hatchling 1.33.0、pytest 8.4.2、Ruff 0.17.3、mypy 2.4.1，以及 ruocun-dev-support。构建可沿已验证的 `--no-isolation` 路线消费这些已安装工具。

`D:/java supplement/Firstcode/RuoCun/.cache/n1-input-wheels` 的运行包现有字节与当前运行锁一致。prompt_toolkit 3.0.52 的 SHA256 为 `9aac639a3bbd33284347de5ad8d68ecc044b91a762dc39b7c21095fcd6a19955`，wcwidth 0.9.4 为 `901eace6d2dd25ebb917d0ce5db18e5c537e1504c905cf32f0d006c12098b05d`。`.cache/wheels` 当前只看到 mypy 纯 Python wheel，不能把它当完整开发依赖 wheelhouse。最终依赖以冻结 pyproject、锁、wheel metadata 和实际安装绑定为准。

## 主协调执行顺序

以下命令在集成根目录按顺序运行。先确认共享接缝独审通过，提交最终产品和测试，登记 `$n24Source`。`n24-r1`、各 label、临时目录必须是本轮未使用值。若产品回修，则保存首候选与失败回执，换 r2 重新冻结和验证。

```powershell
$n24Root = 'D:/java supplement/Firstcode/RuoCun'
$n24Boot = 'C:/Users/PC/AppData/Local/Programs/Python/Python311/python.exe'
$n24Dev = "$n24Root/.venv/Scripts/python.exe"
$n24Git = 'D:/study_software/Git/cmd/git.exe'
$n24Runner = "$n24Root/tools/run.py"
$n24State = "$n24Root/.cache/n24-final"
$n24Release = 'n24-r1'
$n24Wheel = "$n24Root/dist/$n24Release/ruocun-0.1.0.dev0-py311-none-win_amd64.whl"
$n24Source = (& $n24Git -C $n24Root rev-parse HEAD).Trim()

& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-build-r1 -- $n24Dev -I -X utf8 -m build --no-isolation --outdir "dist/$n24Release"
if ($LASTEXITCODE) { throw 'N24 build failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-direct-r1 -- $n24Dev -I -X utf8 -m build --no-isolation --wheel --outdir ".cache/$n24Release-direct"
if ($LASTEXITCODE) { throw 'N24 direct wheel failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-install-r1 -- $n24Dev -I -X utf8 -m pip install --no-index --no-deps --force-reinstall $n24Wheel
if ($LASTEXITCODE) { throw 'N24 fixed install failed' }

& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-pytest-r1 -- $n24Dev -I -X utf8 -m pytest -q --basetemp 'C:/Users/PC/AppData/Local/Temp/ruocun-n24-r1-full'
if ($LASTEXITCODE) { throw 'N24 pytest failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-ruff-r1 -- $n24Dev -I -X utf8 -m ruff check .
if ($LASTEXITCODE) { throw 'N24 Ruff failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-mypy-r1 -- $n24Dev -I -X utf8 -m mypy
if ($LASTEXITCODE) { throw 'N24 mypy failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-offline-r1 -- $n24Dev -I -X utf8 -m ruocun_acceptance offline --output ".cache/$n24Release-offline"
if ($LASTEXITCODE) { throw 'N24 offline failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-bind-r1 -- $n24Dev -I -X utf8 .scratch/ruocun-next24h/evidence/integration/bind.py $n24Source $n24Release $n24Git
if ($LASTEXITCODE) { throw 'N24 artifact binding failed' }
```

最后的绑定先验证产品源、包、安装及实际 SQLite，再写入 `artifacts.json` 与 `runtime.json`。binder 的命令本身由 runner 在结束后才写回执，需在其完成后审查并复制该条 `n24-final-bind-r1` raw 目录到本目录，其余此前 N24 final 回执由 binder 收集。成功状态从实际回执取得。

## 仓库外纯安装复核

独审先按 `artifacts.json` 核包指纹，使用全新仓库外 venv。N24 使用同一套固定 wheel，离线安装按锁验证的两项运行依赖，不安装 pytest 或开发支撑。以下沿用已验证的 CLI 和受控 TTY 原断言，实际测试文件先由独审绑定到冻结提交，仅接受已核实的标准换行转换。两份原文件的实际 SHA256 作为脚本入参，运行前后均核对。

```powershell
$n24Pure = 'C:/Users/PC/AppData/Local/Temp/ruocun-n24-r1-pure'
$n24PurePy = "$n24Pure/Scripts/python.exe"
$n24CliTest = "$n24Root/tests/test_mvp_product.py"
$n24TtyTest = "$n24Root/tests/test_n1_runtime_tty.py"
$n24CliHash = (Get-FileHash -LiteralPath $n24CliTest -Algorithm SHA256).Hash.ToLowerInvariant()
$n24TtyHash = (Get-FileHash -LiteralPath $n24TtyTest -Algorithm SHA256).Hash.ToLowerInvariant()

& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-outside-venv-r1 -- $n24Boot -I -X utf8 -m venv $n24Pure
if ($LASTEXITCODE) { throw 'N24 outside venv failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-outside-deps-r1 -- $n24PurePy -I -X utf8 -m pip install --no-index --find-links "$n24Root/.cache/n1-input-wheels" --require-hashes -r "$n24Root/requirements-runtime-win311.lock"
if ($LASTEXITCODE) { throw 'N24 outside dependencies failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-outside-install-r1 -- $n24PurePy -I -X utf8 -m pip install --no-index --no-deps $n24Wheel
if ($LASTEXITCODE) { throw 'N24 outside product failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Root --state $n24State --label n24-final-outside-pipcheck-r1 -- $n24PurePy -I -X utf8 -m pip check
if ($LASTEXITCODE) { throw 'N24 outside pip check failed' }
& $n24Boot -I -X utf8 $n24Runner --cwd $n24Pure --state $n24State --label n24-final-outside-confirm-r1 -- $n24PurePy -I -X utf8 "$n24Root/.scratch/ruocun-next24h/evidence/integration/outside_confirmation.py" 'C:/Users/PC/AppData/Local/Temp/ruocun-n24-r1-outside-state' $n24CliTest $n24TtyTest $n24CliHash $n24TtyHash
if ($LASTEXITCODE) { throw 'N24 outside original assertions failed' }
```

独审随后复制自己的 raw 回执并记录源码/包/安装字节对照。真实 Windows Terminal、IME、缩放、跨平台实机和用户体验按实际单独登记。
