"""Frozen src/tools/web_search.ts (MIT), DuckDuckGo HTML result parsing."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, unquote

from .schema import objectSchema
from .types import Tool, ToolContext
from .web_network import fetchWeb


def stripTags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    for pattern, value in (("&amp;", "&"), ("&#x27;|&#39;", "'"), ("&quot;", '"')):
        text = re.sub(pattern, lambda _: value, text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def decodeDdgUrl(href: str) -> str:
    match = re.search(r"[?&]uddg=([^&]+)", href)
    if match:
        try:
            if re.search(r"%(?![0-9a-f]{2})", match[1], flags=re.I):
                return href
            return unquote(match[1], errors="strict")
        except UnicodeError:
            return href
    return "https:" + href if href.startswith("//") else href


def parseSearchResults(html: str, maximum: int = 5) -> str:
    links = list(re.finditer(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', html, flags=re.I))
    results = []
    for index, link in enumerate(links[:maximum]):
        end = links[index + 1].start() if index + 1 < len(links) else len(html)
        snippet = re.search(r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>([\s\S]*?)</a>', html[link.end():end], flags=re.I)
        results.append(f"{index + 1}. {stripTags(link[2])}\n   {decodeDdgUrl(link[1])}\n   {stripTags(snippet[1]) if snippet else ''}".rstrip())
    return "\n\n".join(results) or "(无搜索结果)"


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    url = "https://html.duckduckgo.com/html/?q=" + quote(args["query"], safe="-_.!~*'()")
    try:
        response = await (ctx.fetchImpl or fetchWeb)(url, headers={"User-Agent": "Mozilla/5.0"}, signal=ctx.signal)
    except Exception as error:
        detail = "搜索超时(30s)" if isinstance(error, TimeoutError) else str(error)
        return f"Error: Search failed ({detail})" if ctx.lang == "en" else f"Error: 搜索失败({detail})"
    if not response.is_success:
        return f"Error: Search failed HTTP {response.status_code}" if ctx.lang == "en" else f"Error: 搜索失败 HTTP {response.status_code}"
    return parseSearchResults(response.content.decode("utf-8", errors="replace"), args.get("max_results", 5))


_SCHEMA = objectSchema({
    "query": {"type": "string", "description": "搜索关键词"},
    "max_results": {"type": "integer", "minimum": 1, "maximum": 10, "description": "返回结果数,默认 5"},
}, ["query"])

DESCRIPTION = (
    "通过 DuckDuckGo 查找网页，返回标题、地址和摘要。max_results 默认 5、最多 10；请求最多等待 30 秒。需要引用或核对时用 "
    "WebFetch 打开结果。"
)
DESCRIPTION_EN = (
    "Search DuckDuckGo for pages and get their titles, URLs, and snippets. max_results "
    "defaults to five and is capped at ten. Requests time out after 30 seconds. Open a "
    "result with WebFetch to verify it before citing it."
)

webSearchTool = Tool(name="WebSearch", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN,
                     schema=_SCHEMA, capability="network", approval="suggest", handler=_handler)
