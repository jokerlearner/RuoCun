"""按参考实现的 UTF-8 规则计算记忆文本摘要，供来源校验使用。"""

import hashlib


def contentHash(text: str) -> str:
    # Node 将孤立的 UTF-16 代理项编码为 U+FFFD。
    normalized = text.encode("utf-16-le", errors="surrogatepass").decode("utf-16-le", errors="replace")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
