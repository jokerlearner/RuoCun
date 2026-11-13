"""Read-only independent evidence review; --capture writes append-only summaries."""
from pathlib import Path
import ctypes as C
import hashlib
import json
import re
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LAB = ROOT / '.scratch/ruocun-discovery/experiments/durable-io'
sys.path.insert(0, str(HERE))
from review import scan


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def audit(live=False):
    evidence_manifest = HERE / 'evidence-sha256.json'
    if evidence_manifest.exists():
        for name, expected in read(evidence_manifest).items():
            assert sha((HERE / name).read_bytes()) == expected, name
    manifest = read(HERE / 'round-manifest.json')
    archive = HERE / manifest['archive']
    assert sha(archive.read_bytes()) == manifest['archive_sha256']
    with zipfile.ZipFile(archive) as zipped:
        assert set(zipped.namelist()) == set(manifest['files'])
        raw = {name: zipped.read(name) for name in zipped.namelist()}
    assert all(sha(data) == manifest['files'][name] for name, data in raw.items())
    prefix = 'm18f-independent-r01/'
    members = {name.removeprefix(prefix): data for name, data in raw.items()}
    obj = lambda name: json.loads(members[name])
    environment = obj('environment.json')
    assert environment['git_head'] == '069def00672567e1ad7e0c6fdbd6ba3adbb13911'
    assert obj('exit.json')['returncode'] == 0
    pytest = re.search(rb'(16 passed in [0-9.]+s)', members['stdout.txt']).group(1).decode()
    for script, expected in environment['harness_sha256'].items():
        assert sha(members['h/' + script]) == expected
        assert sha((LAB / script).read_bytes()) == expected
    workers = []
    for name in members:
        if not name.endswith('/process.json'):
            continue
        base = name.removesuffix('process.json')
        process, ready, cleanup = [obj(base + suffix) for suffix in ['process.json', 'ready.json', 'cleanup.json']]
        identity = (process['pid'], process['creation_time'])
        assert identity == (ready['pid'], ready['creation_time']) == (cleanup['pid'], cleanup['creation_time'])
        assert cleanup['held_handle_signaled'] and cleanup['same_creation_time'] and cleanup['process_handle_closed']
        if 'pending_reclaimed_by_os_after_process_exit' in cleanup:
            assert cleanup['pipe_absent'] and not cleanup['forced']
        if base + 'kill.json' in members:
            kill = obj(base + 'kill.json')
            assert (kill['pid'], kill['creation_time']) == identity
            assert kill['requested_on_held_handle'] and kill['wait_signaled']
        workers.append({'folder': base, **cleanup})
    assert len(workers) == 21
    unconfirmed = ['cancel-fail', 'cancel-budget', 'wait-fail', 'wait-raise', 'result-incomplete',
                   'result-error', 'read-cancel-fail', 'write-cancel-fail']
    observations = {}
    for mode in unconfirmed:
        item = obj(mode + '/result.json')
        observation, cleanup = item['observation'], item['cleanup']
        assert observation['native_still_pending'] and observation['owner_retained'] and observation['event_open']
        assert not observation['early_event_close_attempts'] and observation['poisoned_process_reuse_blocked']
        assert cleanup['returncode'] == 96 and cleanup['pending_reclaimed_by_os_after_process_exit']
        observations[mode] = {'injections': observation['injections'], 'native_still_pending': True,
                              'application_owner_retained': True, 'native_exit': 96, 'pipe_absent': True}
    for mode, error, status in [('cancel-completed', 995, 0xc0000120), ('broken-read', 109, 0xc000014b)]:
        item = obj(mode + '/result.json')
        observation = item['observation']
        assert not observation['injections'] and not observation['owner_retained']
        assert observation['completion_records'][-1]['winerror'] == error
        assert observation['completion_records'][-1]['native_status'] == status
        assert observation['completion_records'][-1]['confirmed']
        assert item['cleanup']['returncode'] == 0 and item['cleanup']['pipe_absent']
    assert obj('pipe/result.json')['pipe_absent'] and obj('acl/result.json')['cleanup']['pipe_absent']
    original = read(HERE / 'verify-original.stdout.txt')
    assert original['inventory_files'] == original['git_blob_bytes_verified'] == 874 and len(original['rounds']) == 19
    first = read(HERE / 'audit-first-review.stdout.txt')
    assert first['archive_files'] == 134 and first['workers'] == 11
    pending = read(HERE / 'audit-pending-archives.stdout.txt')
    assert sum(item['worker_receipts_verified'] for item in pending) == 108
    for label in ['shutdown-diagnostic-r01', 'shutdown-diagnostic-r02',
                  'submission-interruption-r01', 'submission-interruption-r02']:
        diagnostic = read(HERE / label / 'result.json')
        diagnostic_observation, diagnostic_cleanup = diagnostic['observation'], diagnostic['cleanup']
        assert diagnostic_observation['native_still_pending'] and diagnostic_observation['event_open']
        if label.startswith('submission'):
            assert diagnostic_observation['application_pending_owner_count'] == 0
            assert len(diagnostic_observation['early_event_close_attempts']) == 1
        else:
            assert diagnostic_observation['python_atexit_reached']
            assert diagnostic_observation['application_pending_owner_count'] == 1
        assert diagnostic_cleanup['returncode'] == 96 and diagnostic_cleanup['pipe_absent']
        assert diagnostic_cleanup['held_handle_signaled'] and diagnostic_cleanup['process_handle_closed']
        if label.endswith('r02'):
            metadata = read(HERE / label / 'environment.json')
            for script, expected in metadata['harness_sha256'].items():
                assert sha((HERE / label / 'h' / script).read_bytes()) == expected
                source = HERE / script if script == 'shutdown_probe.py' else LAB / script
                assert sha(source.read_bytes()) == expected
        workers.append({'folder': label + '/', **diagnostic_cleanup})
    for path in HERE.glob('*.exit.json'):
        assert read(path)['returncode'] == 0
    all_material = [path.read_bytes() for path in HERE.rglob('*') if path.is_file()] + list(raw.values())
    assert all(not any(scan(data).values()) for data in all_material), 'sensitive-content presence detected'
    if live:
        sys.path.insert(0, str(LAB))
        import probe as p
        p.bind(p.K, 'OpenProcess', [p.W.DWORD, p.W.BOOL, p.W.DWORD], p.W.HANDLE)
        post = []
        for worker in workers:
            C.set_last_error(0)
            handle = p.K.OpenProcess(0x101000, False, worker['pid'])
            if handle:
                try:
                    observed = p.creation_time(handle)
                    signaled = p.K.WaitForSingleObject(handle, 0) == 0
                    status = {'observed_creation_time': observed, 'signaled': signaled,
                              'original_exited': observed != worker['creation_time'] or signaled}
                finally:
                    p.checked(p.K.CloseHandle(handle))
            else:
                status = {'open_error': C.get_last_error(), 'original_exited': C.get_last_error() == 87}
            assert status['original_exited']
            post.append({'folder': worker['folder'], 'actual_pid': worker['pid'],
                         'expected_creation_time': worker['creation_time'], **status})
        put('post-process-state.json', post)
    return {'merge': environment['git_head'], 'candidate': '73e63d387654316ee2a415d7e47547725caf40d9',
            'pytest': pytest, 'archive_files': len(raw), 'new_workers_with_bound_exit_receipts': len(workers),
            'original_files': 874, 'original_rounds': 19, 'first_review_files': 134,
            'first_review_workers': 11, 'pending_archive_workers': 108,
            'unconfirmed_cases': observations, 'real_os_completions': [995, 109],
            'diagnostic_exception_reaches_python_shutdown_with_pending_io': True,
            'diagnostic_injection_kept_safe_by_review_atexit_native_termination': True,
            'submission_exception_attempts_early_event_close_and_has_no_application_owner': True,
            'sensitive_value_or_shape_present': False,
            'acceptance': 'not-accepted; submission ownership gap and harness worker lacks final fail-stop'}


if __name__ == '__main__':
    result = audit(live='--capture' in sys.argv)
    if '--capture' in sys.argv:
        put('summary.json', result)
    else:
        assert result == read(HERE / 'summary.json')
    print(json.dumps({key: value for key, value in result.items() if key != 'unconfirmed_cases'}, indent=2))
