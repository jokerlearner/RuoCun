"""Scan with the real parent environment, then seal new review evidence bytes."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import zipfile
import review

HERE = Path(__file__).resolve().parent


def main():
    correction = '--correct-bytecode-inventory' in sys.argv
    if correction:
        initial = json.loads((HERE / 'evidence-sha256.json').read_text(encoding='utf-8'))
        assert any('__pycache__/' in name for name in initial)
        retained = HERE / 'collection-r01'
        retained.mkdir(exist_ok=False)
        shutil.copyfile(HERE / 'evidence-sha256.json', retained / 'rejected-evidence-sha256.json')
        shutil.copyfile(HERE / 'sensitive-scan.json', retained / 'sensitive-scan.json')
        review.put('collection-adjustment.json', {
            'intermediate_commit_not_delivery': 'a3556416864c06bfdb761661b0eb1d5d7a868ad1',
            'failure': 'initial manifest included ignored __pycache__/review.cpython-311.pyc',
            'observed_staged_validation_exit': 128,
            'original_failure_record': 'git show :<ignored pyc> failed; check_output raised CalledProcessError',
            'shell_continued_after_native_python_failure': True,
            'fix': 'exclude bytecode/cache from evidence identity, retain original rejected manifest, validate staged bytes before checked commit',
            'business_or_candidate_test_rerun': False})
    setup = json.loads((HERE / 'setup.json').read_text(encoding='utf-8'))
    python = str(Path(setup['venv']) / 'Scripts/python.exe')
    if not correction:
        assert review.run('audit-final', [python, str(HERE / 'audit.py')]).returncode == 0
    count, archive_members = 0, 0
    for path in HERE.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        assert not any(review.scan(path.read_bytes()).values()), 'sensitive content present; do not commit'
        count += 1
        if path.suffix == '.zip':
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    assert not any(review.scan(archive.read(member)).values()), 'sensitive member present; do not commit'
                    archive_members += 1
    scan_result = {'current_real_parent_environment_used_for_comparison': True,
                                      'known_environment_sensitive_value_present': False,
                                      'token_shape_present': False,
                                      'new_files_scanned': count, 'archive_members_scanned': archive_members,
                                      'credential_values_saved_or_printed': False}
    def replace(name, value):
        (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    def inventory():
        return {path.relative_to(HERE).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(HERE.rglob('*')) if path.is_file()
                and '__pycache__' not in path.parts and path.suffix != '.pyc'
                and path != HERE / 'evidence-sha256.json'}
    if correction:
        replace('sensitive-scan.json', scan_result)
        replace('evidence-sha256.json', inventory())
        assert review.run('audit-corrected', [python, str(HERE / 'audit.py')]).returncode == 0
        replace('evidence-sha256.json', inventory())
    else:
        review.put('sensitive-scan.json', scan_result)
        review.put('evidence-sha256.json', inventory())
    entries = json.loads((HERE / 'evidence-sha256.json').read_text(encoding='utf-8'))
    assert all(hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected for name, expected in entries.items())
    print(json.dumps({'sealed_files': len(entries), 'sensitive_value_present': False, 'token_shape_present': False}))


if __name__ == '__main__':
    main()
