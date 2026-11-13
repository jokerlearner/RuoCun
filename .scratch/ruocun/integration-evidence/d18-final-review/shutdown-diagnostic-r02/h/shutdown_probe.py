"""Safely demonstrate Python shutdown after a pending harness diagnostic failure.

No candidate byte or assertion is changed. A review-only atexit safety callback
observes the shutdown entry while global application ownership is still intact,
then calls native TerminateProcess before Python can release ctypes globals.
"""
from pathlib import Path
import atexit
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
import runpy
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LAB = ROOT / '.scratch/ruocun-discovery/experiments/durable-io'
sys.path.insert(0, str(LAB))
import probe as p
from safe_env import child_env


def worker(root):
    native_dump = p.dump

    def diagnostic_failure(path, value):
        if Path(path).name == 'observation.json':
            raise OSError('review-only injected diagnostic write failure')
        return native_dump(path, value)

    def safe_shutdown_observation():
        owners = p.PENDING_IO
        flags = W.DWORD()
        native_dump(root / 'shutdown-entry.json', {
            'python_atexit_reached': True,
            'evidence_kind': 'review-only diagnostic-write-boundary-injection',
            'native_diagnostic_failure_tested': False,
            'application_pending_owner_count': len(owners),
            'native_still_pending': owners[0]['overlap'].internal == 0x103,
            'event_open': bool(p.K.GetHandleInformation(owners[0]['event'], C.byref(flags))),
            'actual_pid': os.getpid(), 'creation_time': p.creation_time(p.K.GetCurrentProcess()),
            'safety_callback_native_termination_before_global_teardown': True,
            'no_actual_use_after_free_attempted': True})
        p.stop_pending_process()

    atexit.register(safe_shutdown_observation)
    p.dump = diagnostic_failure
    sys.argv = [str(LAB / 'pending.py'), 'worker', 'cancel-fail', str(root)]
    runpy.run_path(str(LAB / 'pending.py'), run_name='__main__')


def submission_worker(root):
    import pending as h

    class SubmissionBoundaryInterruption(BaseException):
        pass

    class SubmissionBoundary(h.Boundary):
        def ConnectNamedPipe(self, handle, pointer):
            ok = super().ConnectNamedPipe(handle, pointer)
            if self.actual_pending:
                self.injected.append({'api': 'ConnectNamedPipe-return-boundary', 'native_called': True,
                                      'native_return': False, 'native_winerror': 997,
                                      'injected_exception': 'SubmissionBoundaryInterruption'})
                raise SubmissionBoundaryInterruption('review-only interruption after actual native pending submission')
            return ok

    import uuid
    boundary = SubmissionBoundary('submission-interruption')
    p.K = boundary
    name = '\\\\.\\pipe\\ruocun-d18-submit-' + uuid.uuid4().hex
    handle = p.new_pipe(name)
    try:
        p.dump(root / 'ready.json', {'pid': os.getpid(), 'creation_time': p.creation_time(p.K.GetCurrentProcess()),
                                     'pipe_name': name})
        caught = None
        try:
            p.pipe_io(handle, 'connect', 0, time.monotonic() + .1)
        except BaseException as error:
            caught = {'type': type(error).__name__, 'text': str(error)}
        flags = W.DWORD()
        p.dump(root / 'submission-entry.json', {
            'evidence_kind': 'review-only post-native-submission-boundary-exception',
            'real_user_ctrl_c_timing_tested': False,
            'native_still_pending': boundary.actual_pending and boundary.overlap.internal == 0x103,
            'event_open': bool(boundary.native.GetHandleInformation(boundary.overlap.event, C.byref(flags))),
            'early_event_close_attempts': boundary.early_closes,
            'application_pending_owner_count': len(p.PENDING_IO), 'error': caught,
            'injections': boundary.injected,
            'test_safety_anchor_retained_overlapped': True,
            'safety_native_termination_before_local_release': True,
            'no_actual_use_after_free_attempted': True})
    finally:
        boundary.native.TerminateProcess(boundary.native.GetCurrentProcess(), 96)
        os._exit(96)


