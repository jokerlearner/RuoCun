"""选择 Shell 方言，过滤子进程环境中的敏感项，并监督前台进程树。

Windows 用 Job 管理整棵树，POSIX 用独立进程组。取消和超限的回收在这里统一处理。
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Literal

if TYPE_CHECKING:
    from .shell_plan import ShellExecutionPlan

_SENSITIVE_ENV = re.compile(
    r"API_?KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|DEEPSEEK|ANTHROPIC|OPENAI|"
    r"AWS_(ACCESS|SECRET|SESSION)|GH_TOKEN|GITHUB_TOKEN|NPM_TOKEN|PRIVATE_KEY", re.I
)
OUT_CAP = 10 * 1024 * 1024
OutputCallback = Callable[[Literal["stdout", "stderr"], str], None]
ChunkCallback = Callable[[int, bytes], None]


@dataclass(frozen=True)
class ForegroundResult:
    stdout: str
    stderr: str
    code: int
    aborted: bool
    elapsedMs: int
    stdoutRaw: bytes = b""
    stderrRaw: bytes = b""
    decodingDiagnostics: tuple[str, ...] = ()
    outputCapped: bool = False


def shell_argv(command: str) -> list[str]:
    from .shell_plan import buildShellPlan
    return list(buildShellPlan(command, os.getcwd(), analyze=False).argv)


def scrubbed_env(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    values = os.environ if environ is None else environ
    return {key: value for key, value in values.items() if not _SENSITIVE_ENV.search(key)}


def _write_process_input(stream: BinaryIO, payload: bytes, errors: list[BaseException]) -> None:
    try:
        with stream:
            remaining = memoryview(payload)
            while remaining:
                count = stream.write(remaining)
                if not count:
                    raise OSError("进程输入未完整发送。")
                remaining = remaining[count:]
    except BrokenPipeError:
        pass  # Hook 可能不读输入就关闭 stdin，此时发送端结束写入即可。
    except BaseException as error:
        errors.append(error)


def _run_posix(
    argv: list[str], cwd: str, env: dict[str, str], signal: threading.Event,
    onChunk: ChunkCallback | None = None, *, captureOutput: bool = True,
    stdinData: bytes | None = None, cap: int = OUT_CAP, perStreamLimit: bool = False,
) -> tuple[bytes, bytes, int, bool, bool]:
    process = subprocess.Popen(
        argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL if stdinData is None else subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
    )
    # 以独立进程组启动，后续可一次终止 Shell 和同组子进程。
    signals = importlib.import_module("signal")
    killpg = getattr(os, "killpg")
    output = [bytearray(), bytearray()]
    lock = threading.Lock()
    capped = threading.Event()
    read_errors: list[BaseException] = []

    def stop_group() -> None:
        try:
            killpg(process.pid, signals.SIGKILL)
        except ProcessLookupError:
            pass

    def drain(index: int) -> None:
        stream = process.stdout if index == 0 else process.stderr
        assert stream is not None
        try:
            with stream:
                while chunk := os.read(stream.fileno(), 65536):
                    with lock:
                        used = len(output[index]) if perStreamLimit else len(output[0]) + len(output[1])
                        remaining = cap - used if captureOutput else len(chunk)
                        if captureOutput:
                            output[index].extend(chunk[:remaining])
                        if len(chunk) > remaining:
                            capped.set()
                    if onChunk is not None and chunk[:remaining]:
                        onChunk(index, chunk[:remaining])
        except BaseException as error:
            read_errors.append(error)

    readers = [threading.Thread(target=drain, args=(index,), daemon=True) for index in range(2)]
    if stdinData is not None:
        assert process.stdin is not None
        readers.append(threading.Thread(target=_write_process_input, args=(process.stdin, stdinData, read_errors), daemon=True))
    for reader in readers:
        reader.start()
    aborted = False
    try:
        while process.poll() is None:
            if signal.is_set() or capped.is_set() or read_errors:
                aborted = signal.is_set()
                stop_group()
                break
            time.sleep(.02)
        code = process.wait()
        stop_group()  # 即使 Shell 本身退出，持有输出管道的子孙仍会让读端等待，需要一并回收。
        for reader in readers:
            reader.join(10)
            if reader.is_alive():
                raise RuntimeError("Shell输出管道退出未确认。")
        if read_errors:
            raise RuntimeError("无法读取Shell输出。") from read_errors[0]
        return bytes(output[0]), bytes(output[1]), code, aborted, capped.is_set()
    finally:
        stop_group()
        process.wait()


def run_foreground(command: str, cwd: str, signal: threading.Event) -> ForegroundResult:
    if signal.is_set():
        return ForegroundResult("", "", 1, True, 0)
    from .shell_plan import buildShellPlan
    return run_foreground_plan(buildShellPlan(command, cwd, analyze=False), signal)


def run_foreground_argv(
    argv: list[str], cwd: str, signal: threading.Event, *, environ: Mapping[str, str] | None = None,
    commandLine: str | None = None, codec: str = "utf-8", onOutput: OutputCallback | None = None,
    decodeClixml: bool = False, onRawOutput: ChunkCallback | None = None, captureOutput: bool = True,
    onLogOutput: OutputCallback | None = None, stdinData: bytes | None = None, outputLimit: int | None = None,
) -> ForegroundResult:
    """用已解析的可执行文件绝对路径和参数启动受控前台进程树。"""
    start = time.monotonic()
    if signal.is_set():
        return ForegroundResult("", "", 1, True, 0)
    if not argv or not Path(argv[0]).is_absolute():
        raise ValueError("前台参数入口需要绝对可执行文件路径。")
    from .shell_output import ShellOutputDecoder
    decoders = [ShellOutputDecoder(codec), ShellOutputDecoder(codec, clixml=decodeClixml or Path(argv[0]).name.casefold() in {"powershell.exe", "pwsh.exe"}, clixmlLimit=OUT_CAP if not captureOutput else None)]
    decoded: list[list[str]] = [[], []]
    observer_errors: list[str] = []
    names: tuple[Literal["stdout", "stderr"], ...] = ("stdout", "stderr")

    def emit(index: int, text: str) -> None:
        if onLogOutput is not None:
            onLogOutput(names[index], text)
        if onOutput is not None and not signal.is_set():
            try:
                onOutput(names[index], text)
            except Exception as error:
                message = f"实时输出回调不可用（{type(error).__name__}）；完整结果仍保留"
                if message not in observer_errors:
                    observer_errors.append(message)

    def chunk(index: int, raw: bytes) -> None:
        if onRawOutput is not None:
            onRawOutput(index, raw)
        text = decoders[index].feed(raw)
        if text:
            if captureOutput:
                decoded[index].append(text)
            emit(index, text)

    env = scrubbed_env(environ)
    cap = OUT_CAP if outputLimit is None else outputLimit
    if os.name == "nt":
        from .windows.process_tree import run_managed

        stdout, stderr, code, aborted, capped = run_managed(
            argv, cwd, env, signal, cap, commandLine=commandLine, onChunk=chunk, captureOutput=captureOutput,
            stdinData=stdinData, perStreamLimit=outputLimit is not None,
        )
    else:
        stdout, stderr, code, aborted, capped = _run_posix(
            argv, cwd, env, signal, onChunk=chunk, captureOutput=captureOutput,
            stdinData=stdinData, cap=cap, perStreamLimit=outputLimit is not None,
        )
    for index, decoder in enumerate(decoders):
        tail = decoder.finish()
        if tail:
            if captureOutput:
                decoded[index].append(tail)
            emit(index, tail)
    diagnostics = [f"{names[index]}: {note}" for index, decoder in enumerate(decoders) for note in decoder.diagnostics]
    diagnostics.extend(observer_errors)
    out, err = "".join(decoded[0]), "".join(decoded[1])
    if diagnostics:
        note = "\n[输出解码] " + "；".join(diagnostics)
        err += note
        emit(1, note)
    emit(0, "")
    emit(1, "")
    if capped and outputLimit is None:
        err += "\n[输出超过 10MB 上限被截断,请用更精确的命令或重定向到文件后再 Grep/Read]"
    return ForegroundResult(out, err, code, aborted, round((time.monotonic() - start) * 1000),
                            stdout, stderr, tuple(diagnostics), capped)


def run_foreground_plan(plan: "ShellExecutionPlan", signal: threading.Event, *, onOutput: OutputCallback | None = None,
                        onRawOutput: ChunkCallback | None = None, captureOutput: bool = True,
                        onLogOutput: OutputCallback | None = None) -> ForegroundResult:
    from .shell_plan import _words
    words = _words(plan.command) or []
    powershell = {"powershell", "powershell.exe", "pwsh", "pwsh.exe"}
    decode_clixml = bool(words and Path(words[0]).name.casefold() in powershell) or any(
        Path(wrapper.partition("\n")[0]).name.casefold() in powershell for wrapper in plan.analysis.wrappers)
    return run_foreground_argv(list(plan.argv), plan.cwd, signal, environ=dict(plan.environment),
                               commandLine=plan.commandLine, codec=plan.codec, onOutput=onOutput, decodeClixml=decode_clixml, onRawOutput=onRawOutput, captureOutput=captureOutput, onLogOutput=onLogOutput)
