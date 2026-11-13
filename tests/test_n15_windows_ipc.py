"""D18既有具名管道/身份/认证语义的最小产品确认。"""

import ctypes as C
import io
import json
import os
import struct
import subprocess
import sys
import time
import uuid
from ctypes import wintypes as W
from pathlib import Path

import pytest

from ruocun.platform.windows.ipc import (
    MAX_FRAME,
    IPCError,
    PipeServer,
    encode_frame,
    read_frame,
    request,
)


def helper_command():
    source = str(Path(__file__).resolve().parents[1] / "src")
    code = (f"import sys; sys.path.insert(0, {source!r}); "
            "from ruocun.platform.windows.ipc import helper_main; raise SystemExit(helper_main())")
    return [sys.executable, "-I", "-X", "utf8", "-c", code]


def test_utf8_frame_uses_byte_length_and_rejects_oversize():
    value = {"version": 1, "content": "中🙂"}
    frame = encode_frame(value)
    assert struct.unpack("<I", frame[:4])[0] == len(frame[4:])
    assert b"\xe4\xb8\xad\xf0\x9f\x99\x82" in frame
    with pytest.raises(ValueError):
        encode_frame({"padding": "x" * MAX_FRAME})


def test_frame_parser_handles_source_unicode_boundary_multiple_and_invalid_frames():
    class Fragmented(io.BytesIO):
        def read(self, size=-1):
            return super().read(min(size, 7))

    # 在来源65536个UTF16单位边界内，中文/emoji的UTF8跨分片仍完整解码。
    text = "中" * 60000 + "🙂" * 2000
    stream = Fragmented(encode_frame({"text": text}) + encode_frame({"next": True}))
    assert read_frame(stream) == {"text": text}
    assert read_frame(stream) == {"next": True}
    for malformed in [struct.pack("<I", 0), struct.pack("<I", MAX_FRAME + 1),
                      struct.pack("<I", 10) + b"{}", struct.pack("<I", 1) + b"\xff"]:
        with pytest.raises((EOFError, ValueError)):
            read_frame(io.BytesIO(malformed))


def test_actual_private_pipe_auth_peer_identity_utf8_and_precise_close():
    name = "\\\\.\\pipe\\ruocun-n15-" + uuid.uuid4().hex
    capability = os.urandom(32)
    peers = []

    def echo(payload, peer):
        peers.append(peer)
        return {"received": payload["text"]}

    server = PipeServer(name, capability, echo, helper_command=helper_command())
    server.start(time.monotonic() + 3)
    try:
        assert server.alive and server.helper_pid != os.getpid()
        assert server.pipe_acl == f"D:P(A;;FA;;;{server.private_sid})"
        text = "中文🙂" * 12000
        result = request(name, capability, {"text": text}, expected_server_pid=server.helper_pid,
                         deadline=time.monotonic() + 3, helper_command=helper_command())
        assert result == {"received": text}
        assert len(peers) == 1 and peers[0].owner_pid == os.getpid()
        assert peers[0].helper_pid != os.getpid() and peers[0].owner_identity.pid == os.getpid()
        # D18匿名身份真实拒绝，子进程仅尝试本次随机pipe，不处理用户数据。
        anonymous = r'''
import ctypes as C
import sys
from ctypes import wintypes as W
k=C.WinDLL("kernel32", use_last_error=True)
a=C.WinDLL("advapi32", use_last_error=True)
k.GetCurrentThread.restype=W.HANDLE
a.ImpersonateAnonymousToken.argtypes=[W.HANDLE]
k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,C.c_void_p,W.DWORD,W.DWORD,W.HANDLE]
k.CreateFileW.restype=W.HANDLE
assert a.ImpersonateAnonymousToken(k.GetCurrentThread())
try:
    handle=k.CreateFileW(sys.argv[1],0x12019b,0,None,3,0,None)
    error=C.get_last_error()
    assert handle==C.c_void_p(-1).value and error==5, error
    print("anonymous_denied_winerror_5")
finally:
    a.RevertToSelf()
'''
        denied = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", anonymous, name],
                                capture_output=True, text=True, timeout=5)
        assert denied.returncode == 0 and "anonymous_denied_winerror_5" in denied.stdout
        duplicate = PipeServer(name, capability, echo, helper_command=helper_command())
        with pytest.raises(IPCError):
            duplicate.start(time.monotonic() + 3)
        with pytest.raises(IPCError):
            request(name, os.urandom(32), {"text": "wrong key"}, expected_server_pid=server.helper_pid,
                    deadline=time.monotonic() + 3, helper_command=helper_command())
        assert len(peers) == 1
        with pytest.raises(IPCError):
            request(name, capability, {"text": "wrong server"}, expected_server_pid=server.helper_pid + 1,
                    deadline=time.monotonic() + 3, helper_command=helper_command())
        assert len(peers) == 1
        assert request(name, capability, {"text": "still alive"}, expected_server_pid=server.helper_pid,
                       deadline=time.monotonic() + 3, helper_command=helper_command()) == {"received": "still alive"}
    finally:
        server.close()
    assert not server.alive
    kernel = C.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
    kernel.CreateFileW.restype = W.HANDLE
    handle = kernel.CreateFileW(name, 0x12019b, 0, None, 3, 0, None)
    assert handle == C.c_void_p(-1).value and C.get_last_error() == 2


