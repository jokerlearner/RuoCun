"""SQLite 连接与显式事务（MM-601 / REC-03）。

冻结来源：``src/session/sqlite.ts``（BEGIN IMMEDIATE / COMMIT / ROLLBACK，
ROLLBACK 失败保留原错）与 ``src/session/durable_store.ts:56-79``
（busy_timeout=3000 / journal_mode=WAL / synchronous=FULL / foreign_keys=ON，
并读回核验）。09 报告 ``# SQLite及文件路线`` 进一步要求：保留默认线程检查、
DB 专属单线程创建/使用/关闭、SQL 异常 / rollback 异常 / "提交结果未确认"
分开保留、失败保留原错不伪造成功。

连接只在受控运行库门禁通过之后由调用方创建；本模块不做静默 DLL 回退。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from .contract import StoreError

if TYPE_CHECKING:
    import sqlite3

_T = TypeVar("_T")


class RollbackError(StoreError):
    """事务体已失败且 ROLLBACK 也失败；原错保留在 __cause__。"""


class CommitUnconfirmedError(StoreError):
    """COMMIT 回执未确认：不得因取消/异常推断已 rollback 或已提交。"""


def connect_database(path: Any, readonly: bool = False) -> "sqlite3.Connection":
    """在本进程已核验的 sqlite3 上打开连接。

    isolation_level=None 表示显式事务；timeout=3s；check_same_thread 保持默认，
    连接只能由创建它的 DB 专属线程使用。
    """
    import sqlite3

    target = f"{Path(path).resolve().as_uri()}?mode=ro" if readonly else str(path)
    con = sqlite3.connect(
        target,
        timeout=3.0,
        isolation_level=None,
        check_same_thread=True,
        uri=readonly,
    )
    return con


def configure_connection(con: "sqlite3.Connection") -> dict[str, Any]:
    """设置并读回 WAL / FULL / busy_timeout=3000 / foreign_keys=ON。"""
    con.execute("PRAGMA busy_timeout=3000")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    journal = str(con.execute("PRAGMA journal_mode").fetchone()[0])
    synchronous = int(con.execute("PRAGMA synchronous").fetchone()[0])
    busy_timeout = int(con.execute("PRAGMA busy_timeout").fetchone()[0])
    foreign_keys = int(con.execute("PRAGMA foreign_keys").fetchone()[0])
    config = {
        "journal_mode": journal,
        "synchronous": synchronous,
        "busy_timeout": busy_timeout,
        "foreign_keys": foreign_keys,
    }
    if journal != "wal" or synchronous != 2 or busy_timeout != 3000 or foreign_keys != 1:
        raise StoreError("SQLite 持久配置未生效（WAL/FULL/busy3000/foreign_keys）。")
    return config


def transaction(
    con: "sqlite3.Connection", body: Callable[[], _T], *, readonly: bool = False,
) -> _T:
    """显式 BEGIN IMMEDIATE / COMMIT / ROLLBACK；三类失败分开保留。

    - 事务体异常：ROLLBACK 成功则原样重抛原错；ROLLBACK 也失败则抛
      RollbackError 并把原错作为 __cause__ 保留。
    - COMMIT 异常：抛 CommitUnconfirmedError（提交结果未确认），原错保留在
      __cause__；不得据此推断 rollback 或已提交，也不得重发事务。
    """
    con.execute("BEGIN" if readonly else "BEGIN IMMEDIATE")
    try:
        value = body()
    except BaseException as original:
        try:
            con.execute("ROLLBACK")
        except BaseException as rollback_error:
            raise RollbackError(
                f"事务体失败且 ROLLBACK 也失败：{rollback_error}"
            ) from original
        raise
    try:
        con.execute("COMMIT")
    except BaseException as commit_error:
        try:
            con.execute("ROLLBACK")
        except BaseException as rollback_error:
            raise CommitUnconfirmedError(
                f"COMMIT 结果未确认且 ROLLBACK 也失败：{rollback_error}"
            ) from commit_error
        raise CommitUnconfirmedError(
            "COMMIT 结果未确认：不得推断已提交或已回滚，须用同一操作身份读回。"
        ) from commit_error
    return value


__all__ = [
    "RollbackError",
    "CommitUnconfirmedError",
    "connect_database",
    "configure_connection",
    "transaction",
]
