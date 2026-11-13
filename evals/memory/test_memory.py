"""Frozen memory extraction, recall, injection A/B and report assertions."""

import asyncio
import json

import pytest

from evals.memory.extract import gradeExtraction
from evals.memory.injection_ab import gradeInjectionAB
from evals.memory.lib.creds import EvalConfig
from evals.memory.recall import gradeRecall
from evals.memory.report import formatReport

CFG = EvalConfig({}, 1, "offline")


def respond(**values):
    async def call(options):
        prompt = options["messages"][0]["content"]
        for key in ("covered", "relevant", "wouldRead", "durable"):
            if key in prompt:
                return json.dumps(values.get(key, {key: False}))
        raise AssertionError("unexpected judge rubric")
    return call


@pytest.mark.parametrize("present,profile,covered", [(True, True, True), (False, True, False), (True, False, True)])
def test_frozen_extract_coverage_and_empty_metrics(present, profile, covered):
    gold = {"mustExtract": [{"text": "用户给低龄孩子做游戏", "type": "user", "scope": "user", "profile": profile}],
            "mustNot": [], "existing": []}
    extracted = [{"title": "画像", "text": "用户给低龄孩子做游戏", "type": "user"}] if present else []
    call = respond(covered={"covered": covered}, durable={"durable": 1, "typeScopeCorrect": 1, "notCatalogDump": 1,
                                                         "actionable": 1})
    result = asyncio.run(gradeExtraction(extracted, gold, call, CFG))
    assert result["factRecall"] == int(covered)
    assert result["profileRecall"] == (int(covered) if profile else None)
    assert result["precision"] == (1 if present else None)
    assert result["quality"] == (1 if present else None)
    assert result["qualityStdev"] == (0 if present else None)
    assert result["typeScopeMatch"] == int(present)
    report = formatReport({"mode": "offline", "rows": [{"case": "fixture", "kind": "extract", "status": "scored", **result}]})
    assert "fixture" in report and "画像召回" in report and "type/scope" in report
    if not present or not profile:
        assert "N/A" in report


@pytest.mark.parametrize("stale", [False, True])
def test_frozen_recall_deterministic_gold_and_stale_leak(stale):
    gold = {"task": "做滑梯", "valueGold": ["a"] if stale else ["a", "b"],
            "relevanceGold": [] if stale else ["a", "b", "c"]}
    result = asyncio.run(gradeRecall(["a", "s1"] if stale else ["a", "b"], ["s1"] if stale else [],
                                    [(name, name) for name in ("a", "b", "c")], gold,
                                    respond(relevant={"relevant": not stale}), CFG))
    assert result["valuePR"]["r"] == 1
    assert result["staleLeak"] == int(stale)
    assert result["relevanceGapValue"] == pytest.approx(0 if stale else 1 / 3)
    assert result["judgeHumanAgreement"] == int(not stale)


@pytest.mark.parametrize(("names", "vote", "recall"), [
    (["标题a", "标题b"], True, 0), (["a", "b"], True, 1), (["a", "b"], False, 0),
])
def test_frozen_injection_ab_exact_candidate_identity(names, vote, recall):
    gold = {"task": "做滑梯", "valueGold": ["a", "b"]}
    score = asyncio.run(gradeInjectionAB(["a", "b"], names, gold, respond(wouldRead={"wouldRead": vote}), CFG))
    assert score["push"]["r"] == 1
    assert score["pull"]["r"] == recall
    assert score["delta"] == 1 - recall

