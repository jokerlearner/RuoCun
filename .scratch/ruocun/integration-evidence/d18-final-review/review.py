"""Independent D18 review runner. Launches test/install/audit children by allowlist."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LAB = ROOT / '.scratch/ruocun-discovery/experiments/durable-io'
sys.path.insert(0, str(LAB))
from safe_env import child_env


def digest(data):
    return hashlib.sha256(data).hexdigest()


def put(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def scan(data):
    values = [value.encode() for key, value in os.environ.items()
              if re.search(r'KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL', key, re.I) and len(value) >= 8]
    return {'known_environment_credential_present': any(value in data for value in values),
            'token_shape_present': bool(re.search(rb'(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[opusr]_[A-Za-z0-9]{24,})', data))}


def run(name, command, timeout=180):
    env = child_env()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    captured = result.stdout + result.stderr
    checked = scan(captured)
    assert not any(checked.values()), 'sensitive output detected; output suppressed'
    (HERE / (name + '.stdout.txt')).write_bytes(result.stdout)
    (HERE / (name + '.stderr.txt')).write_bytes(result.stderr)
    put(name + '.exit.json', {'command': list(map(str, command)), 'returncode': result.returncode,
                             'started_utc': started, 'environment_keys': sorted(env), 'sensitive_scan': checked})
    print(json.dumps({'step': name, 'returncode': result.returncode, 'sensitive_present': False}))
    return result


def main():
    assert len(sys.argv) == 1
    short = Path('D:/r18f-' + datetime.datetime.now().strftime('%H%M%S'))
    short.mkdir(exist_ok=False)
    venv = short / 'v'
    put('setup.json', {'short_root': str(short), 'venv': str(venv), 'cache': str(short / 'c'),
                       'reviewed_merge': '069def00672567e1ad7e0c6fdbd6ba3adbb13911',
                       'candidate': '73e63d387654316ee2a415d7e47547725caf40d9'})
    assert run('venv', [sys.executable, '-m', 'venv', str(venv)]).returncode == 0
    python = str(venv / 'Scripts/python.exe')
    assert run('install', [python, '-m', 'pip', '--isolated', 'install', '--target', str(LAB / '.t'),
                           '-r', str(LAB / 'requirements.txt'), '--cache-dir', str(short / 'c'),
                           '--disable-pip-version-check']).returncode == 0
    label = 'm18f-independent-r01'
    test = run('independent', [python, str(LAB / 'run.py'), label], timeout=120)
    round_path = LAB / 'raw' / label
    retained = LAB / '.t' / label
    assert round_path.resolve().parent == (LAB / 'raw').resolve() and not retained.exists()
    shutil.move(str(round_path), str(retained))
    files = {path.relative_to(retained).as_posix(): path.read_bytes()
             for path in sorted(retained.rglob('*')) if path.is_file()}
    checks = [scan(data) for data in files.values()]
    assert all(not any(check.values()) for check in checks), 'sensitive archive contents detected'
    archive = HERE / (label + '.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as zipped:
        for name, data in files.items():
            zipped.writestr(label + '/' + name, data)
    put('round-manifest.json', {'archive': archive.name, 'archive_sha256': digest(archive.read_bytes()),
                              'files': {label + '/' + name: digest(data) for name, data in files.items()},
                              'sensitive_present': False})
    assert run('verify-original', [python, str(LAB / 'verify.py'), '--git']).returncode == 0
    assert run('audit-first-review', [python, str(HERE.parent / 'd18/audit.py')]).returncode == 0
    assert run('audit-pending-archives', [python, str(HERE.parent / 'd18p/audit.py')]).returncode == 0
    print(json.dumps({'independent_pytest_returncode': test.returncode, 'archive_files': len(files),
                      'round': label, 'evidence_retained': True}))


if __name__ == '__main__':
    main()
