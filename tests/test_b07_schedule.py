"""Frozen schedule.ts line construction and the approved W3 Windows boundary."""

from __future__ import annotations

import asyncio
import sys
import threading

import pytest


def test_source_cron_line_quotes_workspace_launcher_prompt_and_mark():
    from ruocun.schedule import buildCronLine

    line = buildCronLine("0 9 * * *", "检查 PR", "/proj/x", "/usr/bin/ruocun")
    assert line.startswith("0 9 * * * ") and "cd '/proj/x'" in line
    assert "'/usr/bin/ruocun' '检查 PR'" in line
    assert '"$HOME/.ruocun/schedule.log"' in line and "# ruocun-schedule" in line
    assert "'it'\\''s a test'" in buildCronLine("* * * * *", "it's a test", "/a", "/ruocun")


def test_synthetic_posix_routes_preserve_other_jobs_and_prewrite_read_failure():
    from ruocun.schedule import CommandResult, scheduleAdd, scheduleList, scheduleRemove
    from ruocun.tools.types import ToolRejected

    async def scenario():
        table, calls, output = ["0 1 * * * unrelated", "# dao-schedule old reference remains"], [], []
        broken = False
        async def run(argv, stdin, **kwargs):
            calls.append((list(argv), stdin))
            if argv == ("crontab", "-l"):
                return CommandResult(2, "", "synthetic read failure") if broken else CommandResult(0, "\n".join(table))
            assert argv == ("crontab", "-")
            table[:] = stdin.rstrip("\n").split("\n")
            return CommandResult(0, "")
        options = {"platform": "linux", "runner": run}
        assert await scheduleAdd("0 9 * * *", "检查 PR", "/proj/x", "/venv/bin/python", output.append,
                                 launcherArgs=("-m", "ruocun"), **options)
        assert len(table) == 3 and "'/venv/bin/python' '-m' 'ruocun' '检查 PR'" in table[-1]
        assert await scheduleList(output.append, **options) and "1." in output[-1]
        assert await scheduleRemove(1, output.append, **options)
        assert table == ["0 1 * * * unrelated", "# dao-schedule old reference remains"]
        assert not await scheduleRemove(1, output.append, **options)
        broken = True
        before = list(table)
        with pytest.raises(ToolRejected, match="未写入"):
            await scheduleAdd("* * * * *", "preserve", "/p", "/python", output.append, **options)
        assert table == before and calls[-1][0] == ["crontab", "-l"]
    asyncio.run(scenario())


def test_source_tool_preconditions_and_windows_refusal_never_call_backend():
    from ruocun.schedule import ScheduleService
    from ruocun.tools.schedule_tool import createScheduleTools
    from ruocun.tools.types import ToolContext

    async def scenario():
        async def forbidden(*args, **kwargs):
            raise AssertionError("Windows system scheduler must not start a backend")
        tools = createScheduleTools(ScheduleService(platform="win32", runner=forbidden))
        schedule, create, delete, listed = tools
        ctx = ToolContext("synthetic")
        assert schedule.capability == "exec" and schedule.approval == "required"
        assert "需要 cron" in await schedule.handler({"action": "add"}, ctx)
        assert "需要 index" in await schedule.handler({"action": "remove"}, ctx)
        for tool, arguments in ((schedule, {"action": "add", "cron": "* * * * *", "prompt": "x"}),
                                (schedule, {"action": "list"}), (schedule, {"action": "remove", "index": 1}),
                                (create, {"cron": "* * * * *", "prompt": "x"}), (delete, {"jobId": 1}), (listed, {})):
            result = await tool.handler(arguments, ctx)
            assert result.startswith("Error:") and "Windows" in result and "不支持" in result
        assert listed.capability == "read" and listed.approval == "auto" and all(tool.shouldDefer for tool in tools)
        assert "session-only" in await create.handler({"cron": "* * * * *", "prompt": "x", "durable": False}, ctx)
    asyncio.run(scenario())


@pytest.mark.skipif(sys.platform != "win32", reason="independent Windows process HANDLE confirmation")
def test_actual_synthetic_write_cancel_stops_owned_command_and_remains_unknown(tmp_path):
    import _winapi

    from ruocun.schedule import runScheduleCommand
    from ruocun.tools.tool_batch import UnknownToolOutcome

    async def scenario():
        pid_file, effect = tmp_path / "pid", tmp_path / "effect"
        program = ("import os,sys,time;from pathlib import Path;sys.stdin.read();"
                   f"Path({str(effect)!r}).write_text('once');Path({str(pid_file)!r}).write_text(str(os.getpid()));time.sleep(60)")
        signal = threading.Event()
        work = asyncio.create_task(runScheduleCommand((sys._base_executable, "-I", "-c", program), "synthetic crontab", environ={}, signal=signal))
        handle = None
        try:
            async with asyncio.timeout(3):
                while not pid_file.exists():
                    await asyncio.sleep(.01)
            handle = _winapi.OpenProcess(0x100000, False, int(pid_file.read_text()))
            assert _winapi.WaitForSingleObject(handle, 0) == _winapi.WAIT_TIMEOUT
            signal.set()
            with pytest.raises(UnknownToolOutcome, match="未自动重放"):
                await asyncio.wait_for(work, 3)
            assert effect.read_text() == "once"
            assert _winapi.WaitForSingleObject(handle, 0) == _winapi.WAIT_OBJECT_0
        finally:
            signal.set()
            await asyncio.gather(work, return_exceptions=True)
            if handle is not None:
                _winapi.CloseHandle(handle)
    asyncio.run(scenario())
