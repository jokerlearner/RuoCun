"""WIRE-03: Chat SSE 分帧与按增量字节严格解码 UTF-8。

预期独立来源：
- 冻结 src/client/sse.ts:1-20 及 .test.ts:4-38（字符串分帧断言）
- 冻结 src/client/client.ts:313-335（TextDecoder 增量解码 + 末帧 flush）
- D09:95「按增量字节严格解码 UTF-8，中文/emoji 跨字节分片、CR/LF、多帧、
  空行与 [DONE]；来源 data.toString() 的 Unicode/65536 缓冲瑕疵不复制为正确预期」
- 任务票 WIRE-03「文本/reasoning/工具调用参数按 index 完整累积」（累积器在组4）
"""

from __future__ import annotations

import json

import pytest

from ruocun.client import sse

# ---------------------------------------------------------------------------
# 冻结 sse.test.ts 字符串分帧断言（S 类：直接改写）
# ---------------------------------------------------------------------------


def test_single_complete_data_payload():
    r = sse.parseSSEChunk('data: {"a":1}\n\n')
    assert r.payloads == ['{"a":1}']
    assert r.rest == ""


def test_multiple_events_in_one_chunk():
    r = sse.parseSSEChunk('data: {"a":1}\n\ndata: {"b":2}\n\n')
    assert r.payloads == ['{"a":1}', '{"b":2}']
    assert r.rest == ""


def test_keeps_incomplete_trailing_event_in_rest():
    r = sse.parseSSEChunk('data: {"a":1}\n\ndata: {"b"')
    assert r.payloads == ['{"a":1}']
    assert r.rest == 'data: {"b"'


def test_done_sentinel_is_a_payload():
    assert sse.parseSSEChunk("data: [DONE]\n\n").payloads == ["[DONE]"]


def test_ignores_non_data_lines_comments_and_empty():
    r = sse.parseSSEChunk(': keep-alive\n\ndata: {"a":1}\n\n')
    assert r.payloads == ['{"a":1}']


def test_crlf_line_endings_normalized():
    r = sse.parseSSEChunk('data: {"a":1}\r\n\r\ndata: [DONE]\r\n\r\n')
    assert r.payloads == ['{"a":1}', "[DONE]"]
    assert r.rest == ""


def test_data_prefix_trim_and_multiline_event():
    r = sse.parseSSEChunk('data:   {"a":1}  \n\ndata: [DONE]\n\n')
    assert r.payloads == ['{"a":1}', "[DONE]"]


# ---------------------------------------------------------------------------
# 增量 UTF-8 严格解码（本票产品修复，不复制来源瑕疵）
# ---------------------------------------------------------------------------


def _content_frame(text: str) -> str:
    return "data: " + json.dumps(
        {"choices": [{"delta": {"content": text}}]}, ensure_ascii=False) + "\n\n"


def test_utf8_multibyte_split_at_every_byte_boundary():
    # 逐字节喂入：中文 3 字节、emoji 4 字节被切碎，增量解码器必须完整还原。
    text = "中文回答😀与 emoji 混合"
    raw = _content_frame(text).encode("utf-8")
    parser = sse.SSEStreamParser()
    out: list[str] = []
    for i in range(len(raw)):
        out.extend(parser.feed(raw[i:i + 1]))
    out.extend(parser.flush())
    body = json.dumps(
        {"choices": [{"delta": {"content": text}}]}, ensure_ascii=False)
    assert out == [body]


def test_utf8_split_across_chunk_sizes_and_multiple_frames():
    text = "中文😀"
    body1 = json.dumps(
        {"choices": [{"delta": {"content": text}}]}, ensure_ascii=False)
    body2 = json.dumps(
        {"choices": [], "usage": {"prompt_tokens": 1, "completion_tokens": 1,
                                  "total_tokens": 2}}, ensure_ascii=False)
    stream = (
        "data: " + body1 + "\r\n\r\n"
        "data: " + body2 + "\n\n"
        "data: [DONE]\n\n"
    ).encode("utf-8")
    for chunk_size in (2, 3, 5, 7, 11):
        parser = sse.SSEStreamParser()
        out: list[str] = []
        for i in range(0, len(stream), chunk_size):
            out.extend(parser.feed(stream[i:i + chunk_size]))
        out.extend(parser.flush())
        assert out == [body1, body2, "[DONE]"], f"chunk_size={chunk_size}"


def test_crlf_split_across_chunk_boundary():
    # \r 在块末、\n 在下一块：归一后仍能正确分帧。
    raw = b'data: {"a":1}\r\n\r\ndata: [DONE]\r\n\r\n'
    parser = sse.SSEStreamParser()
    out: list[str] = []
    for i in range(len(raw)):
        out.extend(parser.feed(raw[i:i + 1]))
    out.extend(parser.flush())
    assert out == ['{"a":1}', "[DONE]"]


def test_flush_handles_final_event_without_terminator():
    # 冻结 client.ts:330-335 流末 flush：未以 \n\n 收尾的最后一个事件。
    parser = sse.SSEStreamParser()
    assert parser.feed(b'data: {"a":1}') == []
    assert parser.flush() == ['{"a":1}']


def test_flush_on_clean_stream_adds_nothing():
    parser = sse.SSEStreamParser()
    assert parser.feed(b'data: [DONE]\n\n') == ["[DONE]"]
    assert parser.flush() == []


def test_invalid_utf8_raises_not_silently_replaced():
    # 严格解码：非法字节明确失败，不伪报成功、不用 replacement char 吞掉。
    parser = sse.SSEStreamParser()
    with pytest.raises(UnicodeDecodeError):
        parser.feed(b"data: \xff\xfe bad\n\n")


def test_incomplete_multibyte_at_end_then_flush_is_strict_error():
    # 流结束时仍是不完整多字节序列 → 严格模式报错，不产生半个字符。
    parser = sse.SSEStreamParser()
    parser.feed(b"data: \xe4\xb8")  # 中文三字节只来了两字节
    with pytest.raises(UnicodeDecodeError):
        parser.flush()
