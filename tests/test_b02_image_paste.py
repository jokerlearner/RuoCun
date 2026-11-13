"""冻结App图片粘贴/Read语义及D10/D17合成图片边界，不读写系统剪贴板。"""

import asyncio
import base64
import json
import struct
import zlib

import pytest


def png(width=1, height=1):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\0\xff\0\0\xff")) + chunk(b"IEND", b""))


def test_source_path_image_and_failure_preserves_text(tmp_path):
    from ruocun.tui.image_paste import imageFromPath, pastedImagePath, prepareImageInput
    path = tmp_path / "shot.png"
    path.write_bytes(png())
    image = imageFromPath(path)
    assert image["mediaType"] == "image/png" and base64.b64decode(image["base64"]) == png()
    assert pastedImagePath(f'"{path}"') == path
    assert pastedImagePath("not-a-path.png") is None
    parts = asyncio.run(prepareImageInput("看一下 @shot.png", model="kimi-k2.6", cwd=tmp_path))
    assert isinstance(parts, list) and parts[0] == {"type": "text", "text": "看一下 @shot.png"}
    assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,")
    missing = str(tmp_path / "missing.jpeg")
    assert pastedImagePath(missing) is not None
    assert imageFromPath(tmp_path / "missing.jpeg") is None
    assert asyncio.run(prepareImageInput(missing, model="kimi-k2.6", cwd=tmp_path)) == missing
    notices = []
    assert asyncio.run(prepareImageInput("看一下 @shot.png", model="synthetic-no-vision", cwd=tmp_path, notice=notices.append)) == "看一下 @shot.png"
    assert notices


def test_source_image_placeholder_and_unsupported_projection():
    from ruocun.tui.image_paste import prepareImageInput
    from ruocun.tui.input_text import PasteStore
    store = PasteStore()
    placeholder = store.insert_image({"mediaType": "image/png", "base64": base64.b64encode(png()).decode()})
    assert placeholder == "[图片#1]"
    parts = store.expand("说明 " + placeholder)
    assert isinstance(parts, list) and parts[0] == {"type": "text", "text": "说明 "}
    assert parts[1]["type"] == "image_url"
    assert json.dumps(parts, ensure_ascii=False).find("[图片#1]") < 0
    text = asyncio.run(prepareImageInput(parts, model="synthetic-no-vision", cwd=None))
    assert text == "说明"


def test_d10_clipboard_bounded_formats_and_d17_rgba():
    from ruocun.platform.windows.clipboard import ClipboardPayload
    from ruocun.tui.image_paste import getClipboardImages, imageFromBytes
    assert imageFromBytes(b"not-image") is None
    assert imageFromBytes(b"\x89PNG\r\n\x1a\n" + b"broken huge image") is None
    assert imageFromBytes(png(200_000, 200_000)) is None
    assert imageFromBytes(png() + b"x" * (5 * 1024 * 1024)) is None
    assert asyncio.run(getClipboardImages(lambda: ClipboardPayload("png", png())))[0]["mediaType"] == "image/png"
    assert asyncio.run(getClipboardImages(lambda: ClipboardPayload("unavailable"))) == []
    # D17 RGBA合成像素；V5 BGRA、top-down，高alpha与透明逐像素保留。
    pixels = bytes([255, 0, 0, 0, 0, 255, 0, 128, 0, 0, 255, 255, 7, 11, 13, 17])
    bgra = b"".join(bytes((pixels[i+2], pixels[i+1], pixels[i], pixels[i+3])) for i in range(0, len(pixels), 4))
    header = bytearray(124)
    struct.pack_into("<IiiHHII", header, 0, 124, 2, -2, 1, 32, 3, 16)
    struct.pack_into("<IIII", header, 40, 0xFF0000, 0xFF00, 0xFF, 0xFF000000)
    result = asyncio.run(getClipboardImages(lambda: ClipboardPayload("dibv5", bytes(header) + bgra)))
    data = base64.b64decode(result[0]["base64"])
    offset, compressed = 8, b""
    while offset < len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        if data[offset+4:offset+8] == b"IDAT":
            compressed += data[offset+8:offset+8+length]
        offset += 12 + length
    raw = zlib.decompress(compressed)
    assert raw == b"\0" + pixels[:8] + b"\0" + pixels[8:]
    # 同D17的DIB24，bottom-up与每行DWORD padding，不沿V5布局猜像素起点。
    header24 = struct.pack("<IiiHHIIiiII", 40, 2, 2, 1, 24, 0, 16, 0, 0, 0, 0)
    top = b"\0\0\xff\0\xff\0\0\0"
    bottom = b"\xff\0\0\x0d\x0b\x07\0\0"
    result24 = asyncio.run(getClipboardImages(lambda: ClipboardPayload("dib", header24 + bottom + top)))
    assert result24 and result24[0]["mediaType"] == "image/png"
    assert asyncio.run(getClipboardImages(lambda: ClipboardPayload("dib", header24 + bottom))) == []


def test_source_drag_fallback_and_d10_explicit_clipboard_action(tmp_path):
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent.input_broker import InputBroker
    from ruocun.platform.windows.clipboard import ClipboardPayload
    async def scenario():
        path = tmp_path / "shot.png"
        path.write_bytes(png())
        async def pause():
            pass
        with create_pipe_input() as pipe:
            broker = InputBroker(on_pause=pause, input=pipe, output=DummyOutput())
            broker.configure_terminal({"RUOCUN_THEME": "dark"})
            broker.configure_images(clipboard=lambda: ClipboardPayload("png", png()))
            await broker.start()
            async def until(predicate):
                async with asyncio.timeout(2):
                    while not predicate():
                        await asyncio.sleep(.01)
            try:
                pipe.send_text("说明\x1bv")
                await until(lambda: "[图片#1]" in broker.buffer.text)
                with pytest.raises(TimeoutError):
                    await asyncio.wait_for(broker.next_submission(), .02)
                pipe.send_text("\r")
                first = await broker.next_submission()
                assert isinstance(first, list) and any(part["type"] == "image_url" for part in first)
                broker.restore_submission(first)
                assert "说明" in broker.buffer.text and "[图片#" in broker.buffer.text
                broker.buffer.reset()
                pipe.send_text("\x1b[200~" + str(path) + "\x1b[201~")
                await until(lambda: "[图片#" in broker.buffer.text)
                pipe.send_text("\r")
                assert isinstance(await broker.next_submission(), list)
                missing = str(tmp_path / "missing.jpeg")
                pipe.send_text("\x1b[200~" + missing + "\x1b[201~")
                await until(lambda: broker.buffer.text == missing)
                pipe.send_text("\r")
                assert await broker.next_submission() == missing
            finally:
                await broker.close()
    asyncio.run(scenario())
