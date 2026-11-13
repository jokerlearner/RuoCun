"""Read-only source counter. Product files are never imported or executed."""
from __future__ import annotations
import argparse
import ast
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tokenize

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
TRIVIA = {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.NL, tokenize.COMMENT}

def physical_lines(text):
    if not text:
        return []
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines

def files_under(root):
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file() and not any(part in SKIP_DIRS for part in path.relative_to(root).parts) and path.suffix.lower() not in SKIP_SUFFIXES)

def decode_python(raw):
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    return raw.decode(encoding)

def analyze_python(path, raw):
    source = decode_python(raw)
    lines = physical_lines(source)
    blank = {i for i, line in enumerate(lines, 1) if not line.strip()}
    tree = ast.parse(source, filename=str(path))
    doc_spans = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                start_col = len(lines[first.lineno - 1].encode("utf-8")[:first.col_offset].decode("utf-8"))
                end_col = len(lines[first.end_lineno - 1].encode("utf-8")[:first.end_col_offset].decode("utf-8"))
                doc_spans.append(((first.lineno, start_col), (first.end_lineno, end_col)))
    code_lines = set()
    comment_doc_lines = {line for start, end in doc_spans for line in range(start[0], end[0] + 1)}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            comment_doc_lines.update(range(token.start[0], token.end[0] + 1))
        if token.type in TRIVIA:
            continue
        if any(start <= token.start and token.end <= end for start, end in doc_spans):
            continue
        code_lines.update(range(token.start[0], token.end[0] + 1))
    code_lines.difference_update(blank)
    code_lines.intersection_update(range(1, len(lines) + 1))
    docs = comment_doc_lines - blank - code_lines
    code_lines = set(range(1, len(lines) + 1)) - blank - docs
    return {"files": 1, "physical": len(lines), "code": len(code_lines), "comment_docstring": len(docs), "blank": len(blank)}

def new_stats():
    return {"files": 0, "physical": 0, "code": 0, "comment_docstring": 0, "blank": 0}

def add_stats(target, item):
    for key in target:
        target[key] += item[key]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    product = root / "src" / "ruocun"
    groups = defaultdict(new_stats)
    total = new_stats()
    details = []
    snapshot = {}
    text_resources = []
    binary_resources = []
    errors = []
    for path in files_under(product):
        relative = path.relative_to(product)
        raw = path.read_bytes()
        rel = path.relative_to(root).as_posix()
        sha = hashlib.sha256(raw).hexdigest()
        snapshot[rel] = sha
        if path.suffix.lower() == ".py":
            try:
                stats = analyze_python(path, raw)
            except (SyntaxError, UnicodeError, tokenize.TokenError) as exc:
                errors.append({"path": rel, "error_type": type(exc).__name__})
                continue
            group = relative.parts[0] if len(relative.parts) > 1 else "(root)"
            add_stats(groups[group], stats)
            add_stats(total, stats)
            details.append({"path": rel, "module": group, "sha256": sha, **stats})
        else:
            base = {"path": rel, "bytes": len(raw), "sha256": sha}
            try:
                text = raw.decode("utf-8-sig")
                if "\x00" in text:
                    raise UnicodeError("binary NUL")
                text_resources.append({**base, "physical": len(physical_lines(text)), "extension": path.suffix.lower() or "(no suffix)"})
            except UnicodeError:
                binary_resources.append(base)
    supplemental = {}
    for dirname in ("tests", "tools", "evals"):
        py_files = [p for p in files_under(root / dirname) if p.suffix.lower() == ".py"]
        supplemental[dirname] = {"python_files": len(py_files), "python_physical": sum(len(physical_lines(decode_python(p.read_bytes()))) for p in py_files)}
    changed_after_read = [rel for rel, sha in snapshot.items() if not (root / rel).is_file() or hashlib.sha256((root / rel).read_bytes()).hexdigest() != sha]
    current_paths = {p.relative_to(root).as_posix() for p in files_under(product)}
    added_after_read = sorted(current_paths - snapshot.keys())
    resource_extensions = defaultdict(lambda: {"files": 0, "physical": 0, "bytes": 0})
    for item in text_resources:
        group = resource_extensions[item["extension"]]
        group["files"] += 1
        group["physical"] += item["physical"]
        group["bytes"] += item["bytes"]
    result = {
        "root": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "All current src/ruocun .py files including untracked files; groups by first subdirectory, root files together; physical lines split on LF; blank lines take priority; ast locates module/class/function first-statement string docstrings; tokenize counts remaining non-trivia token lines as code; nonempty lines without code are comment/docstring; inline comments remain code lines; data/prompt strings remain code.",
        "excluded_dirs": sorted(SKIP_DIRS),
        "excluded_suffixes": sorted(SKIP_SUFFIXES),
        "modules": dict(sorted(groups.items())),
        "total": total,
        "text_resources_by_extension": dict(sorted(resource_extensions.items())),
        "text_resources_total": {"files": len(text_resources), "physical": sum(item["physical"] for item in text_resources), "bytes": sum(item["bytes"] for item in text_resources)},
        "text_resources": text_resources,
        "binary_resources": binary_resources,
        "supplemental_python_only": supplemental,
        "files": details,
        "product_manifest_sha256": hashlib.sha256("".join(f"{path}\0{sha}\n" for path, sha in sorted(snapshot.items())).encode()).hexdigest(),
        "changed_after_read": changed_after_read,
        "added_after_read": added_after_read,
        "parse_errors": errors,
    }
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("generated_at_utc", "modules", "total", "text_resources_by_extension", "text_resources_total", "binary_resources", "supplemental_python_only", "product_manifest_sha256", "changed_after_read", "added_after_read", "parse_errors")}, ensure_ascii=False, indent=2))
    print(f"RESULT={args.out}")
    if errors or changed_after_read or added_after_read:
        raise SystemExit(2)

if __name__ == "__main__":
    main()

