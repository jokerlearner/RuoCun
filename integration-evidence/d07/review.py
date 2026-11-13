"""D07 fresh merger reproduction; never reads private or real config material."""
from datetime import datetime, timezone
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

REPO = Path(__file__).resolve().parents[2]
HERE = REPO / '.scratch/ruocun-discovery/experiments/distribution'
OUT = Path(__file__).resolve().parent
RAW = OUT / 'raw'
ROOT = Path('C:/Users/PC/AppData/Local/Temp/RuoCun-m07-D07-中文 空格-20261105')
PY = ROOT / '构建环境/Scripts/python.exe'
CACHE = HERE / '.cache'
DLL_SHA = '4b59d3cded9dc1608544160f3b4b10ac974c6ac0d6ffc23064e5f4c8dbd05aea'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def environment():
    root = Path(os.environ.get('SystemRoot', 'C:/Windows'))
    home = ROOT / '合成HOME'
    temp = ROOT / '合成TEMP'
    for p in [home, temp, home / 'AppData/Roaming', home / 'AppData/Local']:
        p.mkdir(parents=True, exist_ok=True)
    return {'SystemRoot': str(root), 'WINDIR': str(root),
            'COMSPEC': str(root / 'System32/cmd.exe'),
            'PATH': str(root / 'System32'), 'PATHEXT': '.COM;.EXE;.BAT;.CMD',
            'HOME': str(home), 'USERPROFILE': str(home),
            'APPDATA': str(home / 'AppData/Roaming'), 'LOCALAPPDATA': str(home / 'AppData/Local'),
            'HOMEDRIVE': home.drive, 'HOMEPATH': str(home)[len(home.drive):],
            'TEMP': str(temp), 'TMP': str(temp), 'OS': 'Windows_NT',
            'PROCESSOR_ARCHITECTURE': 'AMD64', 'NUMBER_OF_PROCESSORS': '2',
            'PYTHONUTF8': '1', 'PYTHONNOUSERSITE': '1', 'PIP_DISABLE_PIP_VERSION_CHECK': '1',
            'PIP_CACHE_DIR': str(CACHE / 'pip-cache')}


def run(tag, argv, *, cwd=HERE, extra=None, expected=0, timeout=360):
    target = RAW / tag
    target.mkdir(parents=True, exist_ok=False)
    env = environment()
    env.update(extra or {})
    argv = list(map(str, argv))
    start = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=timeout)
    except OSError as exc:
        r = subprocess.CompletedProcess(argv, -getattr(exc, 'winerror', 1), b'', str(exc).encode('utf-8'))
    (target / 'stdout.bin').write_bytes(r.stdout)
    (target / 'stderr.bin').write_bytes(r.stderr)
    save(target / 'command.json', {'utc': start, 'argv': argv, 'cwd': str(cwd),
         'returncode': r.returncode, 'expected': expected, 'env_keys': sorted(env),
         'stdout_sha256': sha(target / 'stdout.bin'), 'stderr_sha256': sha(target / 'stderr.bin')})
    print(f'{tag}: exit={r.returncode}; expected={expected}', flush=True)
    assert r.returncode == expected, f'{tag}: see raw capture; values deliberately not printed'
    return r


def inputs():
    paths = [p for p in HERE.rglob('*') if p.is_file() and
             not any(part in {'.cache', '.venv', '__pycache__', 'e'} for part in p.relative_to(HERE).parts)]
    return [{'path': str(p.relative_to(REPO)), 'size': p.stat().st_size, 'sha256': sha(p)} for p in sorted(paths)]


def prepare():
    assert not ROOT.exists(), 'fresh external root required'
    assert not ROOT.resolve().is_relative_to(REPO.resolve())
    ROOT.mkdir(parents=True)
    save(OUT / 'platform.json', {'utc': datetime.now(timezone.utc).isoformat(),
         'python': sys.version, 'executable': sys.executable, 'machine': platform.machine(),
         'platform': platform.platform(), 'windows': sys.getwindowsversion()[:],
         'elevated': bool(ctypes.windll.shell32.IsUserAnAdmin()),
         'external_root': str(ROOT), 'clean_vm': False, 'host_has_python': True,
         'env_policy': 'explicit allowlist; synthetic HOME/config/TEMP; no real credentials/config read',
         'input_sha256': inputs()})
    run('00-venv', [sys.executable, '-m', 'venv', ROOT / '构建环境'])
    run('01-lock-install', [PY, '-m', 'pip', '--isolated', 'install', '--require-hashes', '-r', HERE / 'requirements.lock'])
    run('02-wheelhouse', [PY, '-m', 'pip', '--isolated', 'download', '--require-hashes', '--only-binary=:all:',
                        '-r', HERE / 'requirements.lock', '--dest', CACHE / 'wheels'])
    url = 'https://www.sqlite.org/2026/sqlite-dll-win-x64-3540100.zip'
    raw = urllib.request.urlopen(url, timeout=50).read()
    assert hashlib.sha3_256(raw).hexdigest() == 'c2d09c8babb9399277055c057c97a53f1ffd7c5f11d0c1f2118ffdfa39f2daa4'
    dll = zipfile.ZipFile(io.BytesIO(raw)).read('sqlite3.dll')
    assert hashlib.sha256(dll).hexdigest() == DLL_SHA
    native = HERE / 'pkg/src/ruocun_probe/native/sqlite3.dll'
    native.parent.mkdir(parents=True, exist_ok=True)
    native.write_bytes(dll)
    save(OUT / 'download.json', {'url': url, 'archive_sha3_256': hashlib.sha3_256(raw).hexdigest(),
         'dll_sha256': DLL_SHA, 'target': str(native), 'candidate_json_not_modified': True})


