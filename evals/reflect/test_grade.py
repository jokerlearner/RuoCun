"""Frozen grade.test.ts behavioral assertions and six source fixture controls."""

import asyncio

import pytest

from evals.memory.lib.creds import EvalConfig
from evals.reflect.grade import gradeReflect


@pytest.mark.parametrize(("actual", "advisory", "expected", "judge", "match", "on_point"), [
    (False, "核实后再回答", False, True, True, 1),
    (True, None, False, True, False, 0),
    (False, "改动文件太多", False, False, True, 0),
    (True, None, True, True, True, None),
    (False, "错误报警", True, True, False, None),
])
def test_frozen_grade_contract(actual, advisory, expected, judge, match, on_point):
    async def fake(_options):
        return '{"onPoint":true}' if judge else '{"onPoint":false}'

    gold = {"expectOnTrack": expected, "expectFlag": "未核实断言"}
    result = asyncio.run(gradeReflect(actual, advisory, gold, fake, EvalConfig({}, 1, "offline")))
    assert result["onTrackMatch"] is match
    assert result["advisoryOnPoint"] == on_point

def test_frozen_fixtures_run_through_local_cli(tmp_path):
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from evals.reflect.run import FIXTURES, main

    responses = iter([
        '{"onTrack":false,"advisory":"核实代码再答 synthetic-reflect-key","memories":[]}', '{"onPoint":true}',
        '{"onTrack":true}', '{"onTrack":false,"diagnostic":NaN}', '{"onTrack":true}',
        '{"onTrack":false,"advisory":"误报"}', '{"onTrack":true}',
    ])
    calls = []

    class LocalModel(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return

        def do_POST(self):
            calls.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            content = next(responses)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            frame = {"choices": [{"delta": {"content": content}, "finish_reason": "stop"}]}
            self.wfile.write(("data: " + json.dumps(frame) + "\n\ndata: [DONE]\n\n").encode())

    config, output = tmp_path / "config.json", tmp_path / "output"
    with ThreadingHTTPServer(("127.0.0.1", 0), LocalModel) as server:
        config.write_text(json.dumps({"apiKey": "synthetic-reflect-key",
                                      "baseUrl": f"http://127.0.0.1:{server.server_port}/v1"}), encoding="utf-8")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            from unittest.mock import patch

            argv = ["reflect", "--fixtures", str(FIXTURES), "--config", str(config),
                    "--output", str(output), "--judge-k", "1"]
            with patch("sys.argv", argv):
                assert main() == 1
        finally:
            server.shutdown()
            thread.join(timeout=5)
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["mode"] == "offline"
    assert [row["status"] for row in report["rows"]] == ["passed", "failed", "invalid", "passed", "failed", "passed"]
    assert report["alarmPR"] == {"p": 0.5, "r": 0.5, "f1": 0.5}
    assert len(calls) == 7 and "onPoint" in calls[1]["messages"][0]["content"]
    assert "synthetic-reflect-key" not in calls[1]["messages"][0]["content"]
    assert report["rows"][0]["advisory"] == "核实代码再答 [REDACTED]"
    assert not any("synthetic-reflect-key" in path.read_text(encoding="utf-8") for path in output.iterdir())
