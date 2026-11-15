"""检查 WebFetch 的目标 URL，获取页面并提取可读文本。缓存截断前的纯文本，可按请求进一步提取，最后限制返回长度。"""

from __future__ import annotations

import re
from typing import Any

from .fetch_cache import getCachedFetch, setCachedFetch
from .schema import objectSchema
from .ssrf import blockedUrlReason
from .types import Tool, ToolContext
from .web_network import fetchWeb


def htmlToText(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    for entity, value in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        text = re.sub(re.escape(entity), lambda _: value, text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def truncateText(text: str, maximum: int) -> str:
    units = text.encode("utf-16-le", errors="surrogatepass")
    return units[:maximum * 2].decode("utf-16-le", errors="surrogatepass") + "\n…(已截断)" if len(units) > maximum * 2 else text


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    reason = blockedUrlReason(args["url"])
    if reason:
        return f"Error: Fetch denied ({reason})" if ctx.lang == "en" else f"Error: 拒绝抓取({reason})"
    text = getCachedFetch(args["url"])
    if text is None:
        try:
            response = await (ctx.fetchImpl or fetchWeb)(args["url"], signal=ctx.signal)
        except Exception as error:
            detail = "抓取超时(30s)" if isinstance(error, TimeoutError) else str(error)
            return f"Error: Fetch failed ({detail})" if ctx.lang == "en" else f"Error: 抓取失败({detail})"
        if not response.is_success:
            return f"Error: Fetch failed HTTP {response.status_code}" if ctx.lang == "en" else f"Error: 抓取失败 HTTP {response.status_code}"
        text = htmlToText(response.content.decode("utf-8", errors="replace"))
        setCachedFetch(args["url"], text)
    if args.get("prompt") and ctx.extractFromPage is not None:
        try:
            text = await ctx.extractFromPage(text, args["prompt"])
        except Exception:
            pass
    return truncateText(text, args.get("max_chars", 20000))


_SCHEMA = objectSchema({
    "url": {"type": "string", "format": "uri", "description": "要抓取的 http(s) URL"},
    "max_chars": {"type": "integer", "minimum": 100, "description": "最多返回字符数,默认 20000"},
    "prompt": {"type": "string", "description": "按此指令从抓到的页面里提取相关内容,返回提取结果而非整页;不传则返回整页纯文本(默认行为)"},
}, ["url"])

DESCRIPTION = (
    "下载公开 URL 并将 HTML 转成纯文本，可用 max_chars 限定长度，默认 20000 字符。需要提取特定信息时可提交对应要求。请求超时为 30 "
    "秒，拒绝本机、内网和云元数据目标。"
)
DESCRIPTION_EN = (
    "Fetch a public URL and extract text from the HTML. Use max_chars to bound the "
    "text, with 20,000 by default, or provide an extraction request for specific "
    "information. Requests have a 30-second timeout and reject local, private, and "
    "cloud metadata targets."
)

fetchUrlTool = Tool(name="WebFetch", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN,
                    schema=_SCHEMA, capability="network", approval="suggest", handler=_handler)
