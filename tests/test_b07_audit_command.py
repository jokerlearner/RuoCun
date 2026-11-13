"""Source /audit routes the existing six trace reports without running models."""

import json


def test_source_audit_reports_skip_bad_lines_and_keep_session_selection_inside_root(tmp_path):
    from ruocun.commands.audit import auditCommand

    selected=tmp_path/'synthetic-session'
    selected.mkdir()
    (selected/'tool-trace.jsonl').write_text('not-json\n'+json.dumps({
        'kind':'call','name':'Read','cap':'read','ok':False,'durationMs':12,'args':'synthetic'})+'\n',encoding='utf-8')
    output=auditCommand(['all'],sessionsRoot=tmp_path,currentId='synthetic-session',redact=lambda text:text)
    assert 'Read' in output and '错误率 100%' in output
    for category in ('memory','reflect','tools','perms','cache','skills'):
        assert auditCommand([category],sessionsRoot=tmp_path,currentId='synthetic-session',redact=lambda text:text)
    assert '用法' in auditCommand([],sessionsRoot=tmp_path,currentId='synthetic-session',redact=lambda text:text)
    assert '无效会话' in auditCommand(['all','../outside'],sessionsRoot=tmp_path,currentId='synthetic-session',redact=lambda text:text)
