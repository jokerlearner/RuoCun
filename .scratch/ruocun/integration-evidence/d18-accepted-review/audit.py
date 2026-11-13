"""Read-only final review of original bytes, ownership, real completion and exit evidence."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import re
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LAB = ROOT / '.scratch/ruocun-discovery/experiments/durable-io'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def put(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def os_check(workers):
    native = C.WinDLL('kernel32', use_last_error=True)
    native.OpenProcess.argtypes, native.OpenProcess.restype = [W.DWORD, W.BOOL, W.DWORD], W.HANDLE
    native.GetProcessTimes.argtypes = [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4
    native.WaitForSingleObject.argtypes, native.WaitForSingleObject.restype = [W.HANDLE, W.DWORD], W.DWORD
    native.CloseHandle.argtypes = [W.HANDLE]
    states = []
    for worker in workers:
        C.set_last_error(0)
        handle = native.OpenProcess(0x101000, False, worker['pid'])
        if handle:
            try:
                times = [W.FILETIME() for _ in range(4)]
                assert native.GetProcessTimes(handle, *[C.byref(item) for item in times])
                observed = str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
                signaled = native.WaitForSingleObject(handle, 0) == 0
                status = {'observed_creation_time': observed, 'signaled': signaled,
                          'original_exited': observed != worker['creation_time'] or signaled}
            finally:
                assert native.CloseHandle(handle)
        else:
            error = C.get_last_error()
            status = {'open_error': error, 'original_exited': error == 87}
        assert status['original_exited']
        states.append({'folder': worker['folder'], 'pid': worker['pid'],
                       'expected_creation_time': worker['creation_time'], **status})
    return states


def audit(capture=False):
    inventory = HERE / 'evidence-sha256.json'
    if inventory.exists():
        for name, expected in read('evidence-sha256.json').items():
            assert sha((HERE / name).read_bytes()) == expected, name
    manifest = read('round-manifest.json')
    archive = HERE / manifest['archive']
    assert sha(archive.read_bytes()) == manifest['archive_sha256']
    with zipfile.ZipFile(archive) as zipped:
        assert set(zipped.namelist()) == set(manifest['files'])
        raw = {name: zipped.read(name) for name in zipped.namelist()}
    assert all(sha(data) == manifest['files'][name] for name, data in raw.items())
    prefix = 'm18q-independent-r01/'
    members = {name.removeprefix(prefix): data for name, data in raw.items()}
    obj = lambda name: json.loads(members[name])
    env = obj('environment.json')
    assert env['git_head'] == 'd719be86b5d768270620dedc7d8db9ed870ff35e'
    assert obj('exit.json')['returncode'] == 0
    pytest = re.search(rb'(18 passed in [0-9.]+s)', members['stdout.txt']).group(1).decode()
    for script, expected in env['harness_sha256'].items():
        assert sha(members['h/' + script]) == expected
        assert sha((LAB / script).read_bytes()) == expected
    assert len(env['harness_sha256']) == 7
    workers = []
    for name in members:
        if not name.endswith('/process.json'):
            continue
        folder = name.removesuffix('process.json')
        process, ready, cleanup = [obj(folder + suffix) for suffix in ['process.json', 'ready.json', 'cleanup.json']]
        identity = (process['pid'], process['creation_time'])
        assert identity == (ready['pid'], ready['creation_time']) == (cleanup['pid'], cleanup['creation_time'])
        assert cleanup['same_creation_time'] and cleanup['held_handle_signaled'] and cleanup['process_handle_closed']
        if 'pending_reclaimed_by_os_after_process_exit' in cleanup:
            assert cleanup['pipe_absent'] and not cleanup['forced']
            if cleanup['returncode'] == 96:
                assert cleanup['pending_reclaimed_by_os_after_process_exit']
        if folder + 'kill.json' in members:
            kill = obj(folder + 'kill.json')
            assert identity == (kill['pid'], kill['creation_time'])
            assert kill['requested_on_held_handle'] and kill['wait_signaled']
        workers.append({'folder': folder, **cleanup})
    assert len(workers) == 23
    for mode in ['cancel-fail', 'cancel-budget', 'wait-fail', 'wait-raise', 'result-incomplete',
                 'result-error', 'read-cancel-fail', 'write-cancel-fail', 'submit-raise']:
        result = obj(mode + '/result.json')
        observation, cleanup = result['observation'], result['cleanup']
        assert observation['owner_retained'] and observation['native_still_pending'] and observation['event_open']
        assert not observation['early_event_close_attempts'] and observation['poisoned_process_reuse_blocked']
        assert observation['error']['type'] == 'PendingIoUnconfirmed'
        assert cleanup['returncode'] == 96 and not cleanup['forced']
        assert cleanup['pending_reclaimed_by_os_after_process_exit'] and cleanup['pipe_absent']
    submission = obj('submit-raise/result.json')['observation']['injections']
    assert submission == [{'api': 'ConnectNamedPipe-return-boundary', 'native_called': True,
        'native_return': False, 'native_winerror': 997, 'injected_exception': 'SubmissionBoundaryInterruption'}]
    diagnostic = obj('diagnostic-fail/result.json')
    assert diagnostic['diagnostic']['application_owner_count'] == 1
    assert diagnostic['diagnostic']['native_still_pending'] and diagnostic['diagnostic']['event_open']
    assert not diagnostic['python_atexit_reached'] and not diagnostic['target_entry_returned_with_pending']
    assert diagnostic['cleanup']['returncode'] == 96 and diagnostic['cleanup']['pipe_absent']
    for mode, error, status in [('cancel-completed', 995, 0xc0000120), ('broken-read', 109, 0xc000014b)]:
        result = obj(mode + '/result.json')
        observation = result['observation']
        assert not observation['injections'] and not observation['owner_retained']
        assert observation['completion_records'][-1]['confirmed']
        assert observation['completion_records'][-1]['winerror'] == error
        assert observation['completion_records'][-1]['native_status'] == status
        assert result['cleanup']['returncode'] == 0 and result['cleanup']['pipe_absent']
    assert obj('acl/result.json')['cleanup']['pipe_absent']
    assert obj('pipe/result.json')['pipe_absent']
    original = read('verify-original.stdout.txt')
    assert original['inventory_files'] == original['git_blob_bytes_verified'] == 874
    assert len(original['rounds']) == 19
    assert read('audit-first.stdout.txt')['archive_files'] == 134
    assert sum(item['worker_receipts_verified'] for item in read('audit-pending.stdout.txt')) == 108
    assert sum(item['worker_receipts_verified'] for item in read('audit-final-fix.stdout.txt')) == 96
    assert read('audit-old-review-on-current.exit.json')['returncode'] == 1
    assert b'assert sha((LAB / script).read_bytes()) == expected' in (HERE / 'audit-old-review-on-current.stderr.txt').read_bytes()
    assert read('audit-old-review-historical-view.exit.json')['returncode'] == 0
    assert read('audit-old-review-historical-view.stdout.txt')['new_workers_with_bound_exit_receipts'] == 25
    for path in HERE.glob('*.exit.json'):
        assert json.loads(path.read_text())['returncode'] == (1 if path.name == 'audit-old-review-on-current.exit.json' else 0)
    if capture:
        put('post-process-state.json', os_check(workers))
    else:
        assert len(read('post-process-state.json')) == 23
        assert all(item['original_exited'] for item in read('post-process-state.json'))
    result = {'merge': env['git_head'], 'candidate': '1860c70ad6109dbd09ac80ac7a2a118d77818012',
        'pytest': pytest, 'archive_files': len(raw), 'workers_bound_to_pid_creation_and_held_handle': 23,
        'unconfirmed_ownership_cases': 9, 'diagnostic_entry_guard_cases': 1,
        'real_os_completion_errors': [995, 109], 'original_files': 874, 'original_rounds': 19,
        'first_review_archive_files': 134, 'pending_archive_worker_receipts': 108,
        'final_fix_archive_worker_receipts': 96, 'old_review_worker_receipts': 25,
        'old_review_rejected_current_source_as_expected': True,
        'old_review_passed_exact_historical_source_view': True,
        'acceptance': 'D18 standalone experiment technical correction accepted; product and final acceptance pending'}
    if capture:
        put('summary.json', result)
    else:
        assert result == read('summary.json')
    return result


if __name__ == '__main__':
    print(json.dumps(audit('--capture' in sys.argv), indent=2))