def build():
    run('03-build-sdist-wheel', [PY, '-m', 'build', '--no-isolation', HERE / 'pkg', '--outdir', CACHE / 'a3'])
    run('04-direct-wheel', [PY, '-m', 'build', '--no-isolation', '--wheel', HERE / 'pkg', '--outdir', CACHE / 'direct'])
    wheel = next((CACHE / 'a3').glob('*.whl'))
    direct = next((CACHE / 'direct').glob('*.whl'))
    assert wheel.read_bytes() == direct.read_bytes()
    with zipfile.ZipFile(wheel) as z:
        wheel_meta = z.read(next(p for p in z.namelist() if p.endswith('/WHEEL'))).decode()
        assert 'Root-Is-Purelib: false' in wheel_meta and 'Tag: py3-none-win_amd64' in wheel_meta
        assert z.read('ruocun_probe/native/sqlite3.dll') == (HERE / 'pkg/src/ruocun_probe/native/sqlite3.dll').read_bytes()
    sdist = next((CACHE / 'a3').glob('*.tar.gz'))
    with tarfile.open(sdist) as t:
        assert any(n.endswith('/src/ruocun_probe/native/sqlite3.dll') for n in t.getnames())
    source = CACHE / 'v2'
    shutil.copytree(HERE / 'pkg', source, ignore=shutil.ignore_patterns('__pycache__'))
    version = source / 'src/ruocun_probe/__init__.py'
    assert version.read_text().count('"0.0.1"') == 1
    version.write_text('__version__ = "0.0.2"\n', encoding='utf-8')
    run('05-upgrade-build', [PY, '-m', 'build', '--no-isolation', source, '--outdir', CACHE / 'u2'])
    save(OUT / 'artifacts.json', {'wheel': {'path': str(wheel), 'sha256': sha(wheel), 'size': wheel.stat().st_size,
         'metadata': wheel_meta}, 'sdist': {'path': str(sdist), 'sha256': sha(sdist), 'size': sdist.stat().st_size},
         'direct_wheel_equal': True, 'upgrade_wheel': [{'path': str(p), 'sha256': sha(p)} for p in (CACHE / 'u2').glob('*.whl')]})


def tests():
    run('06-pytest', [PY, '-m', 'pytest', '-q', '-rs', '--basetemp', ROOT / 'pytest临时'],
        extra={'D07_RECEIPTS': str(RAW / '06-pytest/receipts')})


def install():
    run('07-install-probe', [PY, HERE / 'install_probe.py', 'm07-20261105'],
        extra={'D07_RECEIPTS': str(RAW / '07-install-probe/receipts')})


def frozen():
    wheel = next((CACHE / 'a3').glob('*.whl'))
    run('08-install-builder-wheel', [PY, '-m', 'pip', '--isolated', 'install', '--no-deps', '--force-reinstall', wheel])
    target = CACHE / 'f3/中文 目录/onedir'
    run('09-build-onedir', [PY, '-m', 'PyInstaller', '--noconfirm', '--clean', '--console', '--onedir',
        '--name', 'ruocun', '--distpath', target / 'dist', '--workpath', target / 'build', '--specpath', target,
        '--collect-all', 'ruocun_probe', '--collect-all', 'prompt_toolkit', '--collect-all', 'rich', '--collect-all', 'wcwidth',
        '--copy-metadata', 'prompt_toolkit', '--copy-metadata', 'rich', '--copy-metadata', 'wcwidth', HERE / 'entry.py'])
    source = HERE / 'pkg/src/ruocun_probe/native/sqlite3.dll'
    pinned = target / 'dist/ruocun/_internal/sqlite3.dll'
    before = sha(pinned) if pinned.exists() else None
    shutil.copyfile(source, pinned)
    save(OUT / 'pin.json', {'path': str(pinned), 'before': before, 'after': sha(pinned), 'global_python_changed': False})
    run('10-standalone-probe', [PY, HERE / 'standalone_probe.py'],
        extra={'D07_RECEIPTS': str(RAW / '10-standalone-probe/receipts')})
    payload = target / 'dist/ruocun'
    save(OUT / 'onedir-manifest.json', [{'path': str(p.relative_to(payload)), 'size': p.stat().st_size,
         'sha256': sha(p)} for p in sorted(payload.rglob('*')) if p.is_file()])


