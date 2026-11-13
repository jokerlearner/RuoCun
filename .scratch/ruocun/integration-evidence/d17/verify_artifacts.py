"""Read-only evidence, entry syntax, and native query validation."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import uuid
import zipfile

evidence = Path(__file__).resolve().parent
repo = next(p for p in evidence.parents if (p / 'AGENTS.md').is_file())
original = repo / '.scratch/ruocun-discovery/experiments/windows'
root = Path(sys.argv[1]).resolve()
manifest = json.loads((original / 'manifest.json').read_text('utf-8'))
def digest(data):
    return hashlib.sha256(data).hexdigest()
mismatches = [name for name, value in manifest['files'].items() if digest((original / name).read_bytes()) != value]
archive_results = []
for name in [root.name + '-manifest.json', root.name + '-raw-supplement.manifest.json']:
    value = json.loads((evidence / name).read_text('utf-8'))
    archive = evidence / value['archive']
    with zipfile.ZipFile(archive) as z:
        errors = [path for path, expected in value['files'].items() if digest(z.read(path)) != expected]
    archive_results.append({'archive': archive.name, 'archive_hash_ok': digest(archive.read_bytes()) == value['archive_sha256'], 'entries': len(value['files']), 'entry_mismatches': errors})
syntax = []
for path in evidence.glob('*.py'):
    ast.parse(path.read_text('utf-8'))
    syntax.append(path.name)
sys.path.insert(0, str(root / 'safe-source'))
spec = importlib.util.spec_from_file_location('d17_entry_query_validation', evidence / 'audit_conftest.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
query_result = audit.absent_query('RuoCunD17Missing' + uuid.uuid4().hex, audit.class_query, {1411})
source_results = {p.name: (root / 'safe-source' / p.name).read_bytes() == p.read_bytes() for p in original.glob('*.py')}
task_tail = (root / 'safe-source/task.py').read_bytes().endswith((original / 'task.py').read_bytes())
original_task = (original / 'task.py').read_bytes()
executed_task = (root / 'safe-source/task.py').read_bytes()
import difflib
byte_diff = ''.join(difflib.unified_diff(original_task.decode('utf-8').splitlines(True), executed_task.decode('utf-8').splitlines(True), fromfile='candidate/task.py', tofile='executed/task.py')).encode('utf-8')
diff_path = evidence / (root.name + '-task-byte.diff')
if diff_path.exists():
    assert diff_path.read_bytes() == byte_diff
else:
    diff_path.write_bytes(byte_diff)
result = {'candidate_entries': len(manifest['files']), 'candidate_mismatches': mismatches,
    'archives': archive_results, 'entry_syntax_checked': syntax,
    'read_only_GetClassInfoW_missing_class_query': query_result,
    'executed_source_byte_identical': source_results, 'task_original_tail_byte_identical': task_tail,
    'task_original_tail_equal_after_CRLF_normalization': executed_task.replace(b'\r\n',b'\n').endswith(original_task.replace(b'\r\n',b'\n')),
    'task_line_endings': {'original_CRLF': original_task.count(b'\r\n'), 'executed_CRLF': executed_task.count(b'\r\n'),
        'original_LF': original_task.count(b'\n'), 'executed_LF': executed_task.count(b'\n')},
    'no_capability_tests_or_resource_creation': True}
output_name = sys.argv[2] if len(sys.argv) > 2 else root.name + '-verification.json'
(evidence / output_name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
