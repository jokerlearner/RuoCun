"""把剪贴板图片或粘贴的绝对路径转换为可提交的图片内容。先检查文件大小、实际格式和像素规模，再按当前模型的能力决定如何提交。"""

from __future__ import annotations

import asyncio
import base64
import json
import re
import struct
import subprocess
import sys
import tempfile
import zlib
from collections.abc import Callable
from pathlib import Path

from ..client.types import ImageData
from ..config.profiles import supportsVision
from ..platform.windows.clipboard import ClipboardPayload
from ..session.inputs import Content
from ..tools.paths import classifyPath, detectImageFormat, isImagePath

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 20_000_000  # 在解码和转换前限制像素数，小文件也可能展开成大图。


def _dimensions(data: bytes, mime: str) -> tuple[int, int] | None:
    try:
        if mime == "image/png":
            if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 33 or data[12:16] != b"IHDR" or struct.unpack_from(">I", data, 8)[0] != 13:
                return None
            dimensions = struct.unpack_from(">II", data, 16)
            offset, image_data, ended = 8, False, False
            while offset + 12 <= len(data):
                size = struct.unpack_from(">I", data, offset)[0]
                end = offset + 12 + size
                if end > len(data):
                    return None
                kind, payload = data[offset + 4:offset + 8], data[offset + 8:end - 4]
                if zlib.crc32(kind + payload) != struct.unpack_from(">I", data, end - 4)[0]:
                    return None
                image_data |= kind == b"IDAT"
                if kind == b"IEND":
                    ended = size == 0
                    break
                offset = end
            return dimensions if image_data and ended else None
        if mime == "image/gif":
            return struct.unpack_from("<HH", data, 6) if data[:6] in {b"GIF87a", b"GIF89a"} and len(data) >= 14 and data.endswith(b";") else None
        if mime == "image/jpeg":
            if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
                return None
            offset = 2
            while offset + 4 <= len(data):
                if data[offset] != 0xFF:
                    return None
                while offset < len(data) and data[offset] == 0xFF:
                    offset += 1
                marker = data[offset]
                offset += 1
                if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                    continue
                size = struct.unpack_from(">H", data, offset)[0]
                if size < 2 or offset + size > len(data):
                    return None
                if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                    height, width = struct.unpack_from(">HH", data, offset + 3)
                    return width, height
                offset += size
            return None
        if mime == "image/webp":
            if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP" or struct.unpack_from("<I", data, 4)[0] + 8 != len(data):
                return None
            kind = data[12:16]
            if kind == b"VP8X":
                return int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1
            if kind == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
                width, height = struct.unpack_from("<HH", data, 26)
                return width & 0x3FFF, height & 0x3FFF
            if kind == b"VP8L" and data[20] == 0x2F:
                bits = int.from_bytes(data[21:25], "little")
                return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    except (IndexError, struct.error):
        return None
    return None


def imageFromBytes(data: bytes) -> ImageData | None:
    if not data or len(data) > MAX_BYTES:
        return None
    mime = detectImageFormat(data)
    dimensions = _dimensions(data, mime) if mime is not None else None
    if not dimensions or min(dimensions) <= 0 or dimensions[0] * dimensions[1] > MAX_PIXELS:
        return None
    return {"mediaType": mime or "", "base64": base64.b64encode(data).decode("ascii")}


def imageFromPath(path: Path) -> ImageData | None:
    try:
        if not isImagePath(str(path)):
            return None
        with path.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
        return imageFromBytes(data)
    except OSError:
        return None


def pastedImagePath(text: str) -> Path | None:
    value = text.strip().removeprefix('"').removesuffix('"').removeprefix("'").removesuffix("'")
    path = Path(value)
    return path if "\n" not in value and "\r" not in value and path.is_absolute() and isImagePath(value) else None


def _png(width: int, height: int, rows: list[bytes]) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    compressor, compressed = zlib.compressobj(), bytearray()
    for row in rows:
        compressed.extend(compressor.compress(b"\0" + row))
        if len(compressed) > MAX_BYTES:
            raise ValueError("encoded image exceeds limit")
    compressed.extend(compressor.flush())
    result = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", bytes(compressed)) + chunk(b"IEND", b"")
    if len(result) > MAX_BYTES:
        raise ValueError("encoded image exceeds limit")
    return result


