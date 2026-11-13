"""Frozen TaskCreate/List/Get/Update/Stop cases through the durable task manager."""

import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

_MANUAL = r'''
import asyncio,re,sys
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.agent.background_runtime import BackgroundRuntime
from ruocun.agent.tasks import TaskManager
from ruocun.session.conversation import Conversation
from ruocun.session.recovery import RecoveryController
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.session import Session
from ruocun.tools.task_create import taskCreateTool
from ruocun.tools.task_get import taskGetTool
from ruocun.tools.task_list import taskListTool
from ruocun.tools.task_output import taskOutputTool
from ruocun.tools.task_stop import taskStopTool
from ruocun.tools.task_update import taskUpdateTool
from ruocun.tools.types import ToolContext

root=Path(sys.argv[1]);runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))

async def scenario():
    ctx=ToolContext(str(root))
    async def open_owner(resume):
        session=Session('synthetic','synthetic',env={})
        store=await Conversation.open(root/'session','n45',root,runtime,session,'synthetic-key',resume=resume)
        background=BackgroundRuntime(store=store,workspaceRoot=root)
        await RecoveryController(store,session,background).recover()
        ctx.taskManager=TaskManager(store,background)
        await ctx.taskManager.bind()
        return store,background

    async def create(text):
        out=await taskCreateTool.handler({'description':text},ctx)
        match=re.fullmatch(r'已创建任务 (task-\d+):'+re.escape(text),out)
        assert match,out
        return match[1]

    async def get(id):
        return await taskGetTool.handler({'id':id},ctx)

    assert '不支持任务追踪' in await taskCreateTool.handler({'description':'x'},ctx)
    store,background=await open_owner(False)
    try:
        assert '暂无运行中的任务' in await taskListTool.handler({},ctx)
        a,b=await create('任务A'),await create('任务B')
        assert a!=b and '状态: running' in await get(b)
        assert '未找到任务' in await get('task-999')
        assert '未找到任务' in await taskUpdateTool.handler({'id':'task-999','status':'completed'},ctx)
        assert '已更新' in await taskUpdateTool.handler({'id':a,'status':'completed','result':'结论X'},ctx)
        detail=await get(a)
        assert all(value in detail for value in ('状态: completed','开始:','结束:','结论X'))
        assert '已结束' in await taskUpdateTool.handler({'id':a,'status':'failed','description':'任务A改'},ctx)
        assert '状态: completed' in await get(a) and '任务A改' in await get(a)
        running=await taskListTool.handler({},ctx)
        assert '任务B' in running and '任务A' not in running
        assert '任务A改' in await taskListTool.handler({'include_finished':True},ctx)
        assert 'TaskGet' in await taskOutputTool.handler({'id':b},ctx)
        assert '已取消' in await taskStopTool.handler({'id':b},ctx)
        assert '未生效' in await taskStopTool.handler({'id':b},ctx)
        c=await create('任务C')
        assert not background.events() and not background.running()
    finally:
        await store.close()  # Release owner without TaskManager's normal-exit cleanup.

    store,background=await open_owner(True)
    try:
        assert '结论X' in await get(a) and '任务A改' in await get(a)
        assert '状态: canceled' in await get(b) and '状态: running' in await get(c)
        d=await create('任务D')
        assert len({a,b,c,d})==4
        await ctx.taskManager.close()
        assert not background.events() and not background.running()
    finally:
        await store.close()

    store,background=await open_owner(True)
    try:
        assert '状态: canceled' in await get(c) and '状态: canceled' in await get(d)
        assert '暂无运行中的任务' in await taskListTool.handler({},ctx)
    finally:
        await store.close()

asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="uses controlled Windows SQLite")
def test_source_manual_tools_round_trip_and_normal_close(tmp_path):
    source = Path(ruocun.__file__).resolve().parents[1]
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", _MANUAL,
                             str(tmp_path), str(archive.resolve()), str(source)],
                            capture_output=True, text=True, encoding="utf-8", timeout=35)
    assert result.returncode == 0, result.stderr + result.stdout
