"""Frozen tools/config.ts read, validation and native persistence semantics."""

import asyncio
import json

import pytest


def test_source_config_read_write_and_preserved_bad_native_file(tmp_path):
    from ruocun.platform.windows.durable_file import ensure_private_dir
    from ruocun.tools.config import makeConfigTool
    from ruocun.tools.schema import parseSchema
    from ruocun.tools.types import ToolContext, ToolRejected

    user = tmp_path / 'home' / '.ruocun'
    user.parent.mkdir()
    ensure_private_dir(user)
    workspace = tmp_path / 'workspace'
    (workspace / '.ruocun').mkdir(parents=True)
    project = workspace / '.ruocun/settings.json'
    native = user / 'settings.json'
    project.write_text('{"theme":"light","custom":{"zero":0,"null":null}}', encoding='utf-8')
    tool = makeConfigTool(user)
    ctx = ToolContext(str(workspace))

    async def scenario():
        assert tool.name == 'Config' and tool.shouldDefer and tool.capability == 'plan'
        with pytest.raises(ValueError):
            parseSchema(tool.schema, {'setting':'custom','value':{}})
        assert '已设置' in await tool.handler({'setting':'theme','value':'dark'},ctx)
        assert await tool.handler({'setting':'theme'},ctx) == 'light'
        assert await tool.handler({'setting':'custom.zero'},ctx) == '0'
        assert '已设置' in await tool.handler({'setting':'custom.null','value':False},ctx)
        assert await tool.handler({'setting':'custom.null'},ctx) == 'false'
        before = native.read_bytes()
        assert '无效值' in await tool.handler({'setting':'checkpoint.enabled','value':'true'},ctx)
        assert native.read_bytes() == before
        assert '已设置' in await tool.handler({'setting':'checkpoint.enabled','value':True},ctx)
        assert '已设置' in await tool.handler({'setting':'permissions.defaultMode','value':'plan'},ctx)
        assert json.loads(native.read_text())['permissions']['defaultMode'] == 'plan'
        document=json.loads(native.read_text())
        document['nullable']=None
        document['items']=['first']
        native.write_text(json.dumps(document),encoding='utf-8')
        assert await tool.handler({'setting':'nullable'},ctx) == 'null'
        assert await tool.handler({'setting':'items.0'},ctx) == 'first'
        assert not (workspace / '.ruocun/settings.local.json').exists()
        native.write_bytes(b'{synthetic-invalid-json')
        with pytest.raises(ToolRejected):
            await tool.handler({'setting':'theme','value':'dark'},ctx)
        assert native.read_bytes() == b'{synthetic-invalid-json'

    asyncio.run(scenario())
