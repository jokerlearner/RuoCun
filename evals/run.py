"""冻结 evals/run.mjs（MIT）：隔离工作区中的真实 CLI 与双轨评分。"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import uuid
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import ruocun
from ruocun.config.profiles import DEFAULTS, resolveActive
from ruocun.config.profiles_store import UnsupportedProfilesError, loadProfiles
from ruocun.platform.file_contract import AtomicFileError
from ruocun.platform.process_tree import ForegroundResult, run_foreground_argv
from ruocun.platform.windows.durable_file import atomic_publish

from .materialize_trace import findSessionDir
from .render_trace import renderTraceHtml
from .score import weightedCompletion

_TASKS = Path(__file__).parent / "tasks"
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_ALLOW_ENV = ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "LANG", "LC_ALL")
_LOOPBACK = ("localhost", "127.0.0.1", "::1")
_LOCAL_CHECK = """
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
const [script, data] = process.argv.slice(1);
const context = JSON.parse(await readFile(data, 'utf8'));
const module = await import(pathToFileURL(script));
const verdict = await module.default(context);
console.log(JSON.stringify(verdict));
"""


class EnvironmentIssue(RuntimeError):
    """Required trusted evaluator assets or environment are unavailable."""


class OutcomeUnknown(RuntimeError):
    """External state is preserved because completion or cleanup was not confirmed."""


class CredentialCleanupUnknown(OutcomeUnknown):
    """Private evaluation credentials could not be confirmed removed."""


class InvalidTask(ValueError):
    """The frozen assertion does not discriminate a buggy baseline."""


@dataclass(frozen=True)
class Task:
    id: str
    directory: Path
    definition: dict[str, Any]

    @property
    def kind(self) -> str:
        return str(self.definition.get("kind", "local"))


@dataclass(frozen=True)
class Settings:
    config: Path
    timeout: float
    model: str | None
    node: str | None = None
    git: str | None = None
    bash: str | None = None
    docker: str | None = None
    network: bool = False
    live: bool = False
    inference_only: bool = False


def loadTasks(directory: Path, selected: list[str]) -> list[Task]:
    candidates = sorted(directory.glob("*/task.json"))
    return [
        Task(path.parent.name, path.parent.resolve(), json.loads(path.read_text(encoding="utf-8")))
        for path in candidates if not selected or path.parent.name in selected
    ]


def executable(name: str, override: str | None = None) -> str:
    found = shutil.which(override or name)
    if found is None:
        raise EnvironmentIssue(f"缺少 {name} 可执行文件。")
    return str(Path(found).absolute())


def _run(argv: list[str], cwd: Path, env: dict[str, str], timeout: float, data: bytes | None = None) -> ForegroundResult:
    signal = threading.Event()
    timer = threading.Timer(timeout, signal.set)
    timer.start()
    try:
        return run_foreground_argv(argv, str(cwd), signal, environ=env, stdinData=data, outputLimit=2_000_000)
    except RuntimeError:
        raise OutcomeUnknown("受管进程退出或输出未确认，保留工作区。") from None
    finally:
        timer.cancel()
        timer.join()


def _task_path(root: Path, name: str) -> Path:
    candidate = (root / name).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise InvalidTask("测试资产路径越出任务目录。")
    return candidate


def _check_code(result: ForegroundResult, phase: str) -> None:
    if result.aborted:
        raise EnvironmentIssue(f"{phase} 超时。")
    if result.outputCapped:
        raise EnvironmentIssue(f"{phase} 输出已截断，无法确认完整结果。")
    if result.code in (126, 127):
        raise EnvironmentIssue(f"{phase} 无法执行（{result.code}）。")


def _checked(result: ForegroundResult, phase: str) -> None:
    _check_code(result, phase)
    if result.code != 0:
        raise EnvironmentIssue(f"{phase} 失败（{result.code}）。")


def _profile(config: Path, *, live: bool) -> tuple[dict[str, Any], tuple[str, ...]]:
    try:
        active = resolveActive(loadProfiles(config))
    except UnsupportedProfilesError:
        raise EnvironmentIssue("评估账户配置版本不受支持。") from None
    if active is None:
        raise EnvironmentIssue("评估账户需要显式内联 key，无法使用系统凭据引用。")
    provider, model, base = active.get("provider"), active.get("model"), active.get("baseUrl")
    if provider not in DEFAULTS or not isinstance(model, str) or not model or not isinstance(base, str):
        raise EnvironmentIssue("评估账户必须有有效 provider、model 和 baseUrl。")
    url = urlsplit(base)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
        raise EnvironmentIssue("评估 baseUrl 无效。")
    if url.hostname not in _LOOPBACK and not live:
        raise EnvironmentIssue("离线运行仅接受本地环回账户。")
    key = active["key"]
    normalized = {"provider": provider, "model": model, "baseUrl": base, "key": key}
    return {"version": 2, "activeProfile": "eval", "profiles": {"eval": normalized}}, (key,)


def _isolated_env(home: Path, *, enable_auto: bool = True) -> dict[str, str]:
    home.mkdir(parents=True, exist_ok=True)
    temp = home / "tmp"
    temp.mkdir(exist_ok=True)
    env = {key: os.environ[key] for key in _ALLOW_ENV if key in os.environ}
    env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
               TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp), PROGRAMDATA=str(home / "program-data"),
               XDG_CONFIG_HOME=str(home), PYTHONUTF8="1", GIT_TERMINAL_PROMPT="0")
    if enable_auto:
        env.update(RUOCUN_AUTO_APPROVE="1", RUOCUN_DECK="0", RUOCUN_CACHE_AUDIT="1", RUOCUN_USE_KEYCHAIN="0")
    return env


@contextmanager
def privateProfile(profile: dict[str, Any]) -> Iterator[Path]:
    credential_dir = Path(tempfile.mkdtemp(prefix="rc-key-"))
    config = credential_dir / "private" / "eval-config.json"
    try:
        try:
            serialized = json.dumps(profile, ensure_ascii=False).encode("utf-8")
            if os.name == "nt":
                atomic_publish(config, serialized, require_durability=False)
            else:
                config.parent.mkdir(mode=0o700)
                fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as file:
                    file.write(serialized)
        except AtomicFileError:
            raise EnvironmentIssue("无法发布临时私有账户配置。") from None
        yield config
    finally:
        try:
            config.unlink(missing_ok=True)
            if config.parent.is_dir():
                config.parent.rmdir()
            credential_dir.rmdir()
        except OSError:
            raise CredentialCleanupUnknown("临时账户文件清理未确认，保留隔离现场。") from None


def agent_command(
    config: Path, cwd: Path, prompt: str | None, model: str | None, *, evaluation: bool = True, local_only: bool = True,
) -> list[str]:
    package_root = Path(ruocun.__file__).resolve().parent.parent
    launch = f"import runpy,sys;sys.path.insert(0,{str(package_root)!r});"
    if local_only:
        eval_root = Path(__file__).resolve().parent.parent
        launch += (f"sys.path.insert(0,{str(eval_root)!r});"
                   "from evals.local_model import installOfflineOpener;installOfflineOpener();")
    launch += "runpy.run_module('ruocun',run_name='__main__')"
    argv = [sys.executable, "-I", "-X", "utf8", "-c", launch, "--no-hooks", "--no-skills",
            "--cwd", str(cwd), "--config", str(config)]
    if evaluation:
        argv.append("--eval")
    else:
        argv.extend(("--no-mcp", "--no-web", "--no-project-instructions"))
    if model:
        argv.extend(("--model", model))
    if prompt:
        argv.extend(("--", prompt))
    return argv


class _Attempt:
    def __init__(self, task: Task, settings: Settings, work: Path, control: Path) -> None:
        self.task, self.settings, self.work, self.control = task, settings, work, control
        self.definition = task.definition
        self.remote = task.kind in ("oss", "docker")
        self.env = _isolated_env(control / "checks", enable_auto=False)
        self.git = executable("git", settings.git) if self.remote and settings.network else None

    def exec(self, argv: list[str], data: bytes | None = None, *, cwd: Path | None = None) -> ForegroundResult:
        try:
            return _run(argv, cwd or self.work, self.env, self.settings.timeout, data)
        except OSError as error:
            raise EnvironmentIssue(f"子进程无法启动（{type(error).__name__}）。") from error

    def git_cmd(self, *args: str) -> ForegroundResult:
        if self.git is None:
            raise EnvironmentIssue("没有已授权的 Git 路由。")
        return self.exec([self.git, "-C", str(self.work), *args])

    def prepare(self) -> None:
        if not self.remote:
            source = self.task.directory / "workspace"
            if source.is_dir():
                shutil.copytree(source, self.work, dirs_exist_ok=True)
            return
        if not self.settings.network or self.git is None:
            raise EnvironmentIssue("该任务需要已授权的外部 Git/安装资源。")
        if self.task.kind == "docker":
            _checked(self.exec([executable("docker", self.settings.docker), "version", "--format", "{{.Server.Version}}"]), "Docker")
        repo = self.definition["repo"]
        if urlsplit(repo).scheme not in ("https", "file") and not Path(repo).is_absolute():
            raise EnvironmentIssue("仅接受明确的 HTTPS 或本地仓库。")
        _checked(self.exec([self.git, "clone", "--", repo, str(self.work)], cwd=self.control), "仓库克隆")
        refs = [self.definition[field] for field in ("ref", "fix_ref") if self.definition.get(field)]
        for ref in refs:
            if self.git_cmd("cat-file", "-e", ref + "^{commit}").code != 0:
                result = self.git_cmd("fetch", "--depth", "1", "origin", ref)
                if result.code != 0:
                    _checked(self.git_cmd("fetch", "origin", ref), "冻结提交获取")
        _checked(self.git_cmd("checkout", "--detach", self.definition["ref"]), "冻结基线检出")
        install = self.definition.get("install") or []
        for command in [install] if isinstance(install, str) else install:
            _checked(self.check(command, phase="install"), "依赖安装")

    def inject(self) -> None:
        files, fix_ref = self.definition.get("test_files"), self.definition.get("fix_ref")
        if files and fix_ref:
            paths = [files] if isinstance(files, str) else files
            for name in paths:
                _task_path(self.work, name)
            _checked(self.git_cmd("checkout", fix_ref, "--", *paths), "隐藏验证器注入")

    def restore(self) -> None:
        files = self.definition.get("test_files") or []
        for name in [files] if isinstance(files, str) else files:
            path = _task_path(self.work, name)
            tracked = self.git_cmd("ls-tree", "-r", "--name-only", self.definition["ref"], "--", name)
            _checked(tracked, "基线验证器探测")
            if tracked.stdout.strip():
                _checked(self.git_cmd("checkout", self.definition["ref"], "--", name), "恢复基线验证器")
            else:
                _checked(self.git_cmd("rm", "--cached", "-f", "--ignore-unmatch", "--", name), "隐藏验证器撤除索引")
                path.unlink(missing_ok=True)

    def _docker(self, command: str, phase: str) -> ForegroundResult:
        docker = executable("docker", self.settings.docker)
        name = "ruocun-eval-" + uuid.uuid4().hex
        find = [docker, "container", "ls", "--all", "--filter", f"name=^/{name}$", "--format", "{{.ID}}"]
        _checked(self.exec(find), "Docker 生命周期核验")
        arguments = [docker, "container", "create", "--name", name, "-v", f"{self.work}:/work", "-w", "/work"]
        if phase == "test":
            arguments.extend(("--network", "none", "--cap-drop=ALL", "--security-opt", "no-new-privileges",
                              "--cpus=2", "--memory=4g", "--pids-limit=512"))
            command = "timeout 600 " + command
        created = self.exec([*arguments, self.definition["image"], "bash", "-lc", command])
        if created.aborted:
            raise OutcomeUnknown(f"Docker 创建未确认，保留工作区并核对容器 {name}。")
        if created.code:
            state = self.exec(find)
            if state.aborted or state.code or state.stdout.strip():
                raise OutcomeUnknown(f"Docker 创建未确认，保留工作区并核对容器 {name}。")
            _checked(created, "Docker 容器创建")
        cid = created.stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{64}", cid):
            raise OutcomeUnknown(f"Docker 容器身份未确认，保留工作区并核对容器 {name}。")
        try:
            result = self.exec([docker, "container", "start", "--attach", cid])
            if result.aborted:
                raise EnvironmentIssue("Docker 命令超时。")
            observed = self.exec([docker, "container", "inspect", "--format",
                                  "{{.State.Running}} {{.State.ExitCode}}", cid])
            if observed.aborted or observed.code != 0 or not re.fullmatch(r"false [0-9]+", observed.stdout.strip()):
                raise OutcomeUnknown(f"Docker 执行终态未确认，检查容器 {name} 的命令回执。")
            code = int(observed.stdout.split()[1])
            if phase == "test" and code == 124:
                raise EnvironmentIssue("容器内验证器超时。")
            return replace(result, code=code)
        finally:
            try:
                removed = self.exec([docker, "container", "rm", "--force", cid])
                remaining = self.exec(find)
                confirmed = not removed.aborted and removed.code == 0 and not remaining.aborted and remaining.code == 0
            except EnvironmentIssue:
                confirmed = False
            if not confirmed or remaining.stdout.strip():
                raise OutcomeUnknown(f"Docker 清理未确认，保留工作区并核对容器 {name}。")

    def check(self, command: str, *, phase: str = "test") -> ForegroundResult:
        if self.task.kind == "docker":
            return self._docker(command, phase)
        elif self.remote:
            argv = [executable("bash", self.settings.bash), "-lc", command]
        else:
            path = _task_path(self.task.directory, command)
            if not path.is_file():
                raise EnvironmentIssue("缺少冻结任务验证器。")
            argv = [sys.executable, "-I", str(path), str(self.work)] if path.suffix == ".py" else [
                executable("node", self.settings.node), str(path), str(self.work),
            ]
        result = self.exec(argv)
        _check_code(result, phase)
        return result

    def preflight(self) -> dict[str, Any]:
        fail2pass = self.definition.get("fail2pass")
        if self.task.kind == "local" or not fail2pass:
            return {}
        if self.remote:
            self.inject()
        try:
            base = self.check(fail2pass)
        finally:
            if self.remote:
                self.restore()
        if base.code == 0:
            raise InvalidTask("基线未改动时 fail2pass 已经通过。")
        if self.definition.get("pass2pass"):
            stable = self.check(self.definition["pass2pass"])
            if stable.code != 0:
                raise InvalidTask("基线 pass2pass 未通过。")
        return {"baselineFail2passExit": base.code}

    def judge(self, result: ForegroundResult) -> dict[str, Any]:
        if self.task.kind == "local":
            path = self.task.directory / "check.mjs"
            if not path.is_file():
                raise EnvironmentIssue("缺少冻结本地检查入口。")
            data = self.control / "check.json"
            data.write_text(json.dumps({"workspace": str(self.work), "output": _ANSI.sub("", result.stdout + result.stderr),
                                        "exitCode": result.code}, ensure_ascii=False), encoding="utf-8")
            verdict = self.exec([executable("node", self.settings.node), "--input-type=module", "-e", _LOCAL_CHECK,
                                 str(path), str(data)])
            _checked(verdict, "本地检查")
            parsed = json.loads(verdict.stdout.splitlines()[-1])
            passed = parsed.get("pass") is True
            return {"pass": passed, "note": str(parsed.get("note", "")), "completion": int(passed)}
        checkpoints = self.definition.get("checkpoints") or []
        fail2pass, pass2pass = self.definition.get("fail2pass"), self.definition.get("pass2pass")
        if not (checkpoints or fail2pass or pass2pass):
            raise InvalidTask("双轨任务缺少验证器。")
        outcomes = [(checkpoint, self.check(checkpoint["cmd"])) for checkpoint in checkpoints]
        stable = self.check(pass2pass) if pass2pass else None
        stable_ok = stable is None or stable.code == 0
        stable_out = stable.stdout + stable.stderr if stable is not None else ""
        if outcomes:
            completed = weightedCompletion(checkpoints, [checkpoint["id"] for checkpoint, check in outcomes if check.code == 0])
            passed = completed["completion"] == 1 and stable_ok
            logs = "\n".join(f"## {checkpoint['id']} ({check.code})\n{check.stdout}{check.stderr}"
                             for checkpoint, check in outcomes)
            return {"pass": passed, "completion": completed["completion"], "checkpoints": completed,
                    "note": "" if passed else "加权检查点或 pass2pass 未通过", "f2pOut": logs, "p2pOut": stable_out}
        fixed = self.check(fail2pass) if fail2pass else None
        fixed_ok = fixed is None or fixed.code == 0
        passed = fixed_ok and stable_ok
        return {"pass": passed, "completion": int(passed),
                "note": "" if passed else "pass2pass 未通过" if fixed_ok else "fail2pass 未通过",
                "f2pOut": fixed.stdout + fixed.stderr if fixed is not None else "", "p2pOut": stable_out}

    def diff(self) -> str:
        if self.remote:
            if self.settings.inference_only:
                _checked(self.git_cmd("add", "-A", "--", ".", ":(exclude).ruocun"), "暂存推理补丁")
                tracked = self.git_cmd("diff", "--cached", "HEAD", "--")
            else:
                tracked = self.git_cmd("diff", "HEAD", "--")
            _checked(tracked, "评估补丁采集")
            return tracked.stdout
        source = self.task.directory / "workspace"
        paths = sorted({path.relative_to(root) for root in (source, self.work) if root.is_dir()
                        for path in root.rglob("*") if path.is_file() and not path.is_symlink()
                        and path.resolve().is_relative_to(root.resolve()) and not {".git", ".ruocun"}.intersection(path.parts)})
        result: list[str] = []
        for rel in paths:
            old, new = source / rel, self.work / rel
            if any(path.is_symlink() or not path.resolve().is_relative_to(root.resolve())
                   or path.is_file() and path.stat().st_size > 2_000_000
                   for path, root in ((old, source), (new, self.work))):
                continue
            try:
                before = old.read_text(encoding="utf-8").splitlines() if old.is_file() else []
                after = new.read_text(encoding="utf-8").splitlines() if new.is_file() else []
            except (OSError, UnicodeError):
                continue
            result.extend(difflib.unified_diff(before, after, f"a/{rel.as_posix()}", f"b/{rel.as_posix()}", lineterm=""))
        return "\n".join(result)


def _persist(directory: Path, report: dict[str, Any], *, output: str = "", diff: str = "", redact: Any = str) -> None:
    (directory / "agent.log").write_text(redact(output), encoding="utf-8")
    (directory / "agent.diff").write_text(redact(diff or "(无改动)"), encoding="utf-8")
    for key, name in (("f2pOut", "fail2pass.log"), ("p2pOut", "pass2pass.log")):
        if key in report:
            (directory / name).write_text(redact(report.pop(key)), encoding="utf-8")
    report["note"] = redact(report["note"])
    (directory / "meta.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def runOnce(task: Task, settings: Settings, destination: Path, index: int) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "id": task.id, "kind": task.kind, "run": index, "pass": False, "completion": 0, "note": "",
        "humanMinutes": task.definition.get("humanMinutes"), "tools": 0, "ms": 0,
        "mode": "live" if settings.live else "offline",
    }
    redact: Callable[[str], str] = str
    output = diff = ""
    root = Path(tempfile.mkdtemp(prefix="rc-"))
    try:
        work, control = root / "w", root / "c"
        work.mkdir()
        control.mkdir()
        try:
            profile, secrets = _profile(settings.config, live=settings.live)
            if secrets:
                pattern = re.compile("|".join(re.escape(secret) for secret in sorted(secrets, key=len, reverse=True)))

                def scrub(value: str) -> str:
                    return pattern.sub("[REDACTED]", value)

                redact = scrub

            attempt = _Attempt(task, settings, work, control)
            attempt.prepare()
            report.update(attempt.preflight())
            home = control / "a"
            env = _isolated_env(home)
            try:
                with privateProfile(profile) as config:
                    pipe = task.definition.get("input")
                    stdin_data = ("\n".join(pipe) + "\n").encode("utf-8") if pipe else None
                    argv = agent_command(config, work, task.definition.get("prompt"), settings.model, local_only=not settings.live)
                    result = _run(argv, work, env, settings.timeout, stdin_data)
            except CredentialCleanupUnknown:
                report["credentialCleanup"] = "unconfirmed"
                raise
            finally:
                report.setdefault("credentialCleanup", "confirmed")
            output = _ANSI.sub("", result.stdout + result.stderr)
            report.update(ms=result.elapsedMs, tools=output.count("→ "), agentExit=result.code)
            diff = attempt.diff() if not result.outputCapped else ""
            if result.aborted:
                report.update(status="timeout", note="Agent 超时，受管进程树已发出取消。")
            elif result.outputCapped:
                report.update(status="environment_unavailable", note="Agent 输出已截断，无法完成评分。")
            elif result.code != 0:
                report.update(status="agent_error", note=f"Agent 未正常退出（{result.code}）。")
            elif settings.inference_only:
                if redact(diff) == diff:
                    report["status"] = "prediction_ready"
                else:
                    report.update(status="sensitive_output", note="补丁包含账户凭据，拒绝生成预测。")
            else:
                if attempt.remote:
                    attempt.inject()
                report.update(attempt.judge(result))
                report["status"] = "passed" if report["pass"] else "failed"
            session = findSessionDir(home)
            if session is None:
                report["traceStatus"] = "session_missing"
            else:
                trace = destination / "trace"
                try:
                    repo = Path(__file__).resolve().parent.parent
                    package = Path(ruocun.__file__).resolve().parent.parent
                    launch = (f"import runpy,sys;sys.path[:0]=[{str(repo)!r},{str(package)!r}];"
                              "runpy.run_module('evals.materialize_trace',run_name='__main__')")
                    projection = _run([sys.executable, "-I", "-X", "utf8", "-c", launch,
                                       str(session), str(trace), "--redact-stdin"], work, env, settings.timeout,
                                      json.dumps(secrets).encode("utf-8"))
                    _checked(projection, "会话轨迹投影")
                    report["trace"] = json.loads(projection.stdout)
                    report["tools"] = report["trace"]["tools"]
                    html = renderTraceHtml(trace, passed=None if settings.inference_only else report["pass"], task_id=task.id)
                    (trace / "trace.html").write_text(html, encoding="utf-8")
                    report["traceStatus"] = "materialized"
                except OutcomeUnknown:
                    raise
                except Exception as error:
                    report.update(traceStatus="unavailable", traceError=type(error).__name__)
        except OutcomeUnknown as error:
            report.update(status="outcome_unknown", note=str(error))
            report["pass"] = False
        except EnvironmentIssue as error:
            report.update(status="environment_unavailable", note=str(error))
        except InvalidTask as error:
            report.update(status="invalid_task", note=str(error))
        except (KeyError, TypeError, ValueError, OSError) as error:
            report.update(status="runner_error", note=f"评估材料或运行异常（{type(error).__name__}）。")
    finally:
        if report.get("status") != "outcome_unknown":
            try:
                shutil.rmtree(root)
            except OSError:
                report.update(status="outcome_unknown", note="工作区清理结果未确认。")
                report["pass"] = False
        if report.get("status") == "outcome_unknown":
            report["workspaceRetained"] = str(root)
        _persist(destination, report, output=output, diff=diff, redact=redact)
    return report


def _write_report(output: Path, rows: list[tuple[Task, list[dict[str, Any]]]], repeats: int, *, live: bool) -> None:
    lines = ["# RuoCun 评估", "", f"- 模式 {'live' if live else 'offline'}",
             f"- 稳定解决 pass^{repeats} {sum(all(run['pass'] for run in runs) for _, runs in rows)}/{len(rows)}",
             f"- 至少解决一次 {sum(any(run['pass'] for run in runs) for _, runs in rows)}/{len(rows)}", "",
             "| 任务 | 类型 | 通过 | 完成度 | 工具/次 | 秒/次 | 实际结果 |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for task, runs in rows:
        counts = Counter(run["status"] for run in runs)
        reasons = ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
        fraction = sum(run["completion"] for run in runs) / repeats
        tools = sum(run["tools"] for run in runs) / repeats
        seconds = sum(run["ms"] for run in runs) / repeats / 1000
        lines.append(f"| {task.id} | {task.kind} | {sum(run['pass'] for run in runs)}/{repeats} "
                     f"| {fraction:.0%} | {tools:.1f} | {seconds:.1f} | {reasons} |")
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", nargs="*")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--tasks-dir", type=Path, default=_TASKS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--runs", type=int, default=os.environ.get("EVAL_RUNS", "3"))
    parser.add_argument("--timeout-ms", type=int, default=os.environ.get("EVAL_TIMEOUT_MS", "180000"))
    parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL"))
    parser.add_argument("--node", default=os.environ.get("RUOCUN_ORACLE_NODE"))
    parser.add_argument("--git")
    parser.add_argument("--bash")
    parser.add_argument("--docker")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()
    tasks = loadTasks(args.tasks_dir, args.tasks)
    if not tasks or set(args.tasks).difference(task.id for task in tasks):
        parser.error("没有匹配的评估任务。")
    if args.list:
        for task in tasks:
            print(f"{task.id}\t{task.kind}")
        return 0
    if not args.output or not args.config or args.runs < 1 or args.timeout_ms < 1:
        parser.error("运行时提供 --config、--output，并使用正数次数和超时。")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    settings = Settings(args.config.resolve(), args.timeout_ms / 1000, args.model, args.node,
                        args.git, args.bash, args.docker, args.allow_network, args.allow_live)
    rows = [(task, [runOnce(task, settings, output / task.id / f"run-{index}", index)
                    for index in range(1, args.runs + 1)]) for task in tasks]
    _write_report(output, rows, args.runs, live=args.allow_live)
    print(output / "report.md")
    return 0 if all(run["pass"] and run.get("traceStatus") == "materialized" for _, runs in rows for run in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
