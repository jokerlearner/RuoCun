"""Run in a wheel-only external environment; inspect actual import and resource origins."""
import hashlib
import importlib.util
import json
import sys
from importlib import metadata, resources
from pathlib import Path

import ruocun

product = metadata.distribution("ruocun")
assert ruocun.__version__ == product.version == "0.1.0.dev0"
assert not product.requires
assert all("firstcode" not in p.lower() for p in sys.path)
assert Path(ruocun.__file__).is_relative_to(Path(sys.prefix))
assert all(importlib.util.find_spec(n) is None for n in ("pytest", "ruff", "mypy", "build", "hatchling"))
packages = {d.metadata["Name"]: d.version for d in metadata.distributions()}
support = importlib.util.find_spec("ruocun_acceptance")
if support:
    assert Path(support.origin).is_relative_to(Path(sys.prefix))
    assert importlib.util.find_spec("oracle").origin.startswith(sys.prefix)
else:
    assert importlib.util.find_spec("oracle") is None
pths = []
for p in (Path(sys.prefix) / "Lib/site-packages").glob("*.pth"):
    content = p.read_bytes()
    assert b"firstcode" not in content.lower()
    pths.append({"name": p.name, "sha256": hashlib.sha256(content).hexdigest()})
help_text = resources.files("ruocun").joinpath("resources/help.zh-CN.txt").read_bytes()
assert "用法：ruocun [选项] [提示词]" in help_text.decode()
print(json.dumps({"cwd": str(Path.cwd()), "executable": sys.executable, "prefix": sys.prefix,
                  "origin": ruocun.__file__, "support_origin": support.origin if support else None,
                  "sys_path": sys.path, "distributions": packages, "pth_files": pths,
                  "help_sha256": hashlib.sha256(help_text).hexdigest(),
                  "no_source_or_development_dependencies": True}, ensure_ascii=False, indent=2))
