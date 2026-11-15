"""定义文件发布的回执和失败类型，供不同平台的原子写入接口共用。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


class AtomicFileError(RuntimeError):
    """私有文件或目录操作未能完成。"""


class DurabilityUnconfirmedError(AtomicFileError):
    """新内容已可见，但持久化未获确认。"""


@dataclass(frozen=True)
class PublishReceipt:
    file: str
    tmp_file: str
    replaced: bool | None
    durability: Literal["confirmed", "unconfirmed"]
    bytes_written: int
    directory_sync: str
    note: str
