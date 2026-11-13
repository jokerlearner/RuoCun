"""Independent final D18 collection; all launched children use a synthetic environment."""
from pathlib import Path
import datetime
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LAB = ROOT / '.scratch/ruocun-discovery/experiments/durable-io'
sys.path.insert(0, str(LAB))
from safe_env import child_env


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def scan(data):
    # The PowerShell parent separately compares real sensitive environment values.
    return bool(re.search(rb'(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[opusr]_[A-Za-z0-9]{24,})', data))


def run(name, command, timeout=180):
    env = child_env()
    result = subprocess.run(list(map(str, command)), cwd=ROOT, env=env,
                            capture_output=True, timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    assert not scan(result.stdout + result.stderr), 'sensitive shape detected; output suppressed'
    (HERE / (name + '.stdout.txt')).write_bytes(result.stdout)
    (HERE / (name + '.stderr.txt')).write_bytes(result.stderr)
    put(name + '.exit.json', {'command': list(map(str, command)), 'returncode': result.returncode,
        'environment_keys': sorted(env), 'synthetic_home': env['HOME'],
        'token_shape_present': False})
    print(json.dumps({'step': name, 'returncode': result.returncode, 'sensitive_shape_present': False}))
    return result


def historical_view(python):
    old = HERE.parent / 'd18-final-review'
    relative = old.relative_to(ROOT).as_posix()
    archive = subprocess.check_output(['git', 'archive', '--format=tar', 'HEAD', relative],
                                      cwd=ROOT, env=child_env())
    replay = LAB / '.t' / 'm18q-historical-review'
    replay.mkdir(exist_ok=False)
    copied = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as frozen:
        for member in frozen.getmembers():
            if not member.isfile():
                continue
            target = replay / member.name
            assert target.resolve().is_relative_to(replay.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            data = frozen.extractfile(member).read()
            target.write_bytes(data)
            copied[member.name] = sha(data)
    old_view = replay / relative
    lab_view = replay / LAB.relative_to(ROOT)
    lab_view.mkdir(parents=True)
    scripts = {}
    with zipfile.ZipFile(old / 'm18f-independent-r01.zip') as zipped:
        metadata = json.loads(zipped.read('m18f-independent-r01/environment.json'))
        for script, expected in metadata['harness_sha256'].items():
            data = zipped.read('m18f-independent-r01/h/' + script)
            assert sha(data) == expected
            (lab_view / script).write_bytes(data)
            scripts[script] = expected
    put('historical-view.json', {'root': str(replay), 'tracked_review_files': copied,
        'lab_scripts_from_old_exact_archive': scripts,
        'current_implementation_untouched': True, 'assertions_unchanged': True})
    assert run('audit-old-review-historical-view', [python, old_view / 'audit.py']).returncode == 0


def main():
    short = Path('D:/r18q-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    short.mkdir(exist_ok=False)
    venv = short / 'v'
    put('setup.json', {'short_root': str(short), 'venv': str(venv), 'cache': str(short / 'c'),
        'merge': 'd719be86b5d768270620dedc7d8db9ed870ff35e',
        'candidate': '1860c70ad6109dbd09ac80ac7a2a118d77818012',
        'collector_sha256_before_execution': sha(Path(__file__).read_bytes()),
        'audit_sha256_before_execution': sha((HERE / 'audit.py').read_bytes())})
    assert run('venv', [sys.executable, '-m', 'venv', venv]).returncode == 0
    python = venv / 'Scripts/python.exe'
    assert run('install', [python, '-m', 'pip', '--isolated', 'install', '--target', LAB / '.t',
        '-r', LAB / 'requirements.txt', '--cache-dir', short / 'c',
        '--disable-pip-version-check']).returncode == 0
    label = 'm18q-independent-r01'
    result = run('independent', [python, LAB / 'run.py', label], timeout=120)
    source, retained = LAB / 'raw' / label, LAB / '.t' / label
    assert source.resolve().parent == (LAB / 'raw').resolve()
    assert retained.resolve().parent == (LAB / '.t').resolve()
    assert source.resolve().is_relative_to(ROOT) and retained.resolve().is_relative_to(ROOT)
    assert not retained.exists()
    shutil.move(str(source), str(retained))
    files = {path.relative_to(retained).as_posix(): path.read_bytes()
             for path in sorted(retained.rglob('*')) if path.is_file()}
    assert not any(scan(data) for data in files.values())
    archive = HERE / (label + '.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as zipped:
        for name, data in files.items():
            zipped.writestr(label + '/' + name, data)
    put('round-manifest.json', {'archive': archive.name, 'archive_sha256': sha(archive.read_bytes()),
        'files': {label + '/' + name: sha(data) for name, data in files.items()},
        'source_resolved_before_move': str(source.resolve()), 'retained': str(retained),
        'token_shape_present': False})
    assert result.returncode == 0
    assert run('verify-original', [python, LAB / 'verify.py', '--git']).returncode == 0
    for name, folder in [('first', 'd18'), ('pending', 'd18p'), ('final-fix', 'd18q')]:
        assert run('audit-' + name, [python, HERE.parent / folder / 'audit.py']).returncode == 0
    rejection = run('audit-old-review-on-current', [python, HERE.parent / 'd18-final-review/audit.py'])
    assert rejection.returncode == 1 and b'AssertionError' in rejection.stderr
    historical_view(python)
    assert run('audit-new-capture', [python, HERE / 'audit.py', '--capture']).returncode == 0
    print(json.dumps({'round': label, 'pytest_returncode': result.returncode,
                      'archive_files': len(files), 'old_source_bound_audit_rejection_expected': True}))


if __name__ == '__main__':
    main()
