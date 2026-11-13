"""One independent original D20 suite; original assets and assertions stay read-only."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
import winreg
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = next(p for p in ROOT.parents if (p / 'AGENTS.md').is_file())
SOURCE = REPO / '.scratch/ruocun-discovery/experiments/psec'
CACHE = Path(r'D:\java supplement\Firstcode\RuoCun\.worktrees\reference-mxc-f4aa3fd')
sys.path.insert(0, str(SOURCE))
import psec
import acl


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def walk(root):
    """Never follow a junction left by a failed fixture."""
    for item in sorted(root.iterdir()):
        if item.lstat().st_file_attributes & 0x400:
            continue
        if item.is_dir():
            yield from walk(item)
        elif item.is_file():
            yield item


out = ROOT / 'r1'
out.mkdir(exist_ok=False)
runtime = ROOT / '.r/r1'
runtime.mkdir(exist_ok=False)
(runtime / 'tmp').mkdir()
env = psec.safe_env(runtime)
env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
tracked = subprocess.check_output([r'D:\study_software\Git\cmd\git.exe', '-C', str(REPO), 'ls-files', '-z', '--', str(SOURCE)], env=env)
assets = [REPO / value.decode('utf-8') for value in tracked.split(b'\0') if value]
before = {p.relative_to(SOURCE).as_posix(): digest(p) for p in assets}
checks = []
manifest = json.loads((SOURCE / 'manifest.json').read_text('utf-8'))
for row in manifest:
    target = SOURCE / row['path']
    checks.append(target.stat().st_size == row['bytes'] and digest(target) == row['sha256'])
for path in sorted((SOURCE / 'e').glob('*/run.json')):
    info = json.loads(path.read_text('utf-8'))
    checks.extend([digest(path.parent / 'bytes.zip') == info['archive_sha256'], digest(path.parent / 'pytest.txt') == info['raw_sha256']])
    with zipfile.ZipFile(path.parent / 'bytes.zip') as archive:
        for name, expected in info['source_sha256'].items():
            checks.append(hashlib.sha256(archive.read('code/' + name)).hexdigest() == expected)
download = json.loads((SOURCE / 'source/download.json').read_text('utf-8'))
checks.extend(digest(SOURCE / 'source' / Path(row['path']).name) == row['sha256'] for row in download['files'])
abi_source = CACHE / 'src/mxc-sdk/src/backends/process_container/common/secenv.rs'
abi_hash = digest(abi_source)
checks.append(abi_hash == '2bc998c58eb50c6f4a2913197ac3d5b7245a78c34e1e9ebe52a21908b4eacb09')
original_final = json.loads((SOURCE / 'e/final2/run.json').read_text('utf-8'))
checks.extend(digest(SOURCE / name) == expected for name, expected in original_final['source_sha256'].items())
save(out / 'before.json', {'assets': before, 'asset_count': len(assets), 'manifest_count': len(manifest), 'all_original_hashes_match': all(checks), 'abi_source_sha256': abi_hash})
if not all(checks) or len(assets) != 75:
    raise RuntimeError('original candidate byte verification failed')

cmd = [sys.executable, '-I', '-m', 'pytest', str(SOURCE / 'test_psec.py'), '-q', '-rA', '--tb=short', '-p', 'no:cacheprovider', '--basetemp=' + str(runtime / 'cases')]
info = {'command': cmd, 'cwd': str(REPO), 'environment_keys': sorted(env), 'python': sys.version, 'platform': platform.platform(),
        'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
        'source_sha256': original_final['source_sha256'], 'original_candidate_assets': len(assets),
        'abi_bytes': {k.__name__: C.sizeof(k) for k in (psec.StartupInfo, psec.StartupEx, psec.ProcessInfo, psec.BasicLimit, psec.ExtendedLimit, psec.Accounting)}}
advapi = C.WinDLL('advapi32', use_last_error=True, winmode=0x800)
get_current = psec.bind(psec.kernel, 'GetCurrentProcess', W.HANDLE, [])
open_token = psec.bind(advapi, 'OpenProcessToken', W.BOOL, [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)])
get_token = psec.bind(advapi, 'GetTokenInformation', W.BOOL, [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)])
token, elevated, size = W.HANDLE(), W.DWORD(), W.DWORD()
if not open_token(get_current(), 8, C.byref(token)):
    raise C.WinError(C.get_last_error())
try:
    if not get_token(token, 20, C.byref(elevated), C.sizeof(elevated), C.byref(size)):
        raise C.WinError(C.get_last_error())
    info['controller_token_elevated'] = bool(elevated.value)
finally:
    psec.close(token)
if elevated.value:
    raise RuntimeError('ordinary-user evidence requires a non-elevated controller')
info['binary_sha256'] = {str(p): digest(p) for p in (Path(sys._base_executable), Path(r'C:\Windows\System32\processmodel.dll'), Path(r'D:\study_software\Git\cmd\git.exe'), Path(r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'))}
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion') as key:
    info['os'] = {k: winreg.QueryValueEx(key, k)[0] for k in ('CurrentBuildNumber', 'UBR', 'EditionID', 'DisplayVersion')}
save(out / 'command.json', info)
start = time.monotonic()
with (out / 'pytest.stdout').open('xb') as stdout, (out / 'pytest.stderr').open('xb') as stderr:
    result = subprocess.run(cmd, cwd=REPO, env=env, stdout=stdout, stderr=stderr, timeout=180, creationflags=0x8000000)
info.update(exitcode=result.returncode, elapsed_seconds=time.monotonic() - start,
            stdout_sha256=digest(out / 'pytest.stdout'), stderr_sha256=digest(out / 'pytest.stderr'))
save(out / 'run.json', info)

# Read-only fresh audit, independent of the original audit.py's old runtime root.
paths = list(walk(runtime))
identities, jobs = {}, set()
def inspect(value):
    if isinstance(value, dict):
        if isinstance(value.get('pid'), int) and isinstance(value.get('creation_filetime'), int):
            identities[(value['pid'], value['creation_filetime'])] = {'pid': value['pid'], 'creation_filetime': value['creation_filetime']}
        if isinstance(value.get('job_name'), str):
            jobs.add(value['job_name'])
        for child in value.values():
            inspect(child)
    elif isinstance(value, list):
        for child in value:
            inspect(child)
for path in paths:
    if path.suffix == '.json':
        inspect(json.loads(path.read_text('utf-8')))
audit = {'processes': [], 'jobs': [], 'dacl_samples': [], 'junctions': [], 'environment_owner_crash_server_teardown': 'not-independently-queryable'}
for (pid, created), expected in sorted(identities.items()):
    C.set_last_error(0)
    handle = psec.open_process(0x100000 | 0x1000, False, pid)
    row = dict(expected)
    if not handle:
        code = C.get_last_error()
        row.update(open_error=code, recorded_identity_exited=code == 87)
    else:
        try:
            observed = psec.identity(handle, pid)
            signaled = psec.wait(handle, 0) == 0
            row.update(current_creation_filetime=observed['creation_filetime'], signaled=signaled, recorded_identity_exited=signaled or observed['creation_filetime'] != created)
        finally:
            psec.close(handle)
    audit['processes'].append(row)
for name in sorted(jobs):
    C.set_last_error(0)
    handle = psec.open_job(4, False, name)
    code = C.get_last_error()
    audit['jobs'].append({'name': name, 'open_error': code, 'absent': not handle and code == 2})
    if handle:
        psec.close(handle)
for path in paths:
    if path.name == 'config.json' and path.parent.name == 'workspace':
        cfg = json.loads(path.read_text('utf-8'))
        if cfg['acl_confirm']:
            for target in sorted((path.parent.parent / 'outside').glob('write_dac*.txt')):
                audit['dacl_samples'].append({'path': target.relative_to(runtime).as_posix(), 'random_read_ace_absent': cfg['random_sid'] not in acl.snapshot(target)})
            report = json.loads((path.parent.parent / 'result.json').read_text('utf-8'))
            audit['original_dacl_restored_and_read_back'] = report['acl_confirmation']['original_restored_and_read_back'] and report['cleanup']['original_dacl_restored']
        if cfg['files']:
            jump = path.parent / 'jump'
            audit['junctions'].append({'path': str(jump), 'absent': not jump.exists() and not jump.is_symlink(), 'outside_target_retained': (path.parent.parent / 'outside').is_dir()})
audit['all_recorded_identities_exited'] = bool(identities) and all(row['recorded_identity_exited'] for row in audit['processes'])
audit['all_exact_jobs_absent'] = bool(jobs) and all(row['absent'] for row in audit['jobs'])
audit['all_sampled_random_aces_absent'] = bool(audit['dacl_samples']) and all(row['random_read_ace_absent'] for row in audit['dacl_samples'])
audit['all_owned_junctions_absent_target_retained'] = bool(audit['junctions']) and all(row['absent'] and row['outside_target_retained'] for row in audit['junctions'])
save(out / 'post-audit.json', audit)
after = {p.relative_to(SOURCE).as_posix(): digest(p) for p in assets}
save(out / 'after.json', {'all_75_original_assets_unchanged': before == after, 'assets': after})
with zipfile.ZipFile(out / 'bytes.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in assets:
        archive.write(path, 'candidate/' + path.relative_to(SOURCE).as_posix())
    archive.write(abi_source, 'source/secenv.rs')
    for path in paths:
        archive.write(path, 'run/' + path.relative_to(runtime).as_posix())
    for name in ('review.py', 'safe-launch.ps1'):
        archive.write(ROOT / name, 'review/' + name)
with zipfile.ZipFile(out / 'bytes.zip') as archive:
    members = [{'path': name, 'bytes': len(archive.read(name)), 'sha256': hashlib.sha256(archive.read(name)).hexdigest()} for name in archive.namelist()]
save(out / 'archive-manifest.json', {'archive_sha256': digest(out / 'bytes.zip'), 'members': members})
summary = {'pytest_exitcode': result.returncode, 'all_original_hash_checks_match': all(checks), 'all_75_original_assets_unchanged': before == after,
           'full_backend_contract_met': False, 'known_failure': 'outside RO permits WRITE_DAC and actual random SID read ACE mutation',
           'owner_crash_psec_server_teardown': 'not-independently-queryable', 'archive_sha256': digest(out / 'bytes.zip'),
           'audit_passed': all(audit[k] for k in audit if k.startswith('all_')) and audit.get('original_dacl_restored_and_read_back') is True}
save(out / 'summary.json', summary)
print(json.dumps(summary))
sys.exit(0 if result.returncode == 0 and summary['audit_passed'] and before == after else 1)
