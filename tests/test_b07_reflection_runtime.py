"""Necessary seam: asynchronous analysis cannot write or inject into an open tool pair."""

import asyncio
import copy

import pytest


def test_background_reflection_stages_then_drains_once_and_reuses_acknowledgement():
    from ruocun.agent.reflection_runtime import ReflectionRuntime
    from ruocun.session.session import Session

    async def scenario():
        class Conversation:
            reflection_state = None
            blocked = False
            def __init__(self):
                self.agent_tool_batches = asyncio.Lock()
                self.journal = {}
            async def set_reflection_state(self, session, state, *, advisories=()):
                assert not session.messages[-1].get('tool_calls')
                self.reflection_state = copy.deepcopy(state)
                session.messages.extend({'role':'system','content':text} for text in advisories)
            async def scoped_intent(self, ref, name, args, effect, **kwargs):
                if ref in self.journal:
                    value = self.journal[ref]
                    assert value is not None, 'unknown writes must not be replayed'
                    return value
                self.journal[ref] = None
            async def scoped_result(self, ref, text):
                self.journal[ref] = text
        session=Session('SYS','synthetic',env={})
        session.messages.append({'role':'user','content':'synthetic task'})
        session.lastSentLength=2
        conversation=Conversation()
        calls, writes, audits=[], [], []
        gate=asyncio.Event()
        async def analyze(messages):
            calls.append(messages)
            await gate.wait()
            return {'onTrack':False,'advisory':'synthetic advice','memories':[], 'corrections':[], 'confirmed':[]}
        async def apply(result):
            assert conversation.agent_tool_batches.locked()
            writes.append(result)
            return {'added':0,'merged':0,'corrections':[], 'confirmed':0}
        def runtime(enabled=True):
            return ReflectionRuntime(conversation,session,enabled=enabled,analyze=analyze,apply=apply,
                                     audit=audits.append,notice=lambda text:None,env={})
        off=runtime(False)
        await off.after_turn('disabled',provider='other')
        assert conversation.reflection_state is None and not calls
        current=runtime()
        await current.after_turn('stable-one',provider='other')
        await asyncio.sleep(0)
        session.messages.append({'role':'assistant','tool_calls':[{'id':'open'}]})
        gate.set()
        await asyncio.wait({current.task})
        assert not writes and not any(m.get('content')=='[反思]\nsynthetic advice' for m in session.messages)
        session.messages.append({'role':'tool','tool_call_id':'open','content':'paired'})
        await current.drain()
        assert len(writes)==1 and calls[0]==session.messages[:2]
        assert session.messages[-1]['content']=='[反思]\nsynthetic advice'
        await current.after_turn('stable-one',provider='other')
        assert len(writes)==1 and len(calls)==1
        # Simulate acknowledged files but old ready checkpoint: journal result wins.
        result=writes[0]
        conversation.reflection_state={'id':'stable-one','phase':'ready','result':result,
                                       'cadence':{'interval':1,'counter':0}}
        await runtime().drain()
        assert len(writes)==1
        async def unknown(result):
            writes.append(result)
            raise RuntimeError('synthetic write acknowledgement lost')
        failing=runtime()
        failing.apply=unknown
        conversation.reflection_state={'id':'stable-two','phase':'ready','result':result}
        with pytest.raises(RuntimeError):
            await failing.drain()
        assert conversation.blocked
        await failing.after_turn('bypass-attempt',provider='other')
        assert len(writes)==2 and len(calls)==1
    asyncio.run(scenario())
