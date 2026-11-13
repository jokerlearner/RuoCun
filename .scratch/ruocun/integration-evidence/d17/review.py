"""Independent D17 replay: immutable original bytes, explicit child environment."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import zipfile

REPO = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file())
ORIGINAL = REPO / '.scratch/ruocun-discovery/experiments/windows'
EVIDENCE = Path(__file__).resolve().parent
POLICY = r'''
import os as _d17_os
import sys as _d17_sys
def _d17_safe_env():
    names = ('SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','HOMEDRIVE','HOMEPATH','LOCALAPPDATA','APPDATA','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','COMSPEC','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE','PATHEXT','USERNAME','USERDOMAIN')
    result = {name: _d17_os.environ[name] for name in names if name in _d17_os.environ}
    result['PATH'] = _d17_os.pathsep.join((_d17_os.path.dirname(_d17_sys.executable), _d17_sys.base_prefix, r'C:\Windows\System32', r'C:\Windows', r'D:\study_software\Git\cmd'))
    result['PYTHONIOENCODING'] = 'utf-8'
    result['PYTHONDONTWRITEBYTECODE'] = '1'
    result['HOME'] = _d17_os.environ.get('HOME', _d17_os.path.join(_d17_sys.prefix, '.d17-home'))
    for name, child in [('XDG_CONFIG_HOME','config'), ('XDG_DATA_HOME','data'), ('XDG_CACHE_HOME','cache')]:
        result[name] = _d17_os.path.join(result['HOME'], child)
    return result
'''
exec(POLICY)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(source):
    changes = {}
    for original in ORIGINAL.glob('*.py'):
        if original.name != 'task.py':
            shutil.copyfile(original, source / original.name)
            changes[original.name] = {'original_sha256': digest(original), 'executed_sha256': digest(source / original.name), 'byte_identical': True}
            continue
        text = original.read_text('utf-8')
        # ExecAction has no per-action environment parameter. Scrub before worker imports.
        # Preserve the entire original byte tail, including its LF line endings.
        prefix = POLICY + '\n_d17_environment = _d17_safe_env()\n_d17_os.environ.clear()\n_d17_os.environ.update(_d17_environment)\n'
        (source / original.name).write_bytes(prefix.encode('utf-8') + original.read_bytes())
        changes[original.name] = {'original_sha256': digest(original), 'executed_sha256': digest(source / original.name), 'byte_identical': False}
        import difflib
        (source / 'task-environment.diff').write_bytes(''.join(difflib.unified_diff(original.read_bytes().decode('utf-8').splitlines(True), (source / original.name).read_bytes().decode('utf-8').splitlines(True), fromfile='original/task.py', tofile='executed/task.py')).encode('utf-8'))
    assert digest(source / 'test_win.py') == digest(ORIGINAL / 'test_win.py')
    save(source / 'environment-adaptation.json', {'test_assertions_byte_identical': True, 'changes': changes,
        'scope': 'Parent process receives explicit allowlist; original subprocess/native calls inherit that already clean environment. Only scheduled task.py has an early environment scrub because ExecAction accepts no environment parameter. No test assertions or capability logic changed.'})
    shutil.copyfile(EVIDENCE / 'audit_conftest.py', source / 'conftest.py')


def main():
    tag = 'm17' + uuid.uuid4().hex[:10]
    root = ORIGINAL / 'run' / tag
    root.mkdir(parents=True, exist_ok=False)
    source = root / 'safe-source'
    source.mkdir()
    prepare(source)
    command = [sys.executable, '-m', 'pytest', str(source / 'test_win.py'), '-q',
               '--basetemp=' + str(root / 'pytest'), '-o', 'cache_dir=' + str(root / 'pytest-cache')]
    before = {'candidate_manifest_entries': 0, 'candidate_manifest_mismatches': []}
    manifest = json.loads((ORIGINAL / 'manifest.json').read_text('utf-8'))
    for name, expected in manifest['files'].items():
        before['candidate_manifest_entries'] += 1
        if digest(ORIGINAL / name) != expected:
            before['candidate_manifest_mismatches'].append(name)
    save(root / 'before.json', before)
    started = time.time()
    result = subprocess.run(command, cwd=REPO, env=_d17_safe_env(), capture_output=True, timeout=240)
    (root / 'pytest.txt').write_bytes(result.stdout + result.stderr)
    save(root / 'command.json', {'argv': command, 'cwd': str(REPO), 'exit': result.returncode,
        'elapsed_seconds': time.time() - started, 'environment_policy': 'explicit allowlist',
        'allowed_names': sorted(_d17_safe_env()), 'environment_values_saved': False,
        'source': str(source), 'base_prefix': sys.base_prefix, 'python': sys.version,
        'dependencies': {p: importlib.metadata.version(p) for p in ['pytest','pywin32','Pillow']}})
    after = {name: digest(ORIGINAL / name) for name in manifest['files']}
    save(root / 'original-byte-audit.json', {'entries': len(after), 'mismatches': [name for name, actual in after.items() if actual != manifest['files'][name]]})
    # Runtime fixtures may contain synthetic credential fallback material; retain only raw reports.
    selected = []
    for path in root.rglob('*'):
        if not path.is_file() or 'rt' in path.relative_to(root).parts:
            continue
        rel = path.relative_to(root)
        if rel.parts[0] == 'safe-source' or path.name in {'pytest.txt','command.json','before.json','original-byte-audit.json','native-object-audit.json','native-object-journal.json'} or path.name in {'cred.json','power.json','powercfg.txt','isolate.json','schedule.json','sched-limits.json','clipboard.json','clipboard-worker.txt','notify.json','task.xml','task-final.xml','task-created.xml','task-before.xml'} or path.name.startswith('receipt-'):
            selected.append(path)
    archive = EVIDENCE / (tag + '.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(selected):
            z.write(path, path.relative_to(root).as_posix())
    save(EVIDENCE / (tag + '-manifest.json'), {'tag': tag, 'archive': archive.name, 'archive_sha256': digest(archive),
        'files': {p.relative_to(root).as_posix(): digest(p) for p in sorted(selected)}, 'runtime_root': str(root),
        'test_exit': result.returncode})
    print(result.stdout.decode('utf-8','replace'))
    print(result.stderr.decode('utf-8','replace'))
    print(json.dumps({'tag': tag, 'test_exit': result.returncode, 'runtime_root': str(root), 'archive': str(archive)}))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
