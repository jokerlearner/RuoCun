"""Frozen reference memory/hash.ts (MIT)."""

import hashlib


def contentHash(text: str) -> str:
    # Node UTF-8 replaces isolated UTF-16 surrogates with U+FFFD.
    normalized = text.encode("utf-16-le", errors="surrogatepass").decode("utf-16-le", errors="replace")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
