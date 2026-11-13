"""重建 D11 静态复用清单；只读冻结 ZIP，不启动子进程或网络。"""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / ".scratch/ruocun-discovery/research"
REF = ROOT / ".scratch/ruocun-discovery/reference/dao-f17e189-7ac654a0dc06"
PREFIX = "11-test-replay-gates"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest = json.loads((REF / "manifest.json").read_text(encoding="utf-8"))
    metadata = json.loads((REF / "metadata.json").read_text(encoding="utf-8"))
    files = {row["path"]: row for row in manifest["files"]}
    coverage_path = ROOT / ".scratch/ruocun/task-coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    module_path = ROOT / ".scratch/ruocun/module-map.md"
    modules = {}
    for number, line in enumerate(module_path.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r'\| <a id="mm-', line):
            columns = [part.strip() for part in line.strip("|").split("|")]
            source = re.findall(r"`([^`]+)`", columns[1])[0]
            modules[source] = {
                "id": re.search(r"MM-\d+", columns[0])[0],
                "line": number,
                "target": columns[2].strip("`"),
                "existing_disposition": columns[4],
            }

    with zipfile.ZipFile(REF / "source.zip") as archive:
        content = {name: archive.read(name) for name in archive.namelist()}
    assert set(content) == set(files), "ZIP 与 manifest 成员不一致"
    assert len(content) == 805
    assert all(digest(content[name]) == files[name]["sha256"] for name in files)

    # 既有实现任务的责任归属；不把归属登记写成实现通过。
    owners = coverage["module_references"]
    explicit = {
        "background_wait.integration": [16, 40], "cache_audit_integration": [28, 57],
        "cache_prefix": [28, 29, 31], "deck_cli.integration": [56, 70],
        "longtask_eval": [44, 72], "loop_advisor": [42, 44],
        "loop_durable": [7, 10, 17], "reflect_pipeline": [42],
        "resume_durable": [7, 17, 26], "exec_shell_ctl": [14, 15],
        "execute_durable": [10, 12, 17], "multi_select": [66],
        "tail": [65], "steps_select": [69], "toggle": [34, 35],
    }

    def test_owners(path: str) -> tuple[list[int], list[str]]:
        if path.startswith("evals/"):
            task = 73 if "/memory/" in path else 74 if "/reflect/" in path else 72
            return [task], ["task-coverage 的 TEST/评估责任，按对应评估域展开"]
        stem = path.split(".test.")[0]
        for suffix in (".ts", ".tsx", ".mjs"):
            match = modules.get(stem + suffix)
            if match and match["id"] in owners:
                return owners[match["id"]], [match["id"]]
        basename = PurePosixPath(stem).name
        if basename in explicit:
            return explicit[basename], ["D11 对跨模块测试按任务职责显式展开"]
        if path.startswith("src/mcp/"):
            return [51, 52, 53, 54], ["MM-496；MCP manager 的跨传输/生命周期职责"]
        if path == "src/hooks/integration.test.ts":
            return [48, 49], ["Hook 集成职责"]
        if path == "src/permissions/integration.test.ts":
            return [9, 13, 24], ["分层权限与执行前裁决职责"]
        raise AssertionError(f"测试缺拥有任务: {path}")

    recipes = {
        "test-offline": (["S", "D", "R"], ["pytest", "offline"], ["python-dev-lock", "synthetic-profile", "fake-clock-rng"]),
        "test-protocol": (["S", "D", "R"], ["pytest", "protocol"], ["python-dev-lock", "synthetic-profile", "loopback-fixtures"]),
        "test-runtime": (["S", "D", "R"], ["pytest", "runtime"], ["python-dev-lock", "synthetic-profile", "owned-process-store"]),
        "test-terminal": (["S", "D", "R"], ["pytest", "offline", "terminal"], ["python-dev-lock", "synthetic-profile", "visible-windows-terminal"]),
        "test-eval-pure": (["S", "D", "R"], ["pytest", "offline"], ["python-dev-lock", "synthetic-profile", "scorer-only-gold"]),
        "script-deterministic": (["R", "S", "D"], ["oracle", "runtime"], ["python-dev-lock", "synthetic-profile", "owned-process-store"]),
        "script-live-runtime": (["P", "R", "S"], ["live", "runtime"], ["python-dev-lock", "explicit-live-budget", "owned-process-store"]),
        "script-live-memory": (["P", "S", "D"], ["live"], ["python-dev-lock", "explicit-live-budget", "scorer-only-gold"]),
        "script-model-topic": (["P", "D", "R", "S"], ["live"], ["python-dev-lock", "explicit-live-budget", "materialize-external-input", "exposure-review"]),
        "script-diagnostic": (["R", "S", "D"], ["offline"], ["python-dev-lock", "synthetic-profile", "redacted-wire"]),
        "script-visual": (["S", "D", "R"], ["terminal"], ["python-dev-lock", "visible-windows-terminal"]),
        "script-demo-live": (["P", "S", "D", "R"], ["terminal", "live"], ["python-dev-lock", "visible-windows-terminal", "explicit-live-budget", "materialize-external-input"]),
        "script-mascot": (["D", "S"], ["offline", "terminal", "install"], ["python-dev-lock", "materialize-mascot-originals"]),
        "script-version": (["S"], ["install"], ["python-build-lock", "clean-install-root"]),
        "task": (["D", "R", "P", "S"], ["offline", "live"], ["python-dev-lock", "explicit-live-budget", "scorer-only-gold", "task-tools-and-refs"]),
        "fixture-memory": (["D", "R", "P"], ["offline", "live"], ["python-dev-lock", "scorer-only-gold", "fixture-redaction-review", "explicit-live-budget"]),
        "fixture-reflect": (["D", "R", "P"], ["offline", "live"], ["python-dev-lock", "scorer-only-gold", "fixture-redaction-review", "explicit-live-budget"]),
        "fixture-mcp": (["D", "R", "S"], ["protocol"], ["python-dev-lock", "loopback-fixtures", "optional-node-fixture"]),
        "fixture-lsp": (["D", "R"], ["protocol"], ["python-dev-lock", "loopback-fixtures"]),
    }
    deterministic = {"verify-memory.ts", "verify-persistence-runtime.ts", "verify-background-wait.mjs", "verify-background-recovery.ts", "verify-recovery-entrypoints.mjs"}
    memory_live = {"accept-memory.sh", "accept-cache.sh", "debug-distill.ts", "verify-reflect.ts"}
    visual = {"preview-taiji.ts", "preview-welcome.ts", "welcome-ink.tsx", "demo-reflect.tape", "demo.en.tape", "demo.tape"}
    script_owner = {
        "verify-memory.ts": [30, 31, 32], "verify-persistence-runtime.ts": [7, 17],
        "verify-background-wait.mjs": [15, 16], "verify-background-recovery.ts": [15, 16, 17, 40],
        "verify-recovery-entrypoints.mjs": [17, 26, 70],
        "verify-background-wait-live.mjs": [16, 76], "verify-background-recovery-live.mjs": [17, 40, 76],
        "accept-cache.sh": [28, 73], "accept-memory.sh": [31, 32, 73],
        "debug-distill.ts": [32, 73], "verify-reflect.ts": [42, 74],
        "dump-harness-wire.ts": [57, 72], "generate-mascot-data.mjs": [68, 79, 83],
        "sync-version.mjs": [79, 80, 83],
    }
    records = []
    external = []
    for path in sorted(content):
        category = (
            "test" if ".test." in path else "script" if path.startswith("scripts/") else
            "task" if path.startswith("evals/tasks/") and path.endswith("/task.json") else
            "fixture" if "/fixtures/" in path or "/__fixtures__/" in path or "/testfixtures/" in path else None
        )
        if category is None:
            continue
        text = content[path].decode("utf-8")
        name = PurePosixPath(path).name
        basis = []
        if category == "test":
            tasks, basis = test_owners(path)
            group = "test-eval-pure" if path.startswith("evals/") else "test-terminal" if "/tui/" in path else "test-protocol" if any(f"/{part}/" in path for part in ("mcp", "lsp", "hooks", "client")) else "test-runtime" if re.search(r"durable|background|process|managed_shell|shell_runner|persistence|deck|resume|scheduler|exec_shell|monitor|sandbox|cron|schedule|wakelock|/db\.test", path) else "test-offline"
        elif category == "script":
            group = (
                "script-deterministic" if name in deterministic else
                "script-live-runtime" if name in {"verify-background-wait-live.mjs", "verify-background-recovery-live.mjs"} else
                "script-live-memory" if name in memory_live else
                "script-demo-live" if name.endswith(".tape") else
                "script-visual" if name in visual else
                "script-mascot" if name == "generate-mascot-data.mjs" else
                "script-version" if name == "sync-version.mjs" else
                "script-diagnostic" if name == "dump-harness-wire.ts" else "script-model-topic"
            )
            tasks = script_owner.get(name, [65, 68, 77] if name in visual else [72, 75, 76])
            if group == "script-demo-live":
                tasks = [65, 73, 74, 77] if name == "demo-reflect.tape" else [65, 75, 77]
            if group == "script-model-topic":
                assert "streamChat" in text, path
        elif category == "task":
            group, tasks = "task", [72, 75]
        else:
            group, tasks = (
                ("fixture-memory", [73]) if path.startswith("evals/memory/") else
                ("fixture-reflect", [74]) if path.startswith("evals/reflect/") else
                ("fixture-mcp", [51, 52, 53, 54]) if "/__fixtures__/" in path else
                ("fixture-lsp", [55])
            )
        disposition, entries, dependencies = recipes[group]
        anchors = [f"{path}:1"]
        if category in {"test", "script"}:
            for number, line in enumerate(text.splitlines(), 1):
                if re.search(r"describe\(|it\(|test\(|streamChat\(|spawn\(|readFile(?:Sync)?\(", line):
                    anchors.append(f"{path}:{number}")
                    if len(anchors) == 4:
                        break
        mm = modules[path]
        record = {
            "category": category, "path": path, "sha256": files[path]["sha256"],
            "source_anchors": anchors, "module_map": f".scratch/ruocun/module-map.md#{mm['id'].lower()}",
            "planned_target": mm["target"], "group": group,
            "disposition": disposition, "entries": entries, "dependencies": dependencies,
            "owner_tasks": sorted(set(tasks)), "assurance_owner_tasks": [82, 85],
            "owner_basis": basis or ["D11 按既有任务72–83的验收/评估/交付职责展开"],
            "state": "planned-product-not-run-in-D11",
        }
        if category == "test":
            record["entry_scope"] = "拟迁移语义的主门禁；terminal为所属UI产品后续体验，非每条纯函数断言均须人工。source文件未经本票执行，主分组不证明其当前安全/离线性。"
            if path in {"src/tools/read_file.test.ts", "src/tools/todo_write.test.ts", "src/tools/registry.test.ts", "src/client/client.test.ts", "src/agent/loop.test.ts", "src/tools/execute.test.ts"}:
                record["prior_source_evidence"] = ".scratch/ruocun/evidence/02-oracle/README.md；Node22的6文件合计190断言通过，非port结果"
        if category in {"fixture", "task"}:
            record["entry_scope"] = "offline只验格式/数据/评分或verifier有效性；真实模型质量只计live，live专属依赖按所选分支检查。"
        if category == "task":
            task = json.loads(text)
            record["task_kind"] = task["kind"]
            record["verifier"] = "check.mjs" if task["kind"] == "local" else "checkpoints+optional-pass2pass" if task.get("checkpoints") else "fail2pass+pass2pass"
            record["protected_fields"] = [key for key in task if key in {"fix_ref", "test_files", "fail2pass", "pass2pass", "checkpoints", "_validation_note", "_humanMinutes_note", "_pass2pass_scope"}]
            record["exposure"] = "existing-development-material;not-unseen"
            if task["kind"] == "oss":
                record["dependencies"] = dependencies + ["external-repository-and-install"]
        if category == "script":
            refs = []
            for number, line in enumerate(text.splitlines(), 1):
                if re.search(r"/Users/|/private/tmp/|[\"']/tmp/|\.codex-analysis", line):
                    refs.append(f"{path}:{number}")
            if refs:
                record["external_material_reference_anchors"] = refs
                external.extend(refs)
        records.append(record)

    counts = dict(collections.Counter(row["category"] for row in records))
    assert counts == {"fixture": 85, "test": 215, "task": 16, "script": 58}, counts
    assert collections.Counter(row["group"] for row in records)["script-model-topic"] == 38
    issue_files = {int(p.name.split("-", 1)[0]): p for p in (ROOT / ".scratch/ruocun/issues").glob("*.md")}
    for row in records:
        assert row["owner_tasks"] and row["disposition"] and row["entries"] and row["dependencies"]
        assert all(task in issue_files for task in row["owner_tasks"] + row["assurance_owner_tasks"])
    index = ROOT / ".scratch/ruocun-discovery/research/02-function-runtime.md"
    fixed = re.findall(r"^\| CMD-([^| ]+) \|", module_path.read_text(encoding="utf-8"), re.M)
    assert len(fixed) == len(set(fixed)) == 52
    app = content["src/tui/app/App.tsx"].decode("utf-8")
    menu_text = app.split("const COMMAND_META:", 1)[1].split("];", 1)[0]
    menu = re.findall(r'"([^"\n]+)"', menu_text)
    assert len(menu) == 49
    basic = re.findall(r'case "([^"\n]+)"', content["src/commands/commands.ts"].decode())
    assert len(basic) == 9
    dataset = {
        "schema": 1, "kind": "planned-reuse-not-product-test-results",
        "snapshot": metadata["snapshot_id"], "base_commit": metadata["base_commit"],
        "source_tree_sha256": metadata["source_tree_sha256"], "counts": counts,
        "definitions": {"D": "直接复用数据并核对来源/许可/脱敏", "R": "适配高层CLI/协议回放", "S": "语义重写语言/平台绑定", "P": "保留评估协议，模型结果单列"},
        "entry_commands": {"pytest": "python -m pytest", **{suite: f"python -m ruocun_acceptance {suite}" for suite in ("oracle", "offline", "runtime", "protocol", "live", "terminal", "install")}},
        "entry_state": "已确认；完整工程入口/产品尚未实现，不代表当前可运行",
        "owner_task_registry": {str(task): {"path": str(path.relative_to(ROOT)).replace('\\', '/'), "title": path.read_text(encoding="utf-8").splitlines()[0].removeprefix("# ")} for task, path in sorted(issue_files.items()) if any(task in row["owner_tasks"] + row["assurance_owner_tasks"] for row in records)},
        "dependency_definitions": {
            "python-dev-lock": "锁定开发依赖/解释器；默认禁外网、无真实凭据", "python-build-lock": "锁定构建后端/发布依赖，按D12/实现79–80确定",
            "synthetic-profile": "独立HOME/config/session/cwd/Git fixture；显式子进程env allowlist", "fake-clock-rng": "可控时钟/随机值和独立预期",
            "loopback-fixtures": "独立fake HTTP/SSE/MCP/LSP/Hook/Deck；真实监听/关闭证据", "owned-process-store": "本次拥有PID+creation time/SQLite/IPC；超时清理回执",
            "visible-windows-terminal": "真实WT自动状态+用户最终操作分列，ADR0004", "scorer-only-gold": "gold/hidden verifier与agent工作区/提示分离",
            "explicit-live-budget": "显式live选择、已授权账户/成本/次数；本轮不执行", "materialize-external-input": "先合法收齐外部轨迹/系统提示并登记hash；本清单不声称缺失路径全量已探测",
            "exposure-review": "标准答案/solution/fix commit/历史开发暴露记录；只能标开发集",
            "redacted-wire": "原始协议含合成输入，诊断材料脱敏后落盘", "materialize-mascot-originals": "嵌入帧可保留；原始PNG/manifest未在快照，重生成单列MATERIAL-GAP",
            "clean-install-root": "仓库外普通用户/VM、新venv、无PYTHONPATH/源码回退", "task-tools-and-refs": "base有效性、双轨/权重/超时和外部verifier版本；RUNS默认3",
            "fixture-redaction-review": "复用前通读邮箱/电话/IP/路径/真实人名等；现有redact不完备", "optional-node-fixture": "外部测试服务可保留Node；产品核心不因此依赖Node",
            "external-repository-and-install": "外部repo/base/fix资源和工具链需预物化锁定；不可用记ENV/MATERIAL-GAP",
        },
        "source_reexecution": "独立可写快照+Node22+冻结lock+合成环境；本D11未重跑来源测试。实现02仅6文件190断言已通过；Node24 native退出为ENV。",
        "routes": {"fixed_slash": fixed, "menu": menu, "non_tty": basic + ["recovery", "resume"], "dynamic": "按每case合成命令/skills/plugin发现结果单列；不加入52/49/11", "source_research_anchor": str(index.relative_to(ROOT)).replace('\\', '/') + ":127"},
        "assets": records,
    }
    for row in records:
        assert all(entry in dataset["entry_commands"] for entry in row["entries"])
        assert all(dependency in dataset["dependency_definitions"] for dependency in row["dependencies"])
        for anchor in row["source_anchors"]:
            anchor_path, line_number = anchor.rsplit(":", 1)
            assert anchor_path == row["path"]
            assert 1 <= int(line_number) <= len(content[anchor_path].decode("utf-8").splitlines())
    output_path = OUT / f"{PREFIX}.assets.json"
    output_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    validation = {
        "kind": "static-catalog-validation-not-product-pass", "source_members_verified": len(files),
        "counts": counts, "total_assets": len(records),
        "groups": dict(sorted(collections.Counter(row["group"] for row in records).items())),
        "task_kinds": dict(collections.Counter(row["task_kind"] for row in records if row["category"] == "task")),
        "fixed_slash": len(fixed), "menu": len(menu), "non_tty": len(basic) + 2,
        "missing_owner_or_dependency": [], "external_material_reference_anchors": sorted(set(external)),
        "source_tests_executed_in_D11": 0, "real_model_calls": 0, "subprocesses_created_by_builder": 0,
        "inputs_sha256": {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p.read_bytes()) for p in (coverage_path, module_path, REF / "manifest.json", REF / "source.zip", Path(__file__), OUT / f"{PREFIX}.md")},
        "assets_sha256": digest(output_path.read_bytes()),
    }
    (OUT / f"{PREFIX}.validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: validation[key] for key in ("source_members_verified", "counts", "total_assets", "groups", "task_kinds", "fixed_slash", "menu", "non_tty", "real_model_calls")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
