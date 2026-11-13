"""ADR-0013 necessary mutation adaptation: malformed input stays reviewable."""
import asyncio

import pytest

from ruocun.approval.store import appendAlwaysApproved, loadAlwaysApproved
from ruocun.config.trust import addTrusted, isTrusted
from ruocun.permissions.settings import appendRuleSync


def test_bad_existing_documents_are_preserved(tmp_path):
    settings = tmp_path / "settings.json"
    settingsRaw = b'{"permissions":{"defaultMode":"bypassPermissions"},"bad":NaN}'
    settings.write_bytes(settingsRaw)
    with pytest.raises(ValueError):
        appendRuleSync(settings, "Read")
    assert settings.read_bytes() == settingsRaw
    trusted = tmp_path / "trusted.json"
    project = tmp_path / "project"
    trustedRaw = ('["' + str(project).replace("\\", "\\\\") + '",Infinity]').encode()
    trusted.write_bytes(trustedRaw)
    assert not asyncio.run(isTrusted(project, userRoot=tmp_path))
    with pytest.raises(ValueError):
        asyncio.run(addTrusted(tmp_path / "project", userRoot=tmp_path))
    assert trusted.read_bytes() == trustedRaw
    approvals = tmp_path / "approvals.json"
    approvalsRaw = b'["Write",-Infinity]'
    approvals.write_bytes(approvalsRaw)
    assert asyncio.run(loadAlwaysApproved(approvals)) == set()
    with pytest.raises(ValueError):
        asyncio.run(appendAlwaysApproved(approvals, "Write"))
    assert approvals.read_bytes() == approvalsRaw
