"""Observable SQLite connection semantics from the frozen SQLite port."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ruocun.session.sqlite_port import (
    CommitUnconfirmedError,
    connect_database,
    transaction,
)


def test_readonly_connection_cannot_write_or_create_database(tmp_path: Path) -> None:
    existing = tmp_path / "existing session #1.db"
    with sqlite3.connect(existing) as con:
        con.execute("CREATE TABLE data (value TEXT)")

    con = connect_database(existing, readonly=True)
    try:
        with pytest.raises(sqlite3.OperationalError):
            con.execute("INSERT INTO data VALUES ('must not be written')")
    finally:
        con.close()

    absent = tmp_path / "must not create.db"
    with pytest.raises(sqlite3.OperationalError):
        connect_database(absent, readonly=True)
    assert not absent.exists()


def test_transaction_failure_rolls_back_run_and_event_together() -> None:
    """Synthetic :memory: adapter check, not a product DLL-gate claim."""
    con = sqlite3.connect(":memory:", isolation_level=None)
    try:
        con.execute("CREATE TABLE runs (id TEXT PRIMARY KEY)")
        con.execute("CREATE TABLE events (id TEXT PRIMARY KEY)")
        con.execute("INSERT INTO events VALUES ('duplicate')")

        def write_run_and_duplicate_event() -> None:
            con.execute("INSERT INTO runs VALUES ('new-run')")
            con.execute("INSERT INTO events VALUES ('duplicate')")

        with pytest.raises(sqlite3.IntegrityError):
            transaction(con, write_run_and_duplicate_event)
        assert con.execute("SELECT id FROM runs").fetchall() == []
        assert con.execute("SELECT id FROM events").fetchall() == [("duplicate",)]
    finally:
        con.close()


def test_lost_commit_ack_is_unknown_even_when_database_committed() -> None:
    """Inject an acknowledgement error at the SQLite connection boundary."""
    con = sqlite3.connect(":memory:", isolation_level=None)
    con.execute("CREATE TABLE events (id TEXT PRIMARY KEY)")

    class LostAcknowledgement:
        def execute(self, sql: str) -> sqlite3.Cursor:
            result = con.execute(sql)
            if sql == "COMMIT":
                raise sqlite3.OperationalError("synthetic lost commit acknowledgement")
            return result

    try:
        def insert_event() -> None:
            con.execute("INSERT INTO events VALUES ('one')")

        with pytest.raises(CommitUnconfirmedError) as caught:
            transaction(LostAcknowledgement(), insert_event)  # type: ignore[arg-type]
        assert isinstance(caught.value.__cause__, sqlite3.OperationalError)
        assert con.execute("SELECT id FROM events").fetchall() == [("one",)]
    finally:
        con.close()
