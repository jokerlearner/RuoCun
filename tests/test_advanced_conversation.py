"""D09/StoragePort已确认输入不能因上下文投影丢失的必要接线确认。"""

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="已验证Windows存储端口")


def test_compact_projection_keeps_acknowledged_input_ledger_after_reopen(tmp_path):
    import ruocun

    code = r'''
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from ruocun.session.runtime import verify_controlled_runtime, verify_official_archive
from ruocun.session.conversation import Conversation
from ruocun.session.inputs import originalInput
from ruocun.session.session import Session
root = Path(sys.argv[1])
runtime = verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]), root / 'dll'))
async def scenario():
    session = Session('SYS', 'synthetic', env={})
    c = await Conversation.open(root / 'session', 'one', root, runtime, session, 'synthetic-key', resume=False)
    try:
        await c.accept_user(session, '已确认原始需求')
        first = (await c.worker.load_recovery_view()).checkpoint.accepted_inputs[0]
        projection = [{'role': 'system', 'content': 'SYS'}, {'role': 'system', 'content': '压缩摘要'}]
        await c.replace_context(session, projection)
        assert session.messages == projection
        assert (await c.worker.load_recovery_view()).checkpoint.accepted_inputs == (first,)
    finally:
        await c.close()
    restored = Session('SYS', 'synthetic', env={})
    c = await Conversation.open(root / 'session', 'one', root, runtime, restored, 'synthetic-key', resume=True)
    try:
        await c.accept_user(restored, '/synthetic-skill', model_content='第二次需求')
        assert restored.messages[-1]['content'] == '第二次需求'
        view = await c.worker.load_recovery_view()
        assert view.checkpoint.accepted_inputs[0] == first
        assert [a.seq for a in view.checkpoint.accepted_inputs] == [1, 2]
        assert json.loads(view.checkpoint.accepted_inputs[0].payload) == '已确认原始需求'
        assert json.loads(view.checkpoint.accepted_inputs[1].payload) == '/synthetic-skill'
        assert first.input_id != view.checkpoint.accepted_inputs[1].input_id
        before_rejected_input = (await c.worker.load_recovery_view()).checkpoint
        try:
            await c.queue_user(restored, '包含synthetic-key的待执行指令')
        except ValueError as error:
            assert '完整保存' in str(error)
        else:
            raise AssertionError('不能确认会被脱敏改写的排队输入')
        assert (await c.worker.load_recovery_view()).checkpoint == before_rejected_input
        # 复用同一必要保存/重开确认，覆盖N1排队账本与checkpoint的共享事务。
        one, _, two = await asyncio.gather(
            c.queue_user(restored, '相同文本'), c.save(restored),
            c.queue_user(restored, '相同文本'))
        assert one.input_id != two.input_id and (one.seq, two.seq) == (3, 4)
        assert [a.input_id for a in c.queued_inputs()] == [one.input_id, two.input_id]
        assert restored.messages[-1]['content'] == '第二次需求'
        projected = await c.queue_user(restored, '/queued-skill', model_content='已确认的技能正文快照')
        assert originalInput(projected.payload) == '/queued-skill'
        await c.set_foreground_state(restored, 'running')
    finally:
        await c.close()
    reopened = Session('SYS', 'synthetic', env={})
    c = await Conversation.open(root / 'session', 'one', root, runtime, reopened, 'synthetic-key', resume=True)
    try:
        assert c.foreground_state == 'paused'
        assert [a.input_id for a in c.queued_inputs()] == [one.input_id, two.input_id, projected.input_id]
        assert await c.consume_user(reopened, one.input_id)
        assert not await c.consume_user(reopened, one.input_id)
        assert reopened.messages[-1]['content'] == '相同文本'
        before = list(reopened.messages)
        assert not await c.consume_user(reopened, two.input_id, rejected=True)
        assert reopened.messages == before
        assert await c.consume_user(reopened, projected.input_id)
        assert reopened.messages[-1]['content'] == '已确认的技能正文快照'
        saved = (await c.worker.load_recovery_view()).checkpoint
        assert json.loads(saved.accepted_inputs[4].payload) == '/queued-skill'
        await c.queue_user(reopened, '暂停前排队')
        await c.discard_queued(reopened, state='paused')
        checkpoint = (await c.worker.load_recovery_view()).checkpoint
        assert checkpoint.background_state == 'paused'
        assert [item.state for item in checkpoint.accepted_inputs] == [
            'consumed', 'consumed', 'consumed', 'discarded', 'consumed', 'discarded']
        assert not c.queued_inputs()
    finally:
        await c.close()
asyncio.run(scenario())
'''
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code,
                             str(tmp_path), str(archive.resolve()), str(Path(ruocun.__file__).parent.parent)],
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
