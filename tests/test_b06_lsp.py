"""Frozen LSP config/manager and source operation semantics, D09 protocol boundary."""

import asyncio
import json
import sys
from pathlib import Path


def test_source_config_override_extension_and_manager_reuse(tmp_path):
    from ruocun.lsp.config import loadLspConfig, resolveServerForFile
    from ruocun.lsp.manager import LspManager

    first, second, broken = tmp_path / "first.json", tmp_path / "second.json", tmp_path / "broken.json"
    first.write_text(json.dumps({"servers": {"typescript": {"command": "user-ts", "extensions": [".ts", ".tsx"]}}}))
    second.write_text(json.dumps({"servers": {"typescript": {"command": sys.executable, "extensions": [".ts"]},
                                             "python": {"command": sys.executable, "extensions": [".py"]}}}))
    broken.write_text("{bad json")
    config = asyncio.run(loadLspConfig([first, broken, tmp_path / "missing.json", second]))
    assert config["servers"]["typescript"] == {"command": sys.executable, "extensions": [".ts"]}
    assert resolveServerForFile(config, "FOO.TS")["name"] == "typescript"
    assert resolveServerForFile(config, "main.go") is None
    manager = LspManager(config, tmp_path.as_uri(), environ={})
    assert "error" in manager.resolve("main.go")
    assert manager.resolve("a.ts")["client"] is manager.resolve("b.ts")["client"]
    assert manager.resolve("a.ts")["client"] is not manager.resolve("a.py")["client"]
    asyncio.run(manager.disposeAll())


def test_existing_d15_protocol_utf16_sync_cancel_and_owned_shutdown(tmp_path):
    from ruocun.lsp.client import LspClient, fileUriToPath, pathToFileUri

    async def scenario():
        file = tmp_path / "中文 space.py"
        file.write_text("A😀中x", encoding="utf-8")
        trace = tmp_path / "wire.jsonl"
        fixture = Path(__file__).parent / "support/lsp_server.py"
        client = LspClient(sys.executable, [str(fixture.resolve()), str(trace)], tmp_path.as_uri(), request_timeout=1)
        try:
            output = await client.definition(str(file), 1, 5)
            assert output == f"{file}:1:5"
            assert fileUriToPath(pathToFileUri(file)) == str(file)
            first, second = await asyncio.gather(client.request("d15/echo", {"value": "先发中文"}),
                                                  client.request("d15/echo", {"value": "后发😀"}))
            assert [first, second] == ["先发中文", "后发😀"]
            file.write_text("\nA😀中x", encoding="utf-8")
            await client.definition(str(file), 2, 5)
            try:
                await client.request("d15/never", {}, timeout=.05)
            except TimeoutError:
                pass
            else:
                raise AssertionError("request did not time out")
        finally:
            await client.dispose()
        assert client.pid is not None and client.returncode == 0
        rows = [json.loads(line) for line in trace.read_text("utf-8").splitlines()]
        assert [row["params"]["textDocument"]["version"] for row in rows
                if row.get("method") in {"textDocument/didOpen", "textDocument/didChange"}] == [1, 2]
        assert next(row["params"]["position"] for row in rows if row.get("method") == "textDocument/definition") == {"line": 0, "character": 4}
        assert any(row.get("method") == "$/cancelRequest" for row in rows)
        methods = [row["method"] for row in rows if "method" in row]
        assert methods[-2:] == ["shutdown", "exit"] and rows[-1] == {"stopped": "exit"}
    asyncio.run(scenario())