def dibToPNG(data: bytes) -> bytes | None:
    if len(data) > MAX_BYTES or len(data) < 40:
        return None
    try:
        header, width, height, planes, bits, compression, declared = struct.unpack_from("<IiiHHII", data)
        if header not in {40, 52, 56, 108, 124} or header > len(data) or width <= 0 or not height or planes != 1 or bits not in {24, 32} or compression not in {0, 3}:
            return None
        top_down, height = height < 0, abs(height)
        if width * height > MAX_PIXELS:
            return None
        stride = ((width * bits + 31) // 32) * 4
        length, offset = stride * height, header
        if length > MAX_BYTES or declared and declared < length:
            return None
        masks = (0xFF0000, 0xFF00, 0xFF, 0)
        if compression == 3:
            if bits != 32:
                return None
            if header == 40:
                if len(data) < 52:
                    return None
                masks = (*struct.unpack_from("<III", data, 40), 0)
                offset += 12
            else:
                masks = (*struct.unpack_from("<III", data, 40), struct.unpack_from("<I", data, 52)[0] if header >= 56 else 0)
            nonzero = [mask for mask in masks if mask]
            if len(nonzero) < 3 or any(a & b for index, a in enumerate(nonzero) for b in nonzero[index+1:]):
                return None
            for mask in nonzero:
                shifted = mask >> ((mask & -mask).bit_length() - 1)
                if shifted & (shifted + 1):
                    return None
        colors = struct.unpack_from("<I", data, 32)[0]
        if colors:
            offset += colors * 4
        if offset + length > len(data):
            return None
        def component(value: int, mask: int, default: int) -> int:
            if not mask:
                return default
            shift = (mask & -mask).bit_length() - 1
            maximum = mask >> shift
            return round(((value & mask) >> shift) * 255 / maximum)
        rows = []
        for row in range(height):
            position = offset + (row if top_down else height - row - 1) * stride
            rgba = bytearray()
            for column in range(width):
                if bits == 24:
                    blue, green, red = data[position + column * 3:position + column * 3 + 3]
                    rgba.extend((red, green, blue, 255))
                else:
                    value = struct.unpack_from("<I", data, position + column * 4)[0]
                    rgba.extend(component(value, mask, 255) for mask in masks)
            rows.append(bytes(rgba))
        return _png(width, height, rows)
    except (ValueError, struct.error, OverflowError):
        return None


def _mac_clipboard() -> ClipboardPayload:
    try:
        with tempfile.TemporaryDirectory(prefix="ruocun-image-") as directory:
            file = Path(directory) / "clipboard.png"
            script = 'set png_data to (the clipboard as «class PNGf»)\nset fp to open for access POSIX file ' + json.dumps(str(file)) + ' with write permission\ntry\nwrite png_data to fp\non error msg number num\nclose access fp\nerror msg number num\nend try\nclose access fp'
            subprocess.run(["/usr/bin/osascript", "-e", script], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=True)
            with file.open("rb") as stream:
                return ClipboardPayload("png", stream.read(MAX_BYTES + 1))
    except (OSError, subprocess.SubprocessError):
        return ClipboardPayload("unavailable")


async def getClipboardImages(port: Callable[[], ClipboardPayload] | None = None) -> list[ImageData]:
    if port is None:
        if sys.platform == "win32":
            from ..platform.windows.clipboard import WindowsClipboard
            port = WindowsClipboard().read
        elif sys.platform == "darwin":
            port = _mac_clipboard
        else:
            return []
    try:
        payload = await asyncio.to_thread(port)
        if payload.kind == "files":
            images = await asyncio.gather(*(asyncio.to_thread(imageFromPath, Path(path)) for path in payload.paths))
            return [image for image in images if image is not None]
        raw = dibToPNG(payload.data) if payload.kind in {"dib", "dibv5"} else payload.data if payload.kind == "png" else b""
        image = imageFromBytes(raw) if raw else None
        return [image] if image is not None else []
    except Exception:
        return []


async def getImageFromClipboard() -> ImageData | None:
    images = await getClipboardImages()
    return images[0] if images else None


async def prepareImageInput(content: Content, *, model: str, cwd: Path | None,
                            notice: Callable[[str], None] | None = None) -> Content:
    if not supportsVision(model):
        if isinstance(content, list):
            text = " ".join(str(part.get("text", "")) for part in content if part.get("type") == "text").strip()
            if notice:
                notice(f"当前模型 {model} 不支持图片输入，图片已忽略。")
            return text or "[图片已忽略]"
        if re.search(r"@(\S+\.(?:png|jpe?g|gif|webp))", content, re.I) and notice:
            notice(f"当前模型 {model} 不支持图片输入，图片已忽略。")
        return content
    if not isinstance(content, str) or cwd is None:
        return content
    parts: list[dict[str, object]] = [{"type": "text", "text": content}]
    for path in re.findall(r"@(\S+\.(?:png|jpe?g|gif|webp))", content, re.I):
        try:
            classified = await asyncio.to_thread(classifyPath, str(cwd), path)
        except (OSError, ValueError):
            if notice:
                notice(f"图片 {path} 路径无法解析，已保留原文。")
            continue
        # 图片路径引用随消息一起提交，自动读取仅限当前工作目录范围。
        if classified.external:
            if notice:
                notice(f"图片 {path} 在工作区外，已跳过。")
            continue
        image = await asyncio.to_thread(imageFromPath, Path(classified.abs))
        if image:
            parts.append({"type": "image_url", "image_url": {"url": f"data:{image['mediaType']};base64,{image['base64']}"}})
        elif notice:
            notice(f"图片 {path} 无法读取或超过图片资源边界，已保留原文。")
    return parts if len(parts) > 1 else content
