"""长输出写入文件，工具结果保留首尾预览和完整输出的访问路径。"""

from __future__ import annotations

import uuid
from pathlib import Path


def spillOutput(
    text: str, workspaceRoot: str, cap: int = 16000, *, persist: bool = True
) -> str:
    raw = text.encode("utf-16-le", errors="surrogatepass")
    units = len(raw) // 2
    if units <= cap:
        return text
    head, tail = int(cap * 0.6), cap - int(cap * 0.6)
    first = raw[: head * 2].decode("utf-16-le", errors="ignore")
    last = raw[-tail * 2 :].decode("utf-16-le", errors="ignore")
    output = f"{first}\n…(已省略中间 {units - cap} 字符,共 {units} 字符)…\n{last}"
    if persist:
        try:
            directory = Path(workspaceRoot) / ".ruocun" / "spill"
            directory.mkdir(parents=True, exist_ok=True)
            file = directory / (uuid.uuid4().hex + ".txt")
            file.write_text(text, encoding="utf-8")
            output += f"\n[完整输出 {units} 字符已落盘:{file} —— 需要完整内容时用 Read 读取(可配合 Grep 精确定位)]"
        except OSError:
            pass
    return output
