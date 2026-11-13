"""Fresh merger's independent byte and Windows process receipt audit (D19)."""
from __future__ import annotations
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path.cwd().resolve()
PREFIX = '.scratch/ruocun-discovery/experiments/sqlite-runtime'
EXP = ROOT / PREFIX
OUT = ROOT / '.scratch/ruocun/integration-evidence/d19-identity-review'
BASE = EXP / '.venv/q'
CANDIDATE = '0419c42c3593a6b56f78e9cad063c2a0c6e56600'
MERGE = '3a00c588fbd685ac4086cafd7d00e16ed64bd7c5'
ORIGINAL = 'b1b15b5a66e1e32b4e466cb830c263dcb13c83d0'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def tree(commit, prefix):
    result = {}
    for row in git('ls-tree', '-r', '-z', commit, '--', prefix).split(b'\0'):
        if row:
            meta, path = row.split(b'\t', 1)
            result[path.decode()] = meta.decode().split()[2]
    return result


def blobs(oids):
    oids = list(dict.fromkeys(oids))
    raw = subprocess.check_output(['git', 'cat-file', '--batch'], input=('\n'.join(oids)+'\n').encode(), cwd=ROOT)
    at, result = 0, {}
    for oid in oids:
        end = raw.index(b'\n', at)
        actual, kind, size = raw[at:end].decode().split()
        assert actual == oid and kind == 'blob'
        at = end + 1
        result[oid] = raw[at:at+int(size)]
        at += int(size)
        assert raw[at:at+1] == b'\n'
        at += 1
    assert at == len(raw)
    return result


def snapshot():
    base = Path(sys._base_executable).resolve().parent
    paths = [base/'python.exe', base/'python311.dll', base/'DLLs/sqlite3.dll', base/'DLLs/_sqlite3.pyd']
    paths += [ROOT/'.scratch/ruocun-discovery/experiments/runtime'/name for name in ['probe.py','run_probe.py']]
    paths += [ROOT.parents[1]/'.scratch/ruocun-discovery/experiments/runtime'/name for name in ['probe.py','run_probe.py']]
    record = {str(p): {'bytes':p.stat().st_size, 'sha256':sha(p.read_bytes())} for p in paths}
    default = subprocess.check_output([sys._base_executable,'-I','-c','import sqlite3; print(sqlite3.sqlite_version)'], text=True).strip()
    return {'files':record,'fresh_default_runtime':default}


def archives():
    checks = []
    for name, count in [('h',1033),('r',174)]:
        manifest = read(EXP/f'evidence/{name}.json')
        archive = EXP/f'evidence/{name}.zip'
        assert manifest['member_count'] == count
        assert sha(archive.read_bytes()) == manifest['archive_sha256']
        items = manifest['members']
        assert len(items) == count
        if name == 'h':
            assert manifest['source_commit'] == ORIGINAL
            entries = tree(ORIGINAL,PREFIX)
            assert {k[len(PREFIX)+1:]:v for k,v in entries.items()} == {v['member']:v['git_blob'] for v in items}
            original_blobs = blobs(entries.values())
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            assert len(names) == len(set(names)) == count
            assert set(names) == {v['member'] for v in items}
            for item in items:
                data = bundle.read(item['member'])
                assert len(data) == item['bytes'] and sha(data) == item['sha256']
                if name == 'h':
                    assert data == original_blobs[item['git_blob']]
            if name == 'h':
                audit = json.loads(bundle.read('evidence/audit-final.json'))
                assert audit['raw_files_checked'] == len(audit['files']) == 1029
                for entry in audit['files']:
                    assert sha(bundle.read(entry['path'])) == entry['sha256']
                failures = [v for v in names if v.endswith('.txt') and ('failed' in bundle.read(v).decode(errors='replace') or 'FAILED' in bundle.read(v).decode(errors='replace'))]
                assert failures
            else:
                text = bundle.read('pytest.txt').decode()
                assert '1 failed, 1 passed' in text and '39784 == 29064' in text
                assert {'pre.py','test.py','run/c/summary.json'}.issubset(names)
                assert json.loads(bundle.read('run/c/summary.json'))['passed'] == 12
        checks.append({'archive':name+'.zip','members':count,'sha256':sha(archive.read_bytes()),'all_member_size_sha_verified':True,'git_original_bytes_verified':name=='h','original_audit_files_verified':1029 if name=='h' else None,'failure_assets_preserved':True})
    entries = tree(CANDIDATE,PREFIX)
    data = blobs(entries.values())
    for path, oid in entries.items():
        raw = (ROOT/path).read_bytes()
        if raw != data[oid]:
            assert path.endswith(('/README.md', '/requirements-dev.txt')), path
            assert git('hash-object', '--path='+path, path).decode().strip() == oid, path
    longest = max((len(path),path) for path in entries)
    assert longest[0] == 146
    return {'archives':checks,'candidate_files_git_bytes_or_declared_text_normalization_verified':len(entries),'max_checkout_repo_relative_path':longest[0],'longest_path':longest[1],'fresh_long_worktree_checkout_succeeded':True}


