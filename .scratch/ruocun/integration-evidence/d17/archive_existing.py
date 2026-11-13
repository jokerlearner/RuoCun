"""Archive existing raw fixture reports without executing any capability probe."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

root = Path(sys.argv[1]).resolve()
out = Path(__file__).resolve().parent / (root.name + '-raw-supplement.zip')
selected = [p for p in root.rglob('*') if p.is_file() and 'rt' not in p.relative_to(root).parts
            and p.suffix in {'.json','.txt','.xml'} and 'pytest-cache' not in p.relative_to(root).parts]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(selected):
        archive.write(path, path.relative_to(root).as_posix())
manifest = {'mode': 'existing raw only; no tests or probes executed', 'archive': out.name,
    'archive_sha256': digest(out), 'files': {p.relative_to(root).as_posix(): digest(p) for p in sorted(selected)}}
out.with_suffix('.manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'archive': out.name, 'raw_files': len(selected)}))
