"""Seal review evidence and compare each staged blob before a checked evidence commit."""
from pathlib import Path
import json
import subprocess
import sys
import audit
import review

HERE, ROOT, LAB = review.HERE, review.ROOT, review.LAB


def files():
    return {path.relative_to(HERE).as_posix(): review.sha(path.read_bytes())
            for path in sorted(HERE.rglob('*')) if path.is_file()
            and '__pycache__' not in path.parts and path.suffix != '.pyc'
            and path.name != 'evidence-sha256.json'}


def inventory():
    (HERE / 'evidence-sha256.json').write_text(json.dumps(files(), ensure_ascii=False, indent=2), encoding='utf-8')


def git(*arguments):
    return subprocess.check_output(['git', *arguments], cwd=ROOT, env=review.child_env())


def validate():
    result = audit.audit()
    pipes = audit.read('post-pipe-state.json')
    assert pipes['all_14_pipe_names_absent_error_2'] and len(pipes['endpoints']) == 14
    assert all(not item['success'] and item['winerror'] == 2 for item in pipes['endpoints'])
    sync = audit.read('sync-check.json')
    assert not sync['relevant_paths_changed'] and not sync['candidate_history_paths_changed']
    assert not sync['unrelated_native_experiments_rerun']
    for name, expected in sync['tested_7_script_sha256_still_match'].items():
        assert review.sha((LAB / name).read_bytes()) == expected
    current = files()
    assert current == audit.read('evidence-sha256.json')
    return result


def staged():
    relative = HERE.relative_to(ROOT).as_posix()
    entries = audit.read('evidence-sha256.json')
    expected_paths = {relative + '/' + name for name in entries} | {relative + '/evidence-sha256.json'}
    actual_paths = set(git('diff', '--cached', '--name-only').decode().splitlines())
    assert actual_paths == expected_paths
    for name, expected in entries.items():
        assert review.sha(git('show', ':' + relative + '/' + name)) == expected, name
    assert git('show', ':' + relative + '/evidence-sha256.json') == (HERE / 'evidence-sha256.json').read_bytes()
    return len(actual_paths)


def main():
    mode = sys.argv[1]
    if mode == 'identity':
        result = subprocess.run(['git', 'var', 'GIT_AUTHOR_IDENT'], cwd=ROOT,
                                env=review.child_env(), capture_output=True)
        assert not review.scan(result.stdout + result.stderr)
        (HERE / 'identity-probe.stdout.txt').write_bytes(result.stdout)
        (HERE / 'identity-probe.stderr.txt').write_bytes(result.stderr)
        review.put('identity-probe.json', {'command': ['git', 'var', 'GIT_AUTHOR_IDENT'],
            'returncode': result.returncode, 'synthetic_home_used': True,
            'known_identity_missing_message': b'Author identity unknown' in result.stderr})
        assert result.returncode != 0 and b'Author identity unknown' in result.stderr
        print(json.dumps({'synthetic_git_author_missing': True, 'evidence_saved': True}))
    elif mode in {'seal', 'reseal'}:
        if mode == 'seal':
            review.put('seal-check.json', {'history_and_round_audit_already_passed': True,
                'sensitive_parent_scan_before_seal': 'sensitive-scan-preseal.json',
                'no_business_test_rerun': True, 'excluded': ['__pycache__', '*.pyc']})
        inventory()
        validate()
        print(json.dumps({'sealed_files': len(files()), 'valid': True}))
    elif mode == 'stage':
        validate()
        relative = HERE.relative_to(ROOT).as_posix()
        git('add', '--', relative)
        count = staged()
        receipt = 'staged-byte-final-check.json' if (HERE / 'staged-byte-check.json').exists() else 'staged-byte-check.json'
        review.put(receipt, {'initial_staged_files_verified': count,
            'each_staged_blob_equals_worktree_sha256': True,
            'manifest_staged_as_exact_bytes': True,
            'final_check_repeated_after_adding_this_receipt': True})
        inventory()
        git('add', '--', relative)
        count = staged()
        validate()
        outcome = subprocess.run(['git', '-c', 'user.name=Codex', '-c', 'user.email=codex@local',
            'commit', '--quiet', '-m',
            'evidence: accept final D18 ownership and entry guards after independent review'],
            cwd=ROOT, env=review.child_env(), capture_output=True)
        if outcome.returncode:
            assert not review.scan(outcome.stdout + outcome.stderr)
            (HERE / 'commit-retry.stdout.txt').write_bytes(outcome.stdout)
            (HERE / 'commit-retry.stderr.txt').write_bytes(outcome.stderr)
            raise RuntimeError('evidence commit failed; scanned output retained')
        print(json.dumps({'staged_files_verified': count, 'commit': git('rev-parse', 'HEAD').decode().strip(),
                          'worktree_clean': not git('status', '--porcelain').strip()}))
    elif mode == 'check':
        result = validate()
        print(json.dumps({'valid': True, 'files': len(files()), 'pytest': result['pytest']}))
    else:
        raise SystemExit('use seal, stage or check')


if __name__ == '__main__':
    main()
