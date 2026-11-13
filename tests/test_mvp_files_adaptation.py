"""ADR-0011必要首版确认；单列，不计作DAO来源断言。"""

import asyncio
import json

import pytest

from ruocun.tools.edit_file import editFileTool
from ruocun.tools.read_file import readFileTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext, ToolRejected
from ruocun.tools.write_file import writeFileTool


def test_external_write_denial_has_no_side_effect(tmp_path):
    outside = tmp_path.parent / "denied-external-write.txt"
    with pytest.raises(ToolRejected):
        asyncio.run(writeFileTool.handler({"path": str(outside), "content": "forbidden"}, ToolContext(str(tmp_path))))
    assert not outside.exists()


def test_edit_rejects_external_change_since_read(tmp_path):
    # 复用来源Write P2-23语义到ADR-0011的Edit读后保护。
    path = tmp_path / "f.txt"
    path.write_bytes(b"original")
    ctx = ToolContext(str(tmp_path))
    asyncio.run(readFileTool.handler({"path": "f.txt"}, ctx))
    path.write_bytes(b"changed externally")
    with pytest.raises(ValueError, match="已被外部改动"):
        asyncio.run(editFileTool.handler({"path": "f.txt", "old_string": "changed", "new_string": "bad"}, ctx))
    assert path.read_bytes() == b"changed externally"


def test_image_read_populates_pending_image_data(tmp_path):
    # N0恢复原Read图片能力；保留原MVP图片fixture，不再断言已撤销的范围限制。
    (tmp_path / "image.png").write_bytes(b"\x89PNG")
    ctx = ToolContext(str(tmp_path))
    out = asyncio.run(readFileTool.handler({"path": "image.png"}, ctx))
    assert out == "[已读取图片: image.png (4 bytes, image/png)]"
    assert ctx.currentImageData == {"base64": "iVBORw==", "mediaType": "image/png"}


def test_integer_json_number_normalizes_for_python_slice(tmp_path):
    # Zod number().int()接受2.0；Python slice需要int。
    (tmp_path / "a.txt").write_bytes(b"line1\nline2\nline3\n")
    registry = ToolRegistry()
    registry.register(readFileTool)
    args = json.dumps({"path": "a.txt", "offset": 2.0, "limit": 1.0})
    assert asyncio.run(registry.dispatch("Read", args, ToolContext(str(tmp_path)))) == "2\tline2"


def test_unsupported_parameter_rejected_before_handler(tmp_path):
    registry = ToolRegistry()
    registry.register(writeFileTool)
    with pytest.raises(ValueError, match="不接受参数"):
        registry.validate("Write", '{"path":"no-write.txt","content":"x","unsupported":true}')
    assert not (tmp_path / "no-write.txt").exists()
