"""为已核验的 SQLite 运行库提供连接配置与事务助手。

同一存储线程打开、使用并关闭连接。写事务显式开始并提交，将事务体失败、回滚失败和提交未确认分别传给调用方。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from .contract import StoreError

if TYPE_CHECKING:
    import sqlite3

_T = TypeVar("_T")


class RollbackError(StoreError):
    """事务体和回滚先后失败，原始异常保留在 __cause__ 中。"""


class CommitUnconfirmedError(StoreError):
    """提交调用报错，数据库是否已提交仍待确认。"""


def connect_database(path: Any, readonly: bool = False) -> "sqlite3.Connection":
    """在调用方已核验的 SQLite 运行库上打开连接。

    禁用隐式事务，忙等待三秒。保留 sqlite3 默认的线程检查，由创建连接的存储线程继续使用它。
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
    """配置并读回 WAL、FULL 同步、三秒忙等待和外键检查。"""
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
    """显式开启、提交或回滚写事务，并区分各阶段的失败。

    事务体抛出异常时先回滚，回滚失败则附带原错抛出 RollbackError。提交阶段报错时抛出 CommitUnconfirmedError，由调用方核查原事务状态。
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