def test_real_local_memory_and_cache_entrypoints(tmp_path):
    import sys
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from unittest.mock import patch

    from evals.memory.accept import main as accept
    from evals.memory.run import main as evaluate

    if sys.platform != "win32":
        pytest.skip("ordinary RuoCun controlled SQLite requires Windows")
    config = tmp_path / "config.json"
    requests = []
    key = "synthetic-memory-fixture-key"

    class LocalModel(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = request["messages"]
            last = messages[-1]["content"]
            requests.append(messages)
            hit = 0
            if "mergeInto" in last:
                if any("macOS" in row["content"] for row in messages[:-1] if isinstance(row["content"], str)):
                    memories = [{"title": "项目包管理器", "text": "项目固定用 pnpm 管理依赖。", "type": "semantic"}]
                else:
                    memories = [
                        {"title": f"长期画像 {key}", "text": "用户持续用 iPad 给低龄孩子制作游戏。", "type": "user"},
                        {"title": "方案偏好", "text": "用户偏好先看完整方案。为什么：确认后减少返工。怎么用：先给方案。",
                         "type": "feedback"},
                    ]
                answer = {"onTrack": True, "memories": memories}
            elif '"covered"' in last:
                answer = {"covered": "一次性目录信息" not in last.split("抽出记忆:")[0]}
            elif '"relevant"' in last:
                answer = {"relevant": "Postgres" not in last}
            elif '"wouldRead"' in last:
                answer = {"wouldRead": last.split("记忆标题:")[1].splitlines()[0] in {"a", "b"}}
            elif '"durable"' in last:
                answer = dict.fromkeys(("durable", "typeScopeCorrect", "notCatalogDump", "actionable"), 1)
            elif "包管理器" in last:
                answer = "pnpm" if any("项目固定用 pnpm" in row["content"] for row in messages
                                        if row["role"] == "system" and isinstance(row["content"], str)) else "未召回"
            else:
                answer = "合成模型回答"
                hit = 95 if "递归" in last else 50 if "闭包" in last else 0
            text = json.dumps(answer, ensure_ascii=False) if isinstance(answer, dict) else answer
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            frame = {"choices": [{"delta": {"content": text}, "finish_reason": "stop"}],
                     "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110,
                               "prompt_cache_hit_tokens": hit, "prompt_cache_miss_tokens": 100 - hit}}
            self.wfile.write(("data: " + json.dumps(frame) + "\n\ndata: [DONE]\n\n").encode())

    with ThreadingHTTPServer(("127.0.0.1", 0), LocalModel) as server:
        config.write_text(json.dumps({"version": 2, "activeProfile": "fixture", "profiles": {"fixture": {
            "provider": "zhipu", "model": "synthetic-memory", "key": key,
            "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
        }}}), encoding="utf-8")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def run(entry, mode):
            output = tmp_path / mode
            argv = ["memory", mode, "--config", str(config), "--output", str(output)]
            if entry is evaluate:
                argv += ["--judge-k", "1"]
            with patch("sys.argv", argv):
                code = entry()
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            assert code == 0, report
            assert report["mode"] == "offline"
            assert all(key not in path.read_text(encoding="utf-8") for path in output.iterdir())
            return report

        try:
            batch = run(evaluate, "both")
            extract, recall = batch["rows"]
            assert extract["factRecall"] == 1 and extract["profileRecall"] == 1 and extract["precision"] == 1
            assert extract["quality"] == 1 and extract["typeScopeMatch"] == 1
            assert recall["valuePR"]["r"] == 1 and recall["staleLeak"] == 0 and recall["judgeHumanAgreement"] == 1
            ab = run(evaluate, "injection-ab")["rows"][0]
            assert ab["push"]["r"] == ab["pull"]["r"] == 1
            memory = run(accept, "memory")
            assert memory["persistedCount"] == memory["reflectedAdded"] == memory["recallInjected"] == 1
            assert memory["answerMentionsPnpm"] and memory["visibleToolMarkers"] == 0
            cache = run(accept, "cache")
            assert [turn["ratio"] for turn in cache["turns"]] == [0, 0.5, 0.95]
            assert cache["warmIncreased"] and cache["warmTarget90"]
        finally:
            server.shutdown()
            thread.join(timeout=5)
    assert not any("synthetic-memory-fixture-key" in json.dumps(messages, ensure_ascii=False) for messages in requests)

def test_offline_cli_does_not_follow_model_redirect(tmp_path):
    import sys
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from evals.memory.accept import runAcceptance

    if sys.platform != "win32":
        pytest.skip("ordinary RuoCun controlled SQLite requires Windows")
    initial, forwarded = [], []

    class Observer(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return

        def do_GET(self):
            forwarded.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.end_headers()

        do_POST = do_GET

    class Redirect(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return

        def do_POST(self):
            initial.append(self.path)
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{target.server_port}/must-not-follow")
            self.end_headers()

    with ThreadingHTTPServer(("127.0.0.1", 0), Observer) as target, \
         ThreadingHTTPServer(("127.0.0.1", 0), Redirect) as first:
        workers = [threading.Thread(target=server.serve_forever, daemon=True) for server in (target, first)]
        for worker in workers:
            worker.start()
        try:
            profile = tmp_path / "config.json"
            profile.write_text(json.dumps({"apiKey": "synthetic-redirect-key",
                                           "baseUrl": f"http://127.0.0.1:{first.server_port}/v1"}), encoding="utf-8")
            result = runAcceptance("cache", profile, live=False)
        finally:
            for server in (target, first):
                server.shutdown()
            for worker in workers:
                worker.join(timeout=5)
    assert initial and not forwarded
    assert result["mode"] == "offline" and result["status"] != "measured"

def test_unknown_explicit_account_version_fails_before_agent(tmp_path, monkeypatch):
    from evals.memory import accept

    config = tmp_path / "future.json"
    config.write_text(json.dumps({"version": 3, "apiKey": "synthetic-version-key",
                                  "baseUrl": "http://127.0.0.1:1/v1"}), encoding="utf-8")

    def unexpected(*args, **kwargs):
        raise AssertionError("unsupported account version reached the ordinary Agent")

    monkeypatch.setattr(accept, "_run_agent", unexpected)
    result = accept.runAcceptance("cache", config, live=False)
    assert result["status"] == "environment_unavailable"
