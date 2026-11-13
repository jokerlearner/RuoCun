"""Supplement the completed round with independent pipe-open and final-sync checks."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import json
import subprocess
import sys
import zipfile
import review

HERE, ROOT, LAB = review.HERE, review.ROOT, review.LAB


def git(*arguments):
    return subprocess.check_output(['git', *arguments], cwd=ROOT, env=review.child_env()).decode().strip()


def main():
    with zipfile.ZipFile(HERE / review.json.loads((HERE / 'round-manifest.json').read_text())['archive']) as zipped:
        members = {name.removeprefix('m18q-independent-r01/'): zipped.read(name) for name in zipped.namelist()}
    obj = lambda name: json.loads(members[name])
    endpoints = {}
    for name in members:
        if name.endswith('/ready.json'):
            ready = obj(name)
            pipe_name = ready.get('pipe_name') or ready.get('name')
            if pipe_name and pipe_name.startswith('\\\\.\\pipe\\'):
                endpoints[name] = pipe_name
    endpoints['acl/result.json'] = obj('acl/result.json')['pipe_name']
    assert len(endpoints) == 14
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    results = []
    for source, pipe_name in endpoints.items():
        C.set_last_error(0)
        handle = kernel.CreateFileW(pipe_name, 0x12019b, 7, None, 3, 0, None)
        error = C.get_last_error()
        success = handle != C.c_void_p(-1).value
        if success:
            assert kernel.CloseHandle(handle)
        results.append({'source': source, 'pipe_name': pipe_name, 'success': success, 'winerror': error})
        assert not success and error == 2
    review.put('post-pipe-state.json', {'independent_native_api': 'CreateFileW',
        'access': 'read/write data and attributes; excludes FILE_CREATE_PIPE_INSTANCE',
        'all_14_pipe_names_absent_error_2': True, 'endpoints': results})
    relevant = ['.scratch/ruocun-discovery/experiments/durable-io',
        '.scratch/ruocun/integration-evidence/d18', '.scratch/ruocun/integration-evidence/d18p',
        '.scratch/ruocun/integration-evidence/d18-final-review', '.scratch/ruocun/integration-evidence/d18q']
    before = 'd719be86b5d768270620dedc7d8db9ed870ff35e'
    final = git('rev-parse', 'HEAD')
    formal = git('rev-parse', 'integration/ruocun-migration')
    related = git('diff', '--name-only', before, final, '--', *relevant).splitlines()
    assert not related
    assert formal == 'cc90a65fa38604a0d5ac3ff92889e2321df5a00f'
    assert subprocess.run(['git', 'merge-base', '--is-ancestor', formal, 'HEAD'], cwd=ROOT,
                          env=review.child_env(), capture_output=True).returncode == 0
    hashes = obj('environment.json')['harness_sha256']
    assert all(review.sha((LAB / name).read_bytes()) == expected for name, expected in hashes.items())
    original_paths = [LAB.relative_to(ROOT).as_posix() + '/raw', LAB.relative_to(ROOT).as_posix() + '/raw-sha256.json', *relevant[1:]]
    history_changed = git('diff', '--name-only', '1860c70ad6109dbd09ac80ac7a2a118d77818012', 'HEAD', '--', *original_paths).splitlines()
    assert not history_changed
    review.put('sync-check.json', {'tested_merge': before, 'formal_tip': formal, 'synced_merge': final,
        'relevant_paths_changed': related, 'candidate_history_paths_changed': history_changed,
        'tested_7_script_sha256_still_match': hashes, 'unrelated_native_experiments_rerun': False})
    crash = obj('crash/result.json')
    pipe = obj('pipe/result.json')
    review.put('facts.json', {'power_loss_tested': False,
        'publish_path_receipts': {name: value['receipt'] for name, value in obj('paths/result.json')['paths'].items()},
        'cold_reads': {name: crash[name]['cold_read']['receipt'] for name in ['before-replace', 'after-replace']},
        'concurrent_readers': {name: {key: item[key] for key in ['reads', 'versions', 'malformed', 'open_errors']}
            for name, item in crash['observers'].items()},
        'server_events_opened': pipe['server']['events_opened'],
        'server_events_closed': pipe['server']['events_closed'],
        'anonymous_attempts': obj('acl/result.json')['anonymous_attempt'],
        'independent_account': obj('acl/result.json')['independent_account']})
    python = Path(json.loads((HERE / 'setup.json').read_text())['venv']) / 'Scripts/python.exe'
    assert review.run('audit-readonly-after-sync', [python, HERE / 'audit.py']).returncode == 0
    print(json.dumps({'independent_pipe_opens': 14, 'all_error_2': True,
                      'synced_merge': final, 'relevant_paths_changed': 0}))


if __name__ == '__main__':
    main()
