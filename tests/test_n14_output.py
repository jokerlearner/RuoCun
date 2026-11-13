"""D10 minimal output adapter checks through actual foreground ports."""

import base64
import os
import sys
import threading
import time
from pathlib import Path

import pytest

from ruocun.platform.process_tree import run_foreground_argv
from ruocun.platform.shell_output import ShellOutputDecoder


def test_incremental_utf8_and_oem_selection_preserves_bytes():
    decoder = ShellOutputDecoder("auto:oem" if os.name == "nt" else "utf-8")
    text = "中文🙂\n".encode("utf-8")
    output = "".join(decoder.feed(bytes([value])) for value in text) + decoder.finish()
    assert output == "中文🙂\n"
    if os.name == "nt":
        decoder = ShellOutputDecoder("auto:oem")
        raw = "中文\n".encode("oem")
        assert decoder.feed(raw) + decoder.finish() == "中文\n"
        assert decoder.diagnostics
    decoder = ShellOutputDecoder("utf-8")
    assert decoder.feed(b"ok\xff") + decoder.finish() == "ok\\xff"
    assert decoder.diagnostics

    literal = b"#< CLIXML\n<Objs><S S='Error'>literal</S></Objs>"
    decoder = ShellOutputDecoder("utf-8")
    assert decoder.feed(literal) + decoder.finish() == literal.decode("utf-8")
    # Managed runner logs are unbounded on disk, so protocol display buffering must be bounded.
    decoder = ShellOutputDecoder("utf-8", clixml=True, clixmlLimit=16)
    assert decoder.feed(literal[:12]) == ""
    assert decoder.feed(literal[12:]) + decoder.finish() == literal.decode("utf-8")
    assert any("缓存上限" in note for note in decoder.diagnostics)


def test_native_argv_unicode_env_and_live_output_before_exit(tmp_path):
    script = tmp_path / "工作脚本.py"
    script.write_text(
        """import os,sys,time
print(sys.argv[1],flush=True)
print(os.environ['SYNTHETIC_VALUE'],flush=True)
assert 'OPENAI_API_KEY' not in os.environ
sys.stdout.buffer.write('中文🙂'.encode('utf-8')[:1]);sys.stdout.flush()
time.sleep(.1)
sys.stdout.buffer.write('中文🙂'.encode('utf-8')[1:]+b'\\n');sys.stdout.flush()
sys.stderr.buffer.write('错误中文'.encode('utf-8'));sys.stderr.flush()
time.sleep(.5)
""",
        encoding="utf-8",
    )
    chunks = []
    start = time.monotonic()

    def output(stream, text):
        chunks.append((stream, text, time.monotonic() - start))

    env = {
        **os.environ,
        "SYNTHETIC_VALUE": "合成环境 % ! ^ $",
        "OPENAI_API_KEY": "synthetic-must-be-removed",
    }
    result = run_foreground_argv(
        [sys.executable, "-I", str(script), "空格 \"双引号\" '单引号' % ! ^ $"],
        str(tmp_path),
        threading.Event(),
        environ=env,
        codec="auto:oem" if os.name == "nt" else "utf-8",
        onOutput=output,
    )
    assert (
        result.code == 0 and "中文🙂" in result.stdout and "错误中文" in result.stderr
    )
    assert "空格" in result.stdout and "合成环境 % ! ^ $" in result.stdout
    assert any(
        text and when < time.monotonic() - start - 0.35 for stream, text, when in chunks
    )
    assert result.stdoutRaw and result.stderrRaw
    assert chunks[-2][1] == chunks[-1][1] == ""


@pytest.mark.skipif(os.name != "nt", reason="PowerShell5.1 CLIXML adapter")
def test_explicit_powershell_error_is_readable(tmp_path):
    from ruocun.platform.process_tree import run_foreground

    script = "Write-Error '合成错误中文'"
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    engine = (
        Path(os.environ.get("SYSTEMROOT", r"C:\Windows"))
        / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    result = run_foreground(
        f'"{engine}" -NoProfile -NonInteractive -EncodedCommand {encoded}',
        str(tmp_path),
        threading.Event(),
    )
    assert "合成错误中文" in result.stderr
    assert "#< CLIXML" not in result.stderr
    assert result.stderrRaw


@pytest.mark.skipif(os.name != "nt", reason="Windows cmd batch/pipe adapter")
def test_cmd_batch_pipe_preserves_env_and_literal_arguments(tmp_path, monkeypatch):
    import asyncio
    import json

    from ruocun.config.compat import Compatibility
    from ruocun.permissions.runtime import createPermissionRuntime
    from ruocun.permissions.settings import emptyPermissions
    from ruocun.session.session import Session
    from ruocun.tools.exec_shell import execShellTool
    from ruocun.tools.types import ToolContext

    async def scenario():
        script = tmp_path / "中文 参数.py"
        script.write_text(
            "import os,sys,json\nfrom pathlib import Path\nPath(__file__).with_suffix('.json').write_text(json.dumps([sys.argv[1],os.environ['SYNTHETIC_VALUE']],ensure_ascii=False),encoding='utf-8')\nprint('cmd-ok')\n",
            encoding="utf-8",
        )
        batch = tmp_path / "中文 batch.cmd"
        batch.write_bytes(b'@echo off\r\n"%~1" -I "%~2" "%~3"\r\n')
        value = "合成环境 % ! ^ $"
        monkeypatch.setenv("SYNTHETIC_VALUE", value)

        async def ask(text):
            return "y"

        runtime = await createPermissionRuntime(
            tmp_path,
            tmp_path / "user",
            Compatibility(1, ()),
            Session("", "synthetic", env={}),
            emptyPermissions(),
            ask,
            interactive=True,
            env={"ProgramData": str(tmp_path / "program")},
        )
        findstr = (
            Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32/findstr.exe"
        )
        argument = "literal % ! ^ $"
        command = (
            f'"{batch}" "{sys.executable}" "{script}" "{argument}" | "{findstr}" cmd-ok'
        )
        assert await runtime.authorize(execShellTool, json.dumps({"command": command}))
        out = await execShellTool.handler(
            {"command": command},
            ToolContext(str(tmp_path), getShellPlan=runtime.getShellPlan),
        )
        assert "cmd-ok" in out and "[exit 0," in out
        assert json.loads(script.with_suffix(".json").read_text(encoding="utf-8")) == [
            argument,
            value,
        ]

    asyncio.run(scenario())
