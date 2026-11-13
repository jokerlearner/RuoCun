"""冻结Read缺少图片单测；本文件仅作N0必要适配确认，不计来源新增矩阵。"""

import asyncio

from ruocun.tools.paths import detectImageFormat
from ruocun.tools.read_file import readFileTool
from ruocun.tools.types import ToolContext


def test_magic_prefixes_match_frozen_paths_helper():
    for data, expected in (
        (b"\x89PNG", "image/png"), (b"\xff\xd8", "image/jpeg"),
        (b"GIF", "image/gif"), (b"RIFF", "image/webp"), (b"", None),
    ):
        assert detectImageFormat(data) == expected


def test_read_english_text_and_image_messages(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"a\nb\n")
    ctx = ToolContext(str(tmp_path), lang="en")
    text = asyncio.run(readFileTool.handler({"path": "a.txt", "limit": 20}, ctx))
    assert text.startswith("1\ta\n2\tb\n3\t\n")
    assert "Read all 3 lines" in text and "limit" in text
    (tmp_path / "image.jpg").write_bytes(b"\x89PNG")
    image = asyncio.run(readFileTool.handler({"path": "image.jpg"}, ctx))
    assert image == "[Image loaded: image.jpg (4 bytes, image/png)]"
    assert ctx.currentImageData == {"base64": "iVBORw==", "mediaType": "image/png"}
    (tmp_path / "utf16.txt").write_text("😀" * 1001, encoding="utf-8")
    long_line = asyncio.run(readFileTool.handler({"path": "utf16.txt"}, ctx))
    assert long_line == "1\t" + "😀" * 1000 + "…(line has 2002 chars, truncated)"


def test_image_read_source_format_size_and_vision_guards(tmp_path):
    path = tmp_path / "image.png"
    path.write_bytes(b"not-an-image")
    ctx = ToolContext(str(tmp_path), sessionModel="glm-5.3-flash")
    invalid = asyncio.run(readFileTool.handler({"path": "image.png"}, ctx))
    assert invalid == "Error: 无法识别图片格式,支持 png/jpg/gif/webp。"
    assert ctx.currentImageData is None
    path.write_bytes(b"\x89PNG")
    ctx.sessionModel = "deepseek-v4-pro"
    unsupported = asyncio.run(readFileTool.handler({"path": "image.png"}, ctx))
    assert unsupported == "Error: 当前模型 deepseek-v4-pro 不支持图片输入,无法读取图片文件。"
    assert ctx.currentImageData is None
    # 原始源码在offset/limit绕过文本大小护栏后仍独立检查图片5MB限制。
    path.write_bytes(b"\x89PNG" + b"x" * (5 * 1024 * 1024))
    too_large = asyncio.run(readFileTool.handler({"path": "image.png", "limit": 1}, ctx))
    assert too_large == "Error: 图片过大(5.0MB > 5MB)。"
    assert ctx.currentImageData is None