def test_pending_native_submission_is_owned_and_only_helper_fails_stops(tmp_path):
    # D18原有submit-raise故障复现，证明产品目标入口自身finally保护。
    source = str(Path(__file__).resolve().parents[1] / "src")
    observed = tmp_path / "pending-owned.json"
    returned = tmp_path / "target-returned.txt"
    code = f'''
import sys,json,ctypes as C
from pathlib import Path
sys.path.insert(0,{source!r})
from ruocun.platform.windows import ipc
native=ipc.K
class Boundary:
    def __getattr__(self,name):
        return getattr(native,name)
    def ConnectNamedPipe(self,handle,pointer):
        result=native.ConnectNamedPipe(handle,pointer)
        if not result and C.get_last_error()==997:
            owner=ipc.PENDING_IO[0]
            Path({str(observed)!r}).write_text(json.dumps({{
                'pending_owned':len(ipc.PENDING_IO),
                'buffer_retained':owner['buffer'] is not None,
                'overlap_retained':C.addressof(owner['overlap'])==C.addressof(pointer._obj),
                'native_pending':owner['overlap'].internal==259,
            }}))
            raise KeyboardInterrupt('synthetic submission-boundary interruption')
        return result
ipc.K=Boundary()
try:
    ipc.helper_main()
finally:
    Path({str(returned)!r}).write_text('target escaped its pending-I/O finally')
'''
    server = PipeServer("\\\\.\\pipe\\ruocun-n15-" + uuid.uuid4().hex, os.urandom(32),
                        lambda payload, peer: payload,
                        helper_command=[sys.executable, "-I", "-X", "utf8", "-c", code])
    server.start(time.monotonic() + 3)
    deadline = time.monotonic() + 3
    while server.alive and time.monotonic() < deadline:
        time.sleep(.01)
    server.close()
    assert server.error is not None and not returned.exists()
    assert json.loads(observed.read_text()) == {
        "pending_owned": 1, "buffer_retained": True, "overlap_retained": True, "native_pending": True,
    }


def test_server_helper_closes_endpoint_when_its_runner_owner_exits():
    # D08真实owner退出后的transport收口，父测试只持有此次helper的实际进程句柄。
    source = str(Path(__file__).resolve().parents[1] / "src")
    code = f'''
import sys,os,json,time,uuid
sys.path.insert(0,{source!r})
from dataclasses import asdict
from ruocun.platform.windows.ipc import PipeServer
from ruocun.session.process_identity import process_identity
assert process_identity() is not None
helper_code="import sys; sys.path.insert(0,"+repr({source!r})+"); from ruocun.platform.windows.ipc import helper_main; raise SystemExit(helper_main())"
server=PipeServer("\\\\\\\\.\\\\pipe\\\\ruocun-n15-"+uuid.uuid4().hex,os.urandom(32),lambda payload,peer:payload,
                  helper_command=[sys.executable,'-I','-X','utf8','-c',helper_code])
server.start(time.monotonic()+3)
print(json.dumps(asdict(server.helper_identity)),flush=True)
os._exit(0)
'''
    controller = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code],
                                capture_output=True, text=True, timeout=15)
    assert controller.returncode == 0, controller.stderr
    identity = json.loads(controller.stdout)
    kernel = C.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    kernel.OpenProcess.restype = W.HANDLE
    kernel.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    kernel.GetProcessTimes.argtypes = [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4
    kernel.TerminateProcess.argtypes = [W.HANDLE, W.UINT]
    kernel.CloseHandle.argtypes = [W.HANDLE]
    handle = kernel.OpenProcess(0x101001, False, identity["pid"])
    if not handle:
        assert C.get_last_error() == 87
        return
    owned = False
    try:
        stamps = [W.FILETIME() for _ in range(4)]
        assert kernel.GetProcessTimes(handle, *[C.byref(stamp) for stamp in stamps])
        owned = str((stamps[0].dwHighDateTime << 32) | stamps[0].dwLowDateTime) == identity["start"]
        if not owned:
            return  # PID已重用同样证明旧helper已退出，绝不触碰新进程。
        assert kernel.WaitForSingleObject(handle, 1500) == 0
    finally:
        if owned and kernel.WaitForSingleObject(handle, 0) != 0:
            kernel.TerminateProcess(handle, 98)
            assert kernel.WaitForSingleObject(handle, 3000) == 0
        kernel.CloseHandle(handle)
