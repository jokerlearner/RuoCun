"""D06单reader协议适配的产品迁移；CPR仅交还正在等待回包的ptk。"""
from __future__ import annotations

import asyncio
import codecs
import re
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any

from prompt_toolkit.input import Input

from .input_text import normalizeSurrogates

START, END = "\x1b[200~", "\x1b[201~"
PASTE_LIMIT_BYTES = 8 * 1024 * 1024


class Reports:
    def __init__(self, emit: Callable[..., None], *, cpr_pending: Callable[[], bool] = lambda: False) -> None:
        self.emit = emit
        self.cpr_pending = cpr_pending
        self.decoder = codecs.getincrementaldecoder("utf-8")("strict")
        self.pending = ""
        self.paste = False
        self._paste_parts: list[str] = []
        self._paste_bytes = 0
        self._paste_rejected = False
        self.since = 0.0
        self.kind: str | None = None
        self.deadline = 0.0
        self.grace = 0.0
        self.attributes: list[int] | None = None
        self.cell: dict[str, int] | None = None
        self.result: dict[str, int] | None = None
        self.outcome = "not-requested"
        self.disposed = False

    def begin(self, kind: str, now: float) -> None:
        if self.disposed:
            return
        if self.kind:
            raise RuntimeError("queries must be serialized")
        self.kind, self.deadline, self.grace = kind, now + .6, now + 2.1
        self.attributes = self.cell = self.result = None
        self.outcome = "pending"
        self.emit("query-started", query=kind)

    def settle(self, outcome: str, result: dict[str, int] | None = None) -> None:
        query, self.kind = self.kind, None
        self.result, self.outcome = result, outcome
        self.emit("query-ended", query=query, outcome=outcome, result=result)

    def feed(self, data: bytes | str, now: float) -> str:
        if self.disposed:
            return ""
        text = self.decoder.decode(data) if isinstance(data, bytes) else data
        forwarded = self.expire(now)
        text = self.pending + text
        self.pending = ""
        while text:
            if self.paste:
                end = text.find(END)
                if end >= 0:
                    self._append_paste(text, end)
                    if not self._paste_rejected:
                        forwarded += START + "".join(self._paste_parts) + END
                        self.emit("paste-accepted")
                    self._paste_parts.clear()
                    self._paste_bytes = 0
                    text, self.paste = text[end + len(END):], False
                    continue
                suffix = min(len(text), len(END) - 1)
                while suffix and not END.startswith(text[-suffix:]):
                    suffix -= 1
                self._append_paste(text, len(text) - suffix)
                self.pending = text[-suffix:] if suffix else ""
                return forwarded
            esc = text.find("\x1b")
            if esc < 0:
                return forwarded + text
            forwarded += text[:esc]
            text = text[esc:]
            if len(text) == 1:
                break
            if text.startswith("\x1b]11;") or "\x1b]11;".startswith(text):
                ending = re.search(r"\x07|\x1b\\", text[2:])
                if ending is None:
                    if len(text) > 128:
                        self.emit("report-fragment-dropped", length=len(text), reason="bounded-prefix")
                        return forwarded
                    break
                end = ending.end() + 2
                sequence, text = text[:end], text[end:]
                match = re.fullmatch(r"\x1b]11;rgb:([0-9a-fA-F]{1,4})/([0-9a-fA-F]{1,4})/([0-9a-fA-F]{1,4})(?:\x07|\x1b\\)", sequence)
                self.emit("report", report="background")
                if match and self.kind == "background":
                    values = [round(int(value, 16) * 65535 / (16 ** len(value) - 1)) for value in match.groups()]
                    self.settle("background", dict(zip(("red", "green", "blue"), values, strict=True)))
                continue
            if text[1] != "[":
                forwarded += text[0]
                text = text[1:]
                continue
            end = 2
            while end < len(text) and not "@" <= text[end] <= "~":
                end += 1
            if end == len(text):
                if len(text) > 128:
                    self.emit("report-fragment-dropped", length=len(text), reason="bounded-prefix")
                    return forwarded
                break
            sequence, text = text[:end + 1], text[end + 1:]
            if sequence == START:
                self.paste = True
                self._paste_parts.clear()
                self._paste_bytes = 0
                self._paste_rejected = False
            elif sequence in {"\x1b[I", "\x1b[O"}:
                self.emit("focus", focused=sequence == "\x1b[I")
            elif match := re.fullmatch(r"\x1b\[\?([\d;]+)c", sequence):
                self.emit("report", report="DA")
                if self.kind == "probe":
                    self.attributes = [int(v) for v in match[1].split(";") if v]
                    if 4 not in self.attributes:
                        self.settle("unsupported")
                    elif self.cell:
                        self.settle("supported", self.cell)
            elif match := re.fullmatch(r"\x1b\[6;(\d+);(\d+)t", sequence):
                self.emit("report", report="cell")
                if self.kind == "probe" and int(match[1]) > 0 and int(match[2]) > 0:
                    self.cell = {"cell_width": int(match[2]), "cell_height": int(match[1])}
                    if self.attributes and 4 in self.attributes:
                        self.settle("supported", self.cell)
            elif match := re.fullmatch(r"\x1b\[(\d+);(\d+)R", sequence):
                row, column = int(match[1]), int(match[2])
                if self.cpr_pending() and row > 0 and column > 0:
                    forwarded += sequence
                elif self.kind == "cursor" and row > 0 and column > 0:
                    self.settle("cursor", {"row": row, "column": column})
                elif row == 1 and 2 <= column <= 8 and now > self.grace:
                    forwarded += sequence
                else:
                    self.emit("report", report="CPR-late")
            else:
                forwarded += sequence
        self.pending, self.since = text, now
        return forwarded

    def _append_paste(self, text: str, end: int) -> None:
        if self._paste_rejected:
            return
        # 每次只编码有限片段，跨限feed不会先复制/编码整段载荷。
        for offset in range(0, end, 4096):
            part = text[offset:min(offset + 4096, end)]
            size = len(part.encode("utf-8", errors="surrogatepass"))
            if self._paste_bytes + size > PASTE_LIMIT_BYTES:
                self._paste_rejected = True
                self._paste_parts.clear()
                self._paste_bytes = 0
                self.emit("paste-rejected", limit_bytes=PASTE_LIMIT_BYTES)
                return
            self._paste_parts.append(part)
            self._paste_bytes += size

    def expire(self, now: float) -> str:
        if self.kind and now >= self.deadline:
            self.settle("timeout")
        if not self.pending or self.paste:
            return ""
        known = bool(re.match(r"^\x1b\[(?:\?[\d;]*|6;[\d;]*|\d+;[\d;]*)$", self.pending)) or self.pending.startswith("\x1b]11;")
        delay = 2 if self.pending.startswith(("\x1b[", "\x1b]11;")) else (.68 if now <= self.grace else .08)
        if now - self.since < delay:
            return ""
        pending, self.pending = self.pending, ""
        if known:
            self.emit("report-fragment-dropped", length=len(pending), reason="timeout")
            return ""
        return pending

    def dispose(self) -> None:
        if self.kind:
            self.settle("disposed")
        if self.paste:
            self.emit("paste-incomplete-on-exit")
        self._paste_parts.clear()
        self._paste_bytes = 0
        self.disposed, self.pending = True, ""