K = C.WinDLL('kernel32',use_last_error=True)
K.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD]
K.OpenProcess.restype=W.HANDLE
K.GetProcessTimes.argtypes=[W.HANDLE]+[C.POINTER(W.FILETIME)]*4
K.GetExitCodeProcess.argtypes=[W.HANDLE,C.POINTER(W.DWORD)]
K.CloseHandle.argtypes=[W.HANDLE]


def is_alive(identity):
    handle=K.OpenProcess(0x1000,False,identity['pid'])
    if not handle:
        assert C.get_last_error()==87, C.WinError(C.get_last_error())
        return False
    try:
        code=W.DWORD()
        times=[W.FILETIME() for _ in range(4)]
        assert K.GetExitCodeProcess(handle,C.byref(code))
        assert K.GetProcessTimes(handle,*map(C.byref,times))
        start=str((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime)
        return code.value==259 and start==identity['start']
    finally:
        K.CloseHandle(handle)


def round_audit(path):
    summary=read(path/'summary.json')
    assert summary['cases']==summary['passed']==12
    assert summary['cleanup_passed'] and summary['supervisor_job_active_processes']==0
    assert summary['owned_processes']==34 and summary['cold_recovery_processes']==21 and summary['runtime_manifests_verified']==35
    assert summary['frozen_harness_unchanged']
    stages=['before_intent_commit','after_intent_commit','after_effect','before_result_commit','after_result_commit','checkpoint_before_commit','checkpoint_after_commit','event_before_commit']
    kills=[]
    for stage in stages:
        case=path/('sqlite-'+stage)
        ready, kill, result=read(case/'ready.json'),read(case/'kill.json'),read(case/'result.json')
        runtime=read(case/('runtime-db-'+stage)/'runtime.json')
        identity=ready['identity']
        assert ready['stage']==stage and result['passed']
        assert all(kill[key]==identity for key in ['handle_identity','spawn_identity','ready_identity','runtime_identity'])
        assert runtime['identity']==identity
        assert result['details']['killed_pid']==identity['pid'] and result['details']['exit_code']==1
        assert kill['createprocess_handle']==kill['kill_handle']
        assert kill['identity_read_from_retained_createprocess_handle'] and kill['handle_was_live']
        assert kill['exit_signaled_before_return'] and kill['wait_result']==0 and kill['exit_code']==1
        assert kill['worker_alive_after_wait'] is False and not is_alive(identity)
        assert kill['termination_requested_ns']<=kill['exit_confirmed_ns']
        assert result['details']['wal_existed_before_recovery'] and result['details']['integrity_check']=='ok'
        assert result['details']['pragmas']=={'journal_mode':'wal','synchronous':2,'busy_timeout':3000,'user_version':2}
        kills.append({'case':case.name,'identity':identity,'retained_handle':kill['kill_handle'],'wait_result':0,'exit_code':1,'worker_dead_immediately':True,'wait_ms':(kill['exit_confirmed_ns']-kill['termination_requested_ns'])/1e6})
    candidate=read(EXP/'candidate.json')
    manifests=[(file,read(file)) for file in path.rglob('runtime.json')]
    assert len(manifests)==35
    identities={(r['identity']['pid'],r['identity']['start']) for _,r in manifests}
    assert len(identities)==35
    for file,runtime in manifests:
        assert runtime['version']==candidate['expected_runtime'] and runtime['source_id']==candidate['expected_source_id']
        assert runtime['dll_sha256']==candidate['dll_sha256']
        assert sha(Path(runtime['dll']).read_bytes())==runtime['dll_sha256']
        assert sha(Path(runtime['driver_extension']).read_bytes())==runtime['driver_extension_sha256']
        assert runtime['vfs']['default_vfs']==runtime['vfs']['c_connection_fcntl_vfsname']=='win32'
        assert runtime['compile_options']==read(path/'runtime.json')['compile_options']
        assert not is_alive(runtime['identity'])
    recoveries=list(path.glob('sqlite-*/recovery-*.json'))
    assert len(recoveries)==21
    recovery_records=[]
    for file in recoveries:
        rec=read(file)
        mode='event' if 'checkpoint_' in file.parent.name else 'tool'
        number=file.stem.rsplit('-',1)[1]
        runtime=read(file.parent/f'runtime-recover-{mode}-{number}/runtime.json')
        assert rec['identity']==runtime['identity'] and not is_alive(rec['identity'])
        assert rec['effect_executions_in_recovery']==0 and rec['pending_events']==0
        recovery_records.append({'file':file.relative_to(path).as_posix(),'identity':rec['identity']})
    for name,expected in read(path/'harness-sha256.json').items():
        live=EXP.parent/'runtime'/name[7:] if name.startswith('frozen-') else EXP/name
        assert sha(live.read_bytes())==sha((path/'harness'/name).read_bytes())==expected
    for item in summary['results']:
        assert read(path/item['name']/'result.json')==item
    return {'path':str(path),'summary':{k:v for k,v in summary.items() if k!='results'},'kill_receipts':kills,'recovery_receipts':recovery_records,'all_35_actual_runtime_identities_unique_and_exited':True,'actual_manifests_and_harness_verified':True,'runtime':candidate['expected_runtime'],'source_id':candidate['expected_source_id'],'dll_sha256':candidate['dll_sha256']}


def main():
    assert git('rev-parse','HEAD').decode().strip()==MERGE
    assert git('rev-parse','impl/d19-sqlite-identity2').decode().strip()==CANDIDATE
    before=snapshot()
    assert before['fresh_default_runtime']=='3.45.1'
    save('before.json',before)
    save('archive-review.json',archives())
    save('candidate-round-review.json',round_audit(EXP/'evidence/n/c'))
    assert not BASE.exists(), 'never overwrite evidence'
    command=[sys.executable,'-m','pytest',str(EXP/'test_runtime.py'),'-q','--basetemp='+str(BASE),'-p','no:cacheprovider']
    save('command.json',{'utc':datetime.now(timezone.utc).isoformat(),'cwd':str(ROOT),'command':command,'merge':MERGE,'candidate':CANDIDATE})
    result=subprocess.run(command,capture_output=True,text=True,timeout=120)
    with (OUT/'pytest.txt').open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(result.stdout+result.stderr)
    assert result.returncode==0, result.stdout+result.stderr
    save('fresh-round-review.json',round_audit(BASE/'c'))
    simple=list(BASE.glob('test_actual*/runtime.json'))
    assert len(simple)==1 and not is_alive(read(simple[0])['identity'])
    after=snapshot()
    save('after.json',after)
    assert before==after, 'global runtime or frozen scripts changed'
    files=[]
    with zipfile.ZipFile(OUT/'fresh.zip','x',compression=zipfile.ZIP_DEFLATED) as bundle:
        for file in sorted(BASE.rglob('*')):
            if file.is_file():
                raw=file.read_bytes()
                name=file.relative_to(BASE).as_posix()
                bundle.writestr(name,raw)
                files.append({'member':name,'bytes':len(raw),'sha256':sha(raw)})
    with zipfile.ZipFile(OUT/'fresh.zip') as bundle:
        assert len(bundle.namelist())==len(files)
        for item in files:
            raw=bundle.read(item['member'])
            assert len(raw)==item['bytes'] and sha(raw)==item['sha256']
    save('fresh-manifest.json',{'archive_sha256':sha((OUT/'fresh.zip').read_bytes()),'member_count':len(files),'members':files})
    save('conclusion.json',{'merge':MERGE,'candidate':CANDIDATE,'pytest_exit':result.returncode,'original_environment_unchanged':True,'simple_test_runtime_also_exited':True,'fresh_round_raw_archive_members':len(files),'scope':'合成契约实验；非产品、wheel/standalone、真实模型、Windows Terminal 或断电验收。'})
    print(json.dumps({'merge':MERGE,'pytest':result.stdout.strip(),'raw_members':len(files),'output':str(OUT)},ensure_ascii=False))


if __name__=='__main__':
    main()

