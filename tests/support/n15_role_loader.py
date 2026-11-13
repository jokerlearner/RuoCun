"""Select this checkout, then execute the real package role dispatcher."""
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
runpy.run_module("ruocun", run_name="__main__")