class ParserGate:
    """锁版本窄适配：在 ptk 的 VT parser 前过滤，不增设 stdin reader。

    封装并检查已锁定 3.0.52 的 parser slot。
    不替换 raw_mode，因此无第二份 raw generation 或模式回滚者。
    """

    def __init__(self, source: Input, reports: Reports, clock: Callable[[], float]) -> None:
        self.reports, self.clock = reports, clock
        self._high_surrogate = ""
        self.owner = getattr(source, "console_input_reader", source)
        self.slot = "_vt100_parser" if hasattr(self.owner, "_vt100_parser") else "vt100_parser"
        self.original: Any = getattr(self.owner, self.slot, None)
        if self.original is None:
            raise RuntimeError("终端VT输入后端不兼容，请使用文本管道入口并保留诊断信息")
        setattr(self.owner, self.slot, self)

    def feed(self, text: str) -> None:
        text = self._high_surrogate + text
        self._high_surrogate = ""
        # Windows ptk can call feed once per UTF-16 unit, even across reads.
        if text and "\ud800" <= text[-1] <= "\udbff":
            self._high_surrogate, text = text[-1], text[:-1]
        self.original.feed(self.reports.feed(normalizeSurrogates(text), self.clock()))

    def flush(self) -> None:
        self.original.feed(self.reports.expire(self.clock()))
        self.original.flush()

    def tick(self) -> bool:
        text = self.reports.expire(self.clock())
        if text:
            self.original.feed(text)
            self.original.flush()
        return bool(text)

    def restore(self) -> None:
        setattr(self.owner, self.slot, self.original)
        self._high_surrogate = ""
        self.reports.dispose()


class TerminalQueries:
    """同Reports上的串行有界查询；不持stdin/raw_mode，也不新增reader。"""

    def __init__(self, reports: Reports, write: Callable[[str, Callable[[], bool]], Awaitable[bool]],
                 *, isTTY: bool, cursor_offset: Callable[[], int] = lambda: 0) -> None:
        self.reports, self._write, self._enabled = reports, write, isTTY
        self._offset = cursor_offset
        self._lock = asyncio.Lock()
        self._pending: asyncio.Future[dict[str, int] | None] | None = None
        self._disposed = False

    def on_event(self, kind: str, **data: object) -> None:
        if kind != "query-ended" or data.get("query") not in {"probe", "cursor"}:
            return
        result = data.get("result")
        if self._pending is not None and not self._pending.done():
            value = result if isinstance(result, dict) and all(isinstance(k, str) and isinstance(v, int) for k, v in result.items()) else None
            self._pending.set_result(value)

    async def _query(self, kind: str) -> dict[str, int] | None:
        async with self._lock:
            if self._disposed or not self._enabled or self.reports.kind is not None:
                return None
            self._pending = asyncio.get_running_loop().create_future()
            self.reports.begin(kind, monotonic())
            try:
                sequence = "\x1b[c\x1b[16t" if kind == "probe" else "\x1b[6n"
                if not await self._write(sequence, lambda: not self._disposed and self.reports.kind == kind):
                    if self.reports.kind == kind:
                        self.reports.settle("unavailable")
                    return None
                try:
                    return await asyncio.wait_for(asyncio.shield(self._pending), .65)
                except TimeoutError:
                    if self.reports.kind == kind:
                        self.reports.settle("timeout")
                    return None
            finally:
                if self.reports.kind == kind:
                    self.reports.settle("cancelled")
                self._pending = None

    async def probe(self) -> dict[str, int] | None:
        return await self._query("probe")

    async def cursor(self) -> dict[str, int] | None:
        # ptk run_in_terminal查询位于已擦动态区的起点；补回已测行数，
        # 向原imageAnchor提供“动态区之后”的来源坐标，不猜绝对原点。
        offset = self._offset()
        value = await self._query("cursor")
        return {**value, "row": value["row"] + offset} if value and "row" in value else None

    def dispose(self) -> None:
        self._disposed = True
        if self._pending is not None and not self._pending.done():
            self._pending.set_result(None)
