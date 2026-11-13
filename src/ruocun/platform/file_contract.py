"""Shared durable-file failures and publication receipt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


class AtomicFileError(RuntimeError):
    """Private file or directory operation did not complete."""


class DurabilityUnconfirmedError(AtomicFileError):
    """Publication is visible, but durable acknowledgement is unknown."""


@dataclass(frozen=True)
class PublishReceipt:
    file: str
    tmp_file: str
    replaced: bool | None
    durability: Literal["confirmed", "unconfirmed"]
    bytes_written: int
    directory_sync: str
    note: str
