"""Frozen commands.test.ts lexical routing plus the retained CMD-* inventory."""


def test_source_command_names_and_paths_preserve_case_and_unknown_names():
    from ruocun.commands.catalog import parseSlashCommand

    for text in ("hello", "/", "/tmp/a.py", "/Users/x/Desktop/a.png", "/usr/bin/node", "/Desktop/a.jpeg"):
        assert parseSlashCommand(text) is None
    assert parseSlashCommand(" /wat \talpha\n beta ") == ("wat", "alpha beta")
    assert parseSlashCommand("/org:task_name-2") == ("org:task_name-2", "")
    assert parseSlashCommand("/Config") == ("Config", "")
    assert parseSlashCommand("/config") == ("config", "")  # Unknown remains dispatcher's decision.
    assert parseSlashCommand("/accounts") == ("accounts", "")  # No implicit alias rewrite.


def test_frozen_inventory_retains_excluded_provenance_but_public_catalog_filters_it():
    from ruocun.commands.catalog import (
        COMMAND_ALIASES,
        COMMAND_NAMES,
        PUBLIC_COMMAND_NAMES,
    )

    # The 52 frozen source entries remain; B adds the native archive query.
    assert len(COMMAND_NAMES) == len(set(COMMAND_NAMES)) == 53
    assert len(set(COMMAND_NAMES) - {"archive"}) == 52
    assert len(PUBLIC_COMMAND_NAMES) == 52 and "plugin" not in PUBLIC_COMMAND_NAMES
    assert "archive" in PUBLIC_COMMAND_NAMES
    assert set(COMMAND_NAMES) - set(PUBLIC_COMMAND_NAMES) == {"plugin"}
    assert {"Config", "accounts", "quit", "task", "coordinator", "recovery", "theme", "loop"} <= set(COMMAND_NAMES)
    assert "config" not in COMMAND_NAMES
    assert COMMAND_ALIASES == {"accounts": "account", "yolo": "bypass", "task": "goal", "quit": "exit"}
