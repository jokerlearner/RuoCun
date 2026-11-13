"""Run the frozen DAO CLI against local SSE; development support, not product code.

Expected Read semantics originate in frozen src/tools/read_file.test.ts; plan
visibility originates in src/agent/loop.test.ts. Fake assistant text is scripted
transport input and is never evidence of live model quality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SNAPSHOT = "dao-f17e189-7ac654a0dc06"
TREE = "7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c"
PROMPT = "只读规划：先建立读取材料的计划，再读取材料 空格.txt 的第2行，最后报告该行。不要修改文件。"


def dump(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def classify_outcomes(
    source: str,
    port: str,
    *,
    approved_delta: bool = False,
    source_defect_confirmed: bool = False,
) -> str | None:
    """T-01 attribution requires two outcomes or independently confirmed cause.

    These flags are evidence decisions supplied by the caller, never guesses made
    from stderr substrings. Source failures cannot excuse unimplemented port work.
    """
    if "environment-error" in (source, port):
        return "ENV"
    if source == "failed" and source_defect_confirmed:
        return "SOURCE-DEFECT"
    if source == "passed" and port == "failed":
        return "INTENTIONAL-DELTA" if approved_delta else "PORT-REGRESSION"
    if source == "passed" and port == "passed":
        return None
    return "UNVERIFIED"


def isolated_env(home: Path, temp: Path, node: Path | None = None) -> dict[str, str]:
    """Allowlist OS essentials; do not copy caller keys, proxies or config variables."""
    home.mkdir(parents=True, exist_ok=True)
    temp.mkdir(parents=True, exist_ok=True)
    env = {
        key: os.environ[key]
        for key in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT")
        if key in os.environ
    }
    executables = [str(node) if node else shutil.which("node"), shutil.which("git")]
    paths = [str(Path(item).parent) for item in executables if item]
    paths += [str(Path(sys.executable).parent)]
    if os.name == "nt":
        paths += [str(Path(env.get("SystemRoot", "C:/Windows")) / "System32")]
        paths += [
            str(
                Path(env.get("SystemRoot", "C:/Windows"))
                / "System32/WindowsPowerShell/v1.0"
            )
        ]
    else:
        paths += ["/usr/bin", "/bin"]
    env.update(
        {
            "PATH": os.pathsep.join(dict.fromkeys(paths)),
            "HOME": str(home),
            "USERPROFILE": str(home),
            "APPDATA": str(home / "AppData/Roaming"),
            "LOCALAPPDATA": str(home / "AppData/Local"),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "TMP": str(temp),
            "TEMP": str(temp),
            "TMPDIR": str(temp),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(home / "empty.gitconfig"),
            "GIT_TERMINAL_PROMPT": "0",
            "DAO_USE_KEYCHAIN": "0",
            "DAO_NO_UPDATE_CHECK": "1",
            "DAO_REFLECT": "0",
            "DAO_LANG": "zh",
            "LANG": "zh_CN.UTF-8",
            "NO_COLOR": "1",
            "NPM_CONFIG_USERCONFIG": str(home / "empty.npmrc"),
            "NPM_CONFIG_GLOBALCONFIG": str(home / "global.npmrc"),
            "NPM_CONFIG_CACHE": str(home / "npm-cache"),
        }
    )
    for name in ("empty.gitconfig", "empty.npmrc", "global.npmrc"):
        (home / name).touch()
    return env


def prepare_source(
    root: Path, cache: Path, install_deps: bool = False, node: Path | None = None
) -> Path:
    """Only restore the designated archive; never consult the active DAO checkout."""
    reference = root / ".scratch/ruocun-discovery/reference" / SNAPSHOT
    tool = root / ".scratch/ruocun-discovery/reference_tool.py"
    env = isolated_env(cache / "tool-home", cache / "tool-temp", node)
    subprocess.run(
        [sys.executable, str(tool), "verify", str(reference)],
        env=env,
        check=True,
        capture_output=True,
    )
    source = cache / "source"
    if not source.exists():
        subprocess.run(
            [
                sys.executable,
                str(tool),
                "extract",
                str(reference),
                "--destination",
                str(source),
            ],
            env=env,
            check=True,
            capture_output=True,
        )
    # npm may create outputs but may not alter any frozen source bytes.
    manifest = json.loads((reference / "manifest.json").read_text(encoding="utf-8"))
    for row in manifest["files"]:
        if row["state"] == "present":
            actual = hashlib.sha256((source / row["path"]).read_bytes()).hexdigest()
            if actual != row["sha256"]:
                raise RuntimeError(f"Frozen source mismatch: {row['path']}")
    if install_deps or not (source / "node_modules/tsx/dist/loader.mjs").is_file():
        if not install_deps:
            raise RuntimeError("Source dependencies missing; rerun with --install-deps")
        npm = shutil.which("npm")
        if not npm:
            raise RuntimeError("npm unavailable")
        npm_command = [npm]
        if node is not None:
            npm_cli = Path(npm).parent / "node_modules/npm/bin/npm-cli.js"
            npm_command = [str(node), str(npm_cli)]
        completed = subprocess.run(
            [*npm_command, "ci", "--no-audit", "--no-fund"],
            check=False,
            cwd=source,
            env=env,
            capture_output=True,
            timeout=300,
        )
        (cache / "npm-ci.stdout.txt").write_bytes(completed.stdout)
        (cache / "npm-ci.stderr.txt").write_bytes(completed.stderr)
        completed.check_returncode()
    # Rebuild every run: a stale or manually edited dist cache is not an oracle.
    completed = subprocess.run(
        [
            str(node) if node else shutil.which("node"),
            str(source / "node_modules/typescript/bin/tsc"),
            "-p",
            "tsconfig.build.json",
        ],
        check=False,
        cwd=source,
        env=env,
        capture_output=True,
        timeout=120,
    )
    (cache / "build.stdout.txt").write_bytes(completed.stdout)
    (cache / "build.stderr.txt").write_bytes(completed.stderr)
    completed.check_returncode()
    return source


def scripted_events() -> list[dict]:
    calls = [
        {
            "index": 0,
            "id": "call_plan",
            "type": "function",
            "function": {
                "name": "TodoWrite",
                "arguments": '{"todos":[{"content":"读取材料","status":"in_progress"}]}',
            },
        },
        {
            "index": 1,
            "id": "call_read",
            "type": "function",
            "function": {
                "name": "Read",
                "arguments": '{"path":"材料 空格.txt","offset":2,"limit":1}',
            },
        },
    ]
    # Deliberately split argument text, as client.test.ts's stream assembly case.
    first = [
        {**call, "function": {"name": call["function"]["name"], "arguments": ""}}
        for call in calls
    ]
    return [
        {"choices": [{"delta": {"tool_calls": first}}]},
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": call["index"],
                                "function": {
                                    "arguments": call["function"]["arguments"][:12]
                                },
                            }
                            for call in calls
                        ]
                    }
                }
            ]
        },
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": call["index"],
                                "function": {
                                    "arguments": call["function"]["arguments"][12:]
                                },
                            }
                            for call in calls
                        ]
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        },
    ]


def stop_tree(process: subprocess.Popen, env: dict[str, str], output: Path) -> None:
    """Stop only this driver's process group/tree, before its root disappears."""
    if os.name == "nt":
        result = subprocess.run(
            [
                str(Path(env["SystemRoot"]) / "System32/taskkill.exe"),
                "/PID",
                str(process.pid),
                "/T",
                "/F",
            ],
            check=False,
            env=env,
            capture_output=True,
            timeout=15,
        )
        dump(
            output / "tree-stop.json",
            {
                "pid": process.pid,
                "returncode": result.returncode,
                "stdout": result.stdout.decode("utf-8", errors="replace"),
                "stderr": result.stderr.decode("utf-8", errors="replace"),
            },
        )
    else:
        os.killpg(process.pid, signal.SIGKILL)
        dump(
            output / "tree-stop.json",
            {"pid": process.pid, "signal": "SIGKILL", "scope": "process-group"},
        )
    if process.poll() is None:
        process.kill()