def supervise(mode='shutdown', label=None):
    root = HERE / (label or ('submission-interruption-r01' if mode == 'submission' else 'shutdown-diagnostic-r01'))
    root.mkdir(exist_ok=False)
    snapshots = root / 'h'
    snapshots.mkdir()
    hashes = {}
    for source in [Path(__file__).resolve(), LAB / 'probe.py', LAB / 'pending.py', LAB / 'safe_env.py']:
        data = source.read_bytes()
        (snapshots / source.name).write_bytes(data)
        hashes[source.name] = hashlib.sha256(data).hexdigest()
    p.dump(root / 'environment.json', {'harness_sha256': hashes,
                                      'review_boundary': 'controlled diagnostic/submission exception only'})
    role = 'submission-worker' if mode == 'submission' else 'worker'
    command = [sys._base_executable, str(Path(__file__).resolve()), role, str(root)]
    with (root / 'worker.stdout.txt').open('wb') as out, (root / 'worker.stderr.txt').open('wb') as err:
        process = subprocess.Popen(command, stdout=out, stderr=err, env=child_env(),
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        start = p.creation_time(process._handle)
        p.dump(root / 'process.json', {'pid': process.pid, 'creation_time': start, 'command': command,
                                      'environment_keys': sorted(child_env())})
        try:
            ready = p.wait_json(root / 'ready.json')
            assert (ready['pid'], ready['creation_time']) == (process.pid, start)
            process.wait(timeout=5)
        finally:
            forced = process.poll() is None
            if forced:
                assert p.creation_time(process._handle) == start
                p.checked(p.K.TerminateProcess(process._handle, 97))
                process.wait(timeout=3)
            cleanup = {'pid': process.pid, 'creation_time': start, 'returncode': process.returncode,
                       'same_creation_time': p.creation_time(process._handle) == start,
                       'held_handle_signaled': p.K.WaitForSingleObject(process._handle, 0) == 0,
                       'forced': forced}
            old = int(process._handle)
            process._handle.Close()
            flags = W.DWORD()
            C.set_last_error(0)
            cleanup['process_handle_closed'] = not p.K.GetHandleInformation(old, C.byref(flags)) and C.get_last_error() == 6
            p.dump(root / 'cleanup.json', cleanup)
    observation = p.load(root / ('submission-entry.json' if mode == 'submission' else 'shutdown-entry.json'))
    absent = p.attempt_open(ready['pipe_name'], pipe=True)
    cleanup['pipe_absent'] = not absent['success'] and absent['winerror'] == 2
    cleanup['open_after_exit'] = absent
    p.dump(root / 'cleanup.json', cleanup)
    assert cleanup['returncode'] == 96 and not forced and cleanup['held_handle_signaled']
    assert cleanup['process_handle_closed'] and cleanup['same_creation_time'] and cleanup['pipe_absent']
    assert observation['native_still_pending'] and observation['event_open']
    if mode == 'submission':
        assert observation['application_pending_owner_count'] == 0 and len(observation['early_event_close_attempts']) == 1
        assert observation['error']['type'] == 'SubmissionBoundaryInterruption'
    else:
        assert observation['python_atexit_reached'] and observation['application_pending_owner_count'] == 1
    p.dump(root / 'result.json', {'ready': ready, 'observation': observation, 'cleanup': cleanup})
    print(json.dumps({'evidence_mode': mode, 'confirmed_unsafe_exit_boundary': True,
                      'safe_native_termination_confirmed': True, 'pipe_absent': True}))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'worker':
        worker(Path(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == 'submission-worker':
        submission_worker(Path(sys.argv[2]))
    else:
        supervise(sys.argv[1] if len(sys.argv) > 1 else 'shutdown', sys.argv[2] if len(sys.argv) > 2 else None)
