"""Repeated prefix summaries retain transcript order through real archive APIs."""

import json
import sqlite3

from ruocun.session.archive import branch_archive, read_archive, save_projection
from ruocun.session.contract import ArchiveDerivation, ArchiveRewrite


def _database():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, json TEXT NOT NULL)")
    return connection


def _read_messages(connection, identity):
    offset, fragments = 0, []
    while offset is not None:
        page = read_archive(connection, "main", identity, offset=offset, limit=17)
        fragments.append(page["text"])
        offset = page["next_offset"]
    return json.loads("".join(fragments))


def test_repeated_prefix_summaries_keep_original_order_across_branch_origins():
    original = [
        {"role": "system", "content": "SYSTEM"},
        {"role": "user", "content": "early request"},
        {"role": "assistant", "content": "early answer"},
        {"role": "system", "content": "[[ruocun:session-start-hook]]\nLATE HOOK"},
        {"role": "user", "content": "recent request"},
        {"role": "assistant", "content": "recent answer"},
    ]
    with _database() as source, _database() as branch:
        save_projection(source, "source", "main", original)
        first = [original[0], original[3], {"role": "system", "content": "first summary"}, *original[4:]]
        save_projection(source, "source", "main", first, ArchiveRewrite(
            "compact", tuple(original), (0, 3, None, 4, 5),
            (ArchiveDerivation("summary-one", "summary", 2, (0, 1, 2, 3)),),
        ))
        second = [*first[:2], {"role": "system", "content": "second summary"}, first[-1]]
        save_projection(source, "source", "main", second, ArchiveRewrite(
            "compact", tuple(first), (0, 1, None, 4),
            (ArchiveDerivation("summary-two", "summary", 2, (0, 1, 2, 3)),),
        ))
        assert _read_messages(source, "summary-two") == original[:5]

        inherited = branch_archive(source, "source")
        local = [{"role": "user", "content": "branch request"}, {"role": "assistant", "content": "branch answer"}]
        continued = [*second, *local]
        save_projection(branch, "branch", "main", continued, imported=inherited)
        third = [*second[:2], {"role": "system", "content": "branch summary"}, local[-1]]
        save_projection(branch, "branch", "main", third, ArchiveRewrite(
            "compact", tuple(continued), (0, 1, None, 5),
            (ArchiveDerivation("summary-three", "summary", 2, (0, 1, 2, 3, 4)),),
        ))
        assert _read_messages(branch, "summary-three") == [*original, local[0]]
