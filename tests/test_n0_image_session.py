"""冻结 execute/loop 图片投递及 D09 完整ToolMessage 的必要持久化确认。"""

import asyncio
import copy
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import ruocun
from ruocun.session.contract import Intent, RunRef, ToolRef
from ruocun.session.messages import flushReadImages
from ruocun.session.storage_worker import StorageWorker


def test_flush_groups_current_history_images_and_marks_only_candidate_projection():
    history = [
        {"role": "system", "content": "SYS"},
        {"role": "tool", "tool_call_id": "one", "content": "图一",
         "imageData": {"base64": "U1lOVEg=", "mediaType": "image/png"}},
        {"role": "tool", "tool_call_id": "two", "content": "图二",
         "imageData": {"base64": "U1lOVEgy", "mediaType": "image/jpeg"}},
    ]
    original = copy.deepcopy(history)
    candidate = flushReadImages(history)
    assert history == original
    assert candidate[-1] == {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,U1lOVEg="}},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,U1lOVEgy"}},
        {"type": "text", "text": "[以上图片由 Read 工具读取,请基于图片内容回答用户的问题]"},
    ]}
    assert candidate[1]["imageDelivered"] is True and candidate[2]["imageDelivered"] is True
    assert flushReadImages(candidate) == candidate


def test_worker_snapshots_mutable_result_and_does_not_return_port_owned_dictionary():
    ready = threading.Event()

    class Port:
        saved = None

        def commit_result_and_event(self, owner, ref, result, run, event):
            self.saved = result

        def commit_intent(self, owner, intent):
            return self.saved

        def close(self, owner):
            pass

    port = Port()

    def factory():
        assert ready.wait(5)
        return port, object()

    async def scenario():
        worker = StorageWorker(factory)
        message = {"role": "tool", "tool_call_id": "image", "content": "读图",
                   "imageData": {"base64": "U1lOVA==", "mediaType": "image/png"}}
        try:
            handle = worker.enqueue_result_and_event(ToolRef("main", "image"), message, None, None)
            message["imageData"]["base64"] = "MUTATED"
            ready.set()
            await handle.wait()
            assert port.saved["imageData"]["base64"] == "U1lOVA=="
            intent = Intent(ToolRef("main", "image"), RunRef("main", "foreground"), "Read", "{}",
                            "synthetic-digest", False, "read-only", "synthetic", 0, "synthetic-time")
            reused = await worker.enqueue_intent(intent).wait()
            reused["imageData"]["base64"] = "CALLER-MUTATED"
            assert port.saved["imageData"]["base64"] == "U1lOVA=="
        finally:
            ready.set()
            await worker.close()
    asyncio.run(scenario())