def run_oracle(
    root: Path,
    output: Path,
    *,
    cache: Path | None = None,
    install_deps: bool = False,
    timeout: float = 45,
    scenario: str = "plan-read",
    node: Path | None = None,
) -> dict:
    """Execute one source CLI round; always keep source/port evidence separate."""
    if scenario not in {"plan-read", "read-first", "stall"}:
        raise ValueError(f"Unknown oracle scenario: {scenario}")
    root, output = root.resolve(), output.resolve()
    node = node.resolve(strict=True) if node is not None else None
    output.mkdir(parents=True, exist_ok=False)
    cache = (cache or root / ".worktrees/oracle").resolve()
    summary = {
        "case_id": "TEST-02.ORACLE-" + scenario.upper(),
        "snapshot": SNAPSHOT,
        "source_tree_sha256": TREE,
        "source": {"status": "not-run"},
        "port": {"status": "not-run", "reason": "Product not implemented in ticket 02"},
        "classification": "UNVERIFIED",
        "paid_api_calls": 0,
        "live_model": "not-run",
        "terminal_experience": "not-run",
        "cleanup": {
            "child_exited": True,
            "server_closed": True,
            "tree_stop_requested": False,
        },
    }
    try:
        source = prepare_source(root, cache, install_deps, node)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        summary.update(
            classification="ENV",
            source={"status": "environment-error", "error": str(error)},
        )
        dump(output / "summary.json", summary)
        return summary
    runtime = output / "runtime"
    home, cwd = runtime / "home", runtime / "工作区 空格"
    cwd.mkdir(parents=True)
    env = isolated_env(home, runtime / "temp", node)
    for args in (
        ("init", "--initial-branch=oracle-fixture"),
        (
            "-c",
            "user.name=Oracle Fixture",
            "-c",
            "user.email=oracle@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "fixture",
        ),
    ):
        subprocess.run(
            [shutil.which("git"), *args],
            cwd=cwd,
            env=env,
            check=True,
            capture_output=True,
        )
    (cwd / "材料 空格.txt").write_text(
        "alpha\n口腔研究\nomega\n", encoding="utf-8", newline="\n"
    )
    dump(
        output / "input.json",
        {
            "prompt": PROMPT,
            "file": "材料 空格.txt",
            "bytes_utf8": "alpha\n口腔研究\nomega\n",
            "expected_read": "2\t口腔研究",
            "permission_mode": "plan",
        },
    )
    requests: list[dict] = []
    responses: list[dict] = []
    stopping = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            requests.append(
                {"method": "POST", "path": self.path, "body": json.loads(body)}
            )
            request_index = len(requests)
            (output / f"request-{request_index:03d}.body.json").write_bytes(body)
            if scenario == "stall":
                stopping.wait(timeout=timeout + 20)
                return
            if scenario == "read-first" and request_index == 1:
                events = [
                    {
                        "choices": [
                            {
                                "delta": {
                                    "tool_calls": [
                                        {
                                            "index": 0,
                                            "id": "call_probe",
                                            "type": "function",
                                            "function": {
                                                "name": "Read",
                                                "arguments": '{"path":"材料 空格.txt","offset":2,"limit":1}',
                                            },
                                        }
                                    ]
                                },
                                "finish_reason": "tool_calls",
                            }
                        ]
                    }
                ]
            elif request_index == (2 if scenario == "read-first" else 1):
                events = scripted_events()
            else:
                events = [
                    {
                        "choices": [
                            {
                                "delta": {"content": "ORACLE_COMPLETE"},
                                "finish_reason": "stop",
                            }
                        ]
                    }
                ]
            responses.append({"events": events})
            payload = (
                "".join(
                    "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"
                    for event in events
                )
                + "data: [DONE]\n\n"
            ).encode("utf-8")
            (output / f"response-{request_index:03d}.sse").write_bytes(payload)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            # Split UTF-8/SSE across writes; no fake internal DAO collaborators.
            for index in range(0, len(payload), 17):
                try:
                    self.wfile.write(payload[index : index + 17])
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    break

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    origin = f"http://127.0.0.1:{server.server_address[1]}"
    config = home / ".dao"
    config.mkdir()
    dump(
        config / "config.json",
        {
            "version": 2,
            "onboardingComplete": True,
            "activeProfile": "oracle",
            "profiles": {
                "oracle": {
                    "provider": "deepseek",
                    "baseUrl": origin + "/v1",
                    "model": "deepseek-v4-pro",
                    "key": "oracle-not-a-real-key",
                }
            },
        },
    )
    dump(config / "settings.json", {"language": "zh"})
    env.update(
        ORACLE_HTTP_ORIGIN=origin, ORACLE_NETWORK_LOG=str(output / "network.jsonl")
    )
    guard = Path(__file__).with_name("network_guard.mjs")
    node_command = str(node) if node else shutil.which("node")
    command = [
        node_command,
        "--import",
        guard.as_uri(),
        str(source / "dist/index.js"),
        "--eval",
        "--no-skills",
        "--no-hooks",
        "--no-progress-advice",
        "--permission-mode",
        "plan",
        PROMPT,
    ]
    dump(
        output / "command.json",
        {"argv": command, "cwd": str(cwd), "env": env, "stdin": "closed"},
    )
    dependencies = {}
    for name in (
        "tsx",
        "vitest",
        "typescript",
        "better-sqlite3",
        "zod",
        "zod-to-json-schema",
        "ink",
    ):
        dependencies[name] = json.loads(
            (source / "node_modules" / name / "package.json").read_text(
                encoding="utf-8"
            )
        )["version"]
    fingerprints = {
        name: hashlib.sha256((source / name).read_bytes()).hexdigest()
        for name in (
            "package-lock.json",
            "dist/index.js",
            "node_modules/better-sqlite3/build/Release/better_sqlite3.node",
        )
    }
    fingerprints["network_guard.mjs"] = hashlib.sha256(guard.read_bytes()).hexdigest()
    fingerprints["driver.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    dump(
        output / "environment.json",
        {
            "python": sys.version,
            "platform": sys.platform,
            "node": subprocess.check_output([node_command, "--version"], env=env)
            .decode()
            .strip(),
            "dependencies": dependencies,
            "sha256": fingerprints,
        },
    )
    thread.start()
    process = None
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            )
            if os.name == "nt"
            else 0,
            start_new_session=os.name != "nt",
        )
        summary["cleanup"]["child_exited"] = False
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            summary["cleanup"]["tree_stop_requested"] = True
            stop_tree(process, env, output)
            stdout, stderr = process.communicate(timeout=10)
            summary["source"] = {
                "status": "canceled",
                "reason": "Oracle deadline exceeded; driver requested process-tree stop",
            }
        (output / "stdout.txt").write_bytes(stdout)
        (output / "stderr.txt").write_bytes(stderr)
        summary["cleanup"]["child_exited"] = process.poll() is not None
        summary["source"]["exit_code"] = process.returncode
        if summary["source"]["status"] != "canceled":
            results = {
                message["tool_call_id"]: message["content"]
                for request in requests[1:]
                for message in request["body"]["messages"]
                if message["role"] == "tool"
            }
            checks = {
                "exit_zero": process.returncode == 0,
                "expected_requests": len(requests)
                == (3 if scenario == "read-first" else 2),
                "read_result": results.get("call_read") == "2\t口腔研究",
                "plan_result": results.get("call_plan") == "▶ 读取材料",
                "scripted_completion": b"ORACLE_COMPLETE" in stdout,
                "fixture_unchanged": (cwd / "材料 空格.txt").read_bytes()
                == "alpha\n口腔研究\nomega\n".encode(),
            }
            if scenario == "read-first":
                checks["headless_first_batch_rejected"] = "TodoWrite" in results.get(
                    "call_probe", ""
                ) and "口腔研究" not in results.get("call_probe", "")
            summary["source"].update(
                status="passed" if all(checks.values()) else "failed", checks=checks
            )
            # A failed run alone does not prove a source defect; retain it for triage.
    except OSError as error:
        summary.update(
            classification="ENV",
            source={"status": "environment-error", "error": str(error)},
        )
    finally:
        if process is not None and process.poll() is None:
            summary["cleanup"]["tree_stop_requested"] = True
            stop_tree(process, env, output)
            process.wait(timeout=10)
        stopping.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        summary["cleanup"]["server_closed"] = not thread.is_alive()
        dump(output / "requests.json", requests)
        dump(output / "responses.json", responses)
        summary["classification"] = classify_outcomes(
            summary["source"]["status"], summary["port"]["status"]
        )
        dump(output / "summary.json", summary)
        hashes = {
            str(path.relative_to(output)).replace("\\", "/"): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in output.iterdir()
            if path.is_file() and path.name != "sha256.json"
        }
        dump(output / "sha256.json", hashes)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--node", type=Path)
    parser.add_argument("--install-deps", action="store_true")
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument(
        "--scenario", choices=("plan-read", "read-first", "stall"), default="plan-read"
    )
    args = parser.parse_args()
    root = args.source_root.resolve()
    result = run_oracle(
        root,
        args.output,
        cache=args.cache,
        install_deps=args.install_deps,
        timeout=args.timeout,
        scenario=args.scenario,
        node=args.node,
    )
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["source"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
