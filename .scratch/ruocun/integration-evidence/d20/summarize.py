"""Read already-saved archive only; no OS probes or mutation of original evidence."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parent
out = root / 'r1'
manifest = json.loads((out / 'archive-manifest.json').read_text('utf-8'))
archive_path = out / 'bytes.zip'
checks = [hashlib.sha256(archive_path.read_bytes()).hexdigest() == manifest['archive_sha256']]
reports = []
with zipfile.ZipFile(archive_path) as archive:
    checks.append(len(archive.namelist()) == len(manifest['members']))
    for row in manifest['members']:
        data = archive.read(row['path'])
        checks.append(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'])
    for name in archive.namelist():
        if name.startswith('run/') and name.endswith(('/result.json', '/owner-result.json')):
            reports.append((name, json.loads(archive.read(name))))
summary = {'archive_and_all_members_verified': all(checks), 'archive_members': len(manifest['members']),
           'full_backend_contract_met': False, 'network': [], 'normal_close': [], 'owner_crash': None}
for name, report in reports:
    if 'environment_server_teardown' in report:
        summary['owner_crash'] = report
        continue
    summary['normal_close'].append({'case': name, 'started': report['started'], 'failure': report.get('failure'), 'cleanup': report['cleanup']})
    if report.get('acl_confirmation'):
        summary['files'] = {'generations': len(report['workers']), 'acl_confirmation': report['acl_confirmation'],
            'worker_outside': [row['files']['outside'] for row in report['workers']],
            'worker_allowed': [{area: row['files'][area] for area in ('workspace', 'tmp')} for row in report['workers']],
            'host_outside': [row['files']['outside'] for row in report['host_workers']],
            'junction': {'worker': report['worker']['files']['junction_write'], 'host': report['host_control']['files']['junction_write']},
            'inherited_handle': {'worker': report['worker']['inherited_handle'], 'host': report['host_control']['inherited_handle']}}
    if report.get('worker', {}).get('external'):
        summary['network'].append({'network': report['network'], 'host_external': [row['external'] for row in report['host_workers']],
            'worker_external': [row['external'] for row in report['workers']],
            'host_loopback_controls': [row['host_loopback'] for row in report['host_workers']],
            'worker_host_loopback': [row['host_loopback'] for row in report['workers']],
            'worker_self_loopback': [row['self_loopback'] for row in report['workers']],
            'worker_parent_loopback': [row['parent_loopback'] for row in report['workers']],
            'host_nonce_receipts': len(report['host_received']), 'self_and_child_nonce_receipts': sum(len(row['self_and_child_received']) for row in report['workers'])})
    if report.get('worker', {}).get('tools'):
        summary['tools'] = report['worker']['tools']
(out / 'observations.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({'archive_and_all_members_verified': all(checks), 'archive_members': len(manifest['members']), 'native_probes_rerun': False}))
if not all(checks):
    raise SystemExit(1)
