"""Read-only PSEC API discovery; never creates a security environment."""
import ctypes as c
import datetime as dt
import hashlib
import json
from pathlib import Path
import winreg

here = Path(__file__).resolve().parent
result = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "creates_environment": False,
          "mxc_pin": "f4aa3fd59306d140ccf7448e914306fc6cdb74d0"}
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
    result["os"] = {name: winreg.QueryValueEx(key, name)[0] for name in ("CurrentBuildNumber", "UBR", "EditionID", "DisplayVersion")}
try:
    library = c.WinDLL("processmodel.dll", winmode=0x800)
    names = ("CreateProcessSecurityEnvironment", "QueryProcessSecurityEnvironmentSupport", "IsProcessSecurityEnvironmentVersionSupported", "CloseProcessSecurityEnvironment")
    result["exports"] = {name: hasattr(library, name) for name in names}
    if result["exports"]["QueryProcessSecurityEnvironmentSupport"]:
        query = library.QueryProcessSecurityEnvironmentSupport
        query.argtypes = [c.POINTER(c.c_uint64)]
        query.restype = c.c_long
        flags = c.c_uint64()
        hr = query(c.byref(flags))
        result["support"] = {"hresult": f"0x{hr & 0xffffffff:08x}", "flags": flags.value}
    if result["exports"]["IsProcessSecurityEnvironmentVersionSupported"]:
        version = library.IsProcessSecurityEnvironmentVersionSupported
        version.argtypes = [c.c_uint32, c.POINTER(c.c_uint8), c.POINTER(c.c_uint32)]
        version.restype = c.c_long
        available, minor = c.c_uint8(), c.c_uint32()
        hr = version(1, c.byref(available), c.byref(minor))
        result["version_1"] = {"hresult": f"0x{hr & 0xffffffff:08x}", "available": available.value, "minor": minor.value}
except OSError as error:
    result["load_error"] = {"winerror": error.winerror}
result["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
output = here / "read-only-support.json"
with output.open("x", encoding="utf-8") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False, indent=2))