@pytest.mark.skipif(sys.platform != "win32", reason="真实Windows Conversation/SQLite端口")
def test_complete_image_result_reopens_once_and_compressed_history_does_not_reinject_old_records(tmp_path):
    # 复用 test_advanced_conversation.py 的真实受控SQLite reopen入口。
    code = r'''
import asyncio, copy, sys
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from ruocun.session.conversation import Conversation
from ruocun.session.contract import StoreError, ToolRef
from ruocun.session.runtime import verify_controlled_runtime, verify_official_archive
from ruocun.session.session import Session
root = Path(sys.argv[1])
runtime = verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]), root / 'dll'))
image = {'base64': 'U1lOVEg=', 'mediaType': 'image/png'}
secret = image['base64']  # 复用独审捕获的同一图片碰巧包含凭据字节的最小复现。
def call(key):
    return {'id': key, 'type': 'function', 'function': {'name': 'Read', 'arguments': '{}'}}
def count_images(session):
    return sum(m.get('role') == 'user' and isinstance(m.get('content'), list)
               and any(p.get('type') == 'image_url' and p.get('image_url', {}).get('url', '').startswith('data:image/')
                       for p in m['content']) for m in session.messages)
async def scenario():
    session = Session('SYS', 'synthetic', env={})
    c = await Conversation.open(root / 'session', 'one', root, runtime, session, secret, resume=False)
    try:
        await c.accept_user(session, [
            {'type': 'text', 'text': '已确认的看图请求，凭据=' + secret, 'base64': secret},
            {'type': 'image_url', 'image_url': {'url': 'https://synthetic.invalid/' + secret}},
        ])
        session.messages.append({'role': 'assistant', 'content': None,
                                 'tool_calls': [call('paired'), call('missing'), call('plain')]})
        await c.save(session)
        await c.intent('paired', 'Read', '{}', False)
        for invalid in [
            {'role': 'tool', 'tool_call_id': 'other', 'content': 'wrong identity', 'imageData': image},
            {'role': 'tool', 'tool_call_id': 'paired', 'content': 'wrong image shape',
             'imageData': {'base64': 7, 'mediaType': 'image/png'}},
        ]:
            try:
                await c.worker.enqueue_result_and_event(ToolRef('main', 'paired'), invalid, None, None).wait()
            except StoreError:
                pass
            else:
                raise AssertionError('malformed tool message must be rejected before committing')
        await c.result('paired', '第一张图，凭据=' + secret, image)
        session.messages.append({'role': 'tool', 'tool_call_id': 'paired', 'content': '第一张图，凭据=' + secret, 'imageData': image})
        await c.save(session)
        await c.intent('missing', 'Read', '{}', False)
        await c.result('missing', '第二张图', image)
        await c.intent('plain', 'Read', '{}', False)
        await c.result('plain', '普通文本')
    finally:
        await c.close()
    restored = Session('SYS', 'synthetic', env={})
    c = await Conversation.open(root / 'session', 'one', root, runtime, restored, secret, resume=True)
    try:
        assert count_images(restored) == 1
        tools = {m['tool_call_id']: m for m in restored.messages if m['role'] == 'tool'}
        assert tools['paired']['imageData'] == tools['missing']['imageData'] == image
        assert tools['paired']['imageDelivered'] is tools['missing']['imageDelivered'] is True
        assert tools['plain']['content'] == '普通文本'
        view = await c.worker.load_recovery_view()
        records = {r.tool_ref.tool_call_id: r for r in view.tool_records}
        assert records['plain'].result == '普通文本'
        assert records['paired'].result['imageData'] == image
        assert records['paired'].result['content'] == '第一张图，凭据=[REDACTED]'
        assert 'imageDelivered' not in records['paired'].result
        assert restored.messages[1]['content'][0]['base64'] == '[REDACTED]'
        assert secret not in restored.messages[1]['content'][0]['text']
        assert restored.messages[1]['content'][1]['image_url']['url'] == 'https://synthetic.invalid/[REDACTED]'
        assert restored.messages[-1]['content'][0]['image_url']['url'] == 'data:image/png;base64,' + image['base64']
        assert list(view.checkpoint.messages) == restored.messages
        reused = await c.intent('paired', 'Read', '{}', False)
        reused['imageData']['base64'] = 'CALLER-MUTATED'
        assert (await c.intent('paired', 'Read', '{}', False))['imageData'] == image
        restored.lastPromptTokens, restored.lastSentLength = 1234, 7
        await c.replace_context(restored, restored.messages, reset_prompt=False)
        assert (restored.lastPromptTokens, restored.lastSentLength) == (1234, 7)
    finally:
        await c.close()
    c = await Conversation.open(root / 'session', 'one', root, runtime, restored, secret, resume=True)
    try:
        assert count_images(restored) == 1  # 标记与图片在同一checkpoint，重开不再投递。
        await c.replace_context(restored, [{'role': 'system', 'content': 'SYS'},
                                           {'role': 'system', 'content': '压缩后的摘要'}])
        assert restored.lastPromptTokens is None and restored.lastSentLength == 0
    finally:
        await c.close()
    c = await Conversation.open(root / 'session', 'one', root, runtime, restored, secret, resume=True)
    try:
        assert count_images(restored) == 0
        assert restored.messages == [{'role': 'system', 'content': 'SYS'}, {'role': 'system', 'content': '压缩后的摘要'}]
        assert len((await c.worker.load_recovery_view()).checkpoint.accepted_inputs) == 1
    finally:
        await c.close()
asyncio.run(scenario())
'''
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    # 开发源定向/最终wheel验证均让子进程消费父进程实际载入的同一包。
    source = Path(ruocun.__file__).resolve().parent.parent
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code,
                             str(tmp_path), str(archive.resolve()), str(source)],
                            capture_output=True, text=True, encoding="utf-8", timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr
