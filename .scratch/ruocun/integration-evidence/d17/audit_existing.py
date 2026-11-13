"""Only query objects named in an already completed replay; never rerun probes."""
import importlib.util
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / 'safe-source'))
spec = importlib.util.spec_from_file_location('d17_post_audit', Path(__file__).with_name('audit_conftest.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
audit.ROOT = root
incomplete = []
journal = root / 'native-object-journal.json'
if journal.exists():
    value = json.loads(journal.read_text('utf-8'))
    for group, names in value['owned'].items():
        audit.OWNED[group].update(names)
    audit.ICON_EVENTS.extend(value['icon_events'])
else:
    incomplete.append('The first post-test hook failed before persisting Job/class/icon names. Their exact names cannot be re-queried. Candidate per-probe cleanup and completed pytest process lifetime remain separate evidence.')
for path in (root / 'pytest').rglob('*.json'):
    try:
        value = json.loads(path.read_text('utf-8'))
    except (ValueError, UnicodeDecodeError):
        continue
    if path.name == 'cred.json':
        prefix = value['prefix']
        for account in ['Profile','profile','中文/账户']:
            audit.OWNED['credentials'].add(prefix + '/' + account.encode('utf-8').hex())
        audit.OWNED['credentials'].update([prefix + '/NativeCase', (prefix + '/NativeCase').lower(), prefix + '/boundary', prefix + '/fallback'])
    if value.get('credential_target'):
        audit.OWNED['credentials'].add(value['credential_target'])
    if path.name == 'isolate.json' and value.get('private_desktop'):
        audit.OWNED['desktops'].add(value['private_desktop'])
audit.pytest_sessionfinish(None, -1)
report_path = root / 'native-object-audit.json'
report = json.loads(report_path.read_text('utf-8'))
report.update(incomplete_observations=incomplete, mode='read-only-post-audit; no probe tests executed',
              original_pytest_exit=1, original_test_observation='Ten passed progress markers; sessionfinish audit hook raised AttributeError; not an overall successful pytest run.')
report['all_object_types_independently_verified'] = not incomplete
if incomplete:
    report['notification'] = {'status': 'not-independently-requeried; original notify.json records cleanup=true',
        'events': [], 'all_added_icons_deleted': None, 'all_owner_windows_destroyed': None}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'all_recorded_objects_absent': report['all_recorded_objects_absent'],
    'incomplete_observations': len(incomplete),
    'counts': {group: len(report[group]) for group in ['credentials','jobs','desktops','stations','window_classes','profiles','tasks','processes']}}))
