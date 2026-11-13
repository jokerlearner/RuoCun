"""冻结 SWE-bench adapter_v2.mjs（MIT）的显式容器接入。"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path, PurePosixPath

from ruocun.platform.process_tree import ForegroundResult

from ..run import EnvironmentIssue, _isolated_env, _run, executable
from .adapter import _instances

# Verify and redact in the container; a credential never travels back to the host.
_CONFIG = """
import subprocess, sys
from ruocun.config.profiles import resolveActive
from ruocun.config.profiles_store import loadProfiles
active = resolveActive(loadProfiles(sys.argv[1]))
if active is None:
    sys.exit(2)
if len(sys.argv) > 2:
    result = subprocess.run(['git', 'diff', '--cached', 'HEAD', '--'], capture_output=True)
    if result.returncode or active['key'].encode() in result.stdout:
        sys.exit(3)
    sys.stdout.buffer.write(result.stdout)
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance")
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--container")
    parser.add_argument("--config-in-container")
    parser.add_argument("--workdir", default="/testbed")
    parser.add_argument("--python-in-container", default="python3")
    parser.add_argument("--docker")
    parser.add_argument("--model")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=900_000)
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()
    if not args.instances.is_file() or not args.container or not args.config_in_container:
        print(json.dumps({"status": "environment_unavailable", "reason": "需要实例清单、已准备容器和容器内配置。"},
                         ensure_ascii=False))
        return 2
    if (not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", args.container)
            or not PurePosixPath(args.workdir).is_absolute()
            or not PurePosixPath(args.config_in_container).is_absolute()
            or not args.allow_live or not args.output or args.timeout_ms <= 0):
        parser.error("须提供合法容器、容器内绝对路径、输出、正数超时及显式模型授权。")
    try:
        row = _instances(args.instances, [args.instance])[0]
        docker = executable("docker", args.docker)
    except (OSError, ValueError, EnvironmentIssue):
        print(json.dumps({"status": "environment_unavailable", "reason": "Docker 或有效实例材料不可用。"},
                         ensure_ascii=False))
        return 2

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "environment_unavailable", "instance_id": args.instance}
    with tempfile.TemporaryDirectory(prefix="rc-swe-") as temporary:
        root = Path(temporary)
        env = _isolated_env(root / "home", enable_auto=False)
        prefix = [docker, "exec", "--workdir", args.workdir]
        command = [*prefix, args.container]

        def invoke(argv: list[str]) -> ForegroundResult:
            return _run(argv, root, env, args.timeout_ms / 1000)

        head = invoke([*command, "git", "rev-parse", "HEAD"])
        status = invoke([*command, "git", "status", "--porcelain"])
        probe = (Path(__file__).resolve().parents[1] / "runtime_probe.py").read_text(encoding="utf-8")
        runtime = invoke([*command, args.python_in_container, "-I", "-c", probe])
        credential = invoke([*command, args.python_in_container, "-I", "-c", _CONFIG, args.config_in_container]) if not (
            runtime.aborted or runtime.code
        ) else runtime
        if (head.code or head.stdout.strip() != row["base_commit"] or status.code or status.stdout.strip()
                or runtime.aborted or runtime.code or credential.aborted or credential.code):
            report["reason"] = "需要实例干净基线、内联账户及可加载的受控 SQLite 运行库。"
        else:
            prompt = f"这是仓库 {row['repo']} 中的实际问题。请定位并修复，只改必要的源码。\n\n{row['problem_statement']}"
            agent = [args.python_in_container, "-m", "ruocun", "--eval", "--no-hooks", "--no-skills",
                     "--config", args.config_in_container]
            if args.model:
                agent.extend(("--model", args.model))
            result = invoke([*prefix, "--env", "RUOCUN_DECK=0", "--env", "RUOCUN_AUTO_APPROVE=1",
                             "--env", "RUOCUN_USE_KEYCHAIN=0", args.container, *agent, "--", prompt])
            if result.aborted:
                report.update(status="outcome_unknown", reason="Docker 客户端超时，保留容器供核对。")
            elif result.code:
                report.update(status="agent_error", reason=f"容器内 Agent 退出码 {result.code}。")
            else:
                staged = invoke([*command, "git", "add", "-A", "--", ".", ":(exclude).ruocun"])
                diff = invoke([*command, args.python_in_container, "-I", "-c", _CONFIG,
                               args.config_in_container, "diff"]) if not staged.code else staged
                if staged.aborted or diff.aborted or diff.code or diff.outputCapped:
                    report.update(status="outcome_unknown", reason="补丁未确认，保留容器供核对。")
                else:
                    prediction = {"instance_id": args.instance, "model_name_or_path": args.model or "ruocun-container",
                                  "model_patch": diff.stdout}
                    (output / "predictions.jsonl").write_text(json.dumps(prediction, ensure_ascii=False) + "\n",
                                                            encoding="utf-8")
                    report["status"] = "prediction_ready"
    (output / "meta.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "prediction_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