def audit():
    original = json.loads((OUT / 'platform.json').read_text(encoding='utf-8'))['input_sha256']
    now = {x['path']: x for x in inputs()}
    changed = [x['path'] for x in original if now.get(x['path']) != x]
    # The ignored native DLL is a new synthetic build input, not an original tracked file.
    assert not changed, changed
    identities = []
    for p in RAW.rglob('cleanup.json'):
        for item in json.loads(p.read_text(encoding='utf-8')):
            assert item['exit'] == 0
            identities.append(item['identity'])
    unique = {json.dumps(i, sort_keys=True) for i in identities}
    assert len(unique) == 12
    historical = []
    for tag in ['n', 'i3', 's3', 'r5c', 'g5']:
        folder = HERE / 'e' / tag
        record = json.loads((folder / 'run.json').read_text(encoding='utf-8'))
        assert sha(folder / 'out.bin') == record['stdout_sha256']
        assert sha(folder / 'err.bin') == record['stderr_sha256']
        for item in record['inputs']:
            snapshot = folder / item['snapshot']
            assert snapshot.stat().st_size == item['size'] and sha(snapshot) == item['sha256']
        historical.append({'tag': tag, 'returncode': record['returncode'],
                           'expected': record['expected'], 'raw_hashes_verified': True,
                           'input_snapshots_verified': len(record['inputs'])})
    base = REPO / '.scratch/ruocun-discovery/reference/dao-f17e189-7ac654a0dc06'
    manifest = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))
    records = json.loads((HERE / 'sources/frozen.json').read_text(encoding='utf-8'))
    by_path = {x['path']: x for x in manifest['files']}
    with zipfile.ZipFile(base / 'source.zip') as archive:
        for item in records['selected_source_members_verified']:
            raw = archive.read(item['path'])
            assert hashlib.sha256(raw).hexdigest() == item['sha256'] == by_path[item['path']]['sha256']
    save(OUT / 'historical.json', {'records': historical, 'source_members_verified': 6,
         'original_r5_stdout': 'explicit redacted review copy; private payload never read',
         'g5': 'real corrected onefile WinError4551 remains ENV; not green or retried'})
    # Silently scan current sensitive environment values. Never print keys or values.
    secrets = [v.encode('utf-8') for k, v in os.environ.items()
               if re.search(r'(TOKEN|SECRET|PASSWORD|API_KEY|AUTH)', k, re.I) and len(v) >= 8]
    scanned = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'scan.json']
    scanned += [p for p in (HERE / 'e').rglob('*') if p.is_file()]
    matches = sum(any(v in p.read_bytes() for v in secrets) for p in scanned)
    git = shutil.which('git')
    assert git and Path(git).is_absolute()
    rows = subprocess.check_output([git, 'ls-files', '--stage', '-z', '--',
        str(HERE.relative_to(REPO)), 'integration-evidence/d07'], cwd=REPO, env=environment()).split(b'\0')
    entries = []
    for row in rows:
        if row:
            fields, path = row.split(b'\t', 1)
            entries.append((path.decode('utf-8'), fields.split()[1].decode()))
    ids = list(dict.fromkeys(oid for _, oid in entries))
    batch = subprocess.check_output([git, 'cat-file', '--batch'], cwd=REPO, env=environment(),
                                   input=('\n'.join(ids) + '\n').encode())
    position, blobs = 0, {}
    for oid in ids:
        end = batch.index(b'\n', position)
        header = batch[position:end].split()
        assert header[0].decode() == oid and header[1] == b'blob'
        size = int(header[2])
        blobs[oid] = batch[end + 1:end + 1 + size]
        assert batch[end + 1 + size:end + 2 + size] == b'\n'
        position = end + size + 2
    assert position == len(batch)
    for path, oid in entries:
        assert blobs[oid] == (REPO / path).read_bytes(), 'staged/worktree bytes mismatch'
        assert '/.cache/' not in path and 'dpapi.bin' not in path
        assert not any(value in blobs[oid] for value in secrets), 'sensitive match; values omitted'
    save(OUT / 'scan.json', {'sensitive_values_present': bool(secrets), 'match_present': bool(matches),
         'values_or_names_recorded': False, 'files_scanned': len(scanned),
         'indexed_files_verified': len(entries), 'indexed_blob_bytes_equal': True,
         'original_inputs_unchanged': not changed, 'unique_held_runtime_identities': len(unique),
         'all_held_runtime_exits_zero': True, 'private_material_read': False,
         'onefile_retried': False})
    assert matches == 0
    print('audit: original inputs unchanged; 12 held runtime identities exited; secret scan match=False')


def archive():
    # Archive only this merger's new raw captures; originals remain untouched.
    paths = sorted(p for p in RAW.rglob('*') if p.is_file())
    target = OUT / 'raw.zip'
    assert not target.exists()
    records = [{'path': p.relative_to(RAW).as_posix(), 'size': p.stat().st_size,
                'sha256': sha(p)} for p in paths]
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in paths:
            archive.write(p, p.relative_to(RAW).as_posix())
    with zipfile.ZipFile(target) as archive:
        assert sorted(archive.namelist()) == sorted(x['path'] for x in records)
        for item in records:
            raw = archive.read(item['path'])
            assert len(raw) == item['size'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    save(OUT / 'raw-manifest.json', {'archive_sha256': sha(target), 'archive_size': target.stat().st_size,
         'members': records, 'source_raw_retained_locally': True, 'original_candidate_evidence_unchanged': True})
    buffer = ctypes.create_string_buffer(64)
    ctypes.windll.kernel32.GetNativeSystemInfo(buffer)
    native_arch = int.from_bytes(buffer.raw[:2], 'little')
    assert native_arch == 9
    save(OUT / 'native-platform.json', {'GetNativeSystemInfo_wProcessorArchitecture': native_arch,
         'architecture_name': 'PROCESSOR_ARCHITECTURE_AMD64',
         'pointer_bits': ctypes.sizeof(ctypes.c_void_p) * 8,
         'platform_machine_empty_in_bootstrap': True,
         'interpretation': 'bootstrap platform.machine() empty; native Windows API supplies OS architecture'})
    frozen = json.loads((RAW / '10-standalone-probe/receipts/summary.json').read_text(encoding='utf-8'))
    commands = [{'argv': [frozen['binary'], *item['args']], 'cwd': frozen['cwd'],
                 'returncode': item['returncode']} for item in frozen['cli_cases']]
    for folder in sorted((RAW / '10-standalone-probe/receipts').glob('p*')):
        owner = json.loads((folder / 'owner.json').read_text(encoding='utf-8'))
        child = owner['command']
        commands.append({'argv': [frozen['binary'], '--owner', '--out', str(folder),
                          '--child-role', owner['child']['role']], 'cwd': frozen['cwd'],
                         'child_argv_recorded_by_owner': child,
                         'runtime_cleanup': json.loads((folder / 'cleanup.json').read_text(encoding='utf-8'))})
    save(OUT / 'frozen-argv.json', {'derivation': 'exact executable + case args and lifecycle.py owner invocation; child argv from runtime receipt',
         'commands': commands})
    print(f'archive: {len(records)} verified members; local raw retained; no process/cache deletion requested')


def sync():
    git = shutil.which('git')
    assert git and Path(git).is_absolute()
    def read(*args):
        return subprocess.check_output([git, *args], cwd=REPO, env=environment()).decode('utf-8').strip()
    accepted = '4048910744a7aab60a9bc75d721df9262a403292'
    reviewed = 'c00ce418083cabbedea9f0de7efeb4f7f76bff6d'
    current = read('rev-parse', 'HEAD')
    relevant = [str(HERE.relative_to(REPO)), 'integration-evidence/d07']
    assert not read('diff', '--name-only', reviewed, current, '--', *relevant)
    assert subprocess.run([git, 'merge-base', '--is-ancestor', accepted, current],
                          cwd=REPO, env=environment(), capture_output=True).returncode == 0
    paths = read('ls-files', '-z', '--', *relevant).split('\0')
    maximum = max(len(path) for path in paths if path)
    assert maximum <= 150
    save(OUT / 'sync.json', {'root_integration': accepted, 'review_evidence_commit': reviewed,
         'synchronization_merge': current, 'root_tip_is_ancestor': True,
         'd07_source_and_committed_evidence_diff': [], 'max_relevant_relative_path_length': maximum,
         'business_chain_rerun': False, 'reason': 'D17/root status material does not touch D07 inputs; reuse passed chain',
         'source_and_raw_bytes_unchanged': True})
    print('sync: root D17 tip merged; no relevant input/evidence delta; paths <=150; no business rerun')


if __name__ == '__main__':
    {'prepare': prepare, 'build': build, 'tests': tests, 'install': install, 'frozen': frozen,
     'audit': audit, 'archive': archive, 'sync': sync}[sys.argv[1]]()
