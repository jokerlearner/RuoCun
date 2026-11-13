"""Read-only post-test audit of names actually created by this replay."""
import json
import ctypes as C
from ctypes import wintypes as W
from pathlib import Path
import pywintypes
import win32api
import win32cred
import win32gui
import win32job
import win32process
import win32service
import winreg
import native

ROOT = Path(__file__).resolve().parent.parent
OWNED = {'credentials': set(), 'jobs': set(), 'desktops': set(), 'stations': set(), 'classes': set()}
ICON_EVENTS = []


def journal():
    (ROOT / 'native-object-journal.json').write_text(json.dumps({
        'owned': {key: sorted(value) for key, value in OWNED.items()},
        'icon_events': ICON_EVENTS}, ensure_ascii=False, indent=2), encoding='utf-8')


def remember(module, function, group, argument=0):
    original = getattr(module, function)
    def wrapped(*args, **kwargs):
        value = args[argument]
        OWNED[group].add(value.lpszClassName if group == 'classes' else value)
        journal()
        return original(*args, **kwargs)
    setattr(module, function, wrapped)


remember(native, 'write_credential', 'credentials')
remember(win32job, 'CreateJobObject', 'jobs', 1)
remember(win32service, 'CreateDesktop', 'desktops')
remember(win32service, 'CreateWindowStation', 'stations')
remember(win32gui, 'RegisterClass', 'classes')
_shell_notify = win32gui.Shell_NotifyIcon
def shell_notify(operation, data):
    result = _shell_notify(operation, data)
    ICON_EVENTS.append({'operation': operation, 'hwnd': data[0], 'uid': data[1]})
    journal()
    return result
win32gui.Shell_NotifyIcon = shell_notify


def absent_query(name, query, expected):
    try:
        handle = query(name)
        if hasattr(handle, 'Close'):
            handle.Close()
        return {'name': name, 'absent': False}
    except pywintypes.error as exc:
        return {'name': name, 'absent': exc.winerror in expected, 'winerror': exc.winerror}


def class_query(name):
    user32 = C.WinDLL('user32', use_last_error=True)
    query = user32.GetClassInfoW
    query.argtypes = [W.HANDLE, W.LPCWSTR, C.c_void_p]
    query.restype = W.BOOL
    buffer = C.create_string_buffer(128)
    if not query(None, name, buffer):
        code = C.get_last_error()
        raise pywintypes.error(code, 'GetClassInfoW', C.FormatError(code))
    return True


def pytest_sessionfinish(session, exitstatus):
    report = {'test_exit': int(exitstatus), 'audit_scope': 'Only names and PIDs recorded by this m17 replay; no deletion, bare-PID kill, or mutation.'}
    report['credentials'] = [absent_query(n, lambda x: native.read_credential(x), {1168}) for n in sorted(OWNED['credentials'])]
    report['jobs'] = [absent_query(n, lambda x: win32job.OpenJobObject(4, False, x), {2}) for n in sorted(OWNED['jobs'])]
    report['desktops'] = [absent_query(n, lambda x: win32service.OpenDesktop(x, 0, False, 1), {2}) for n in sorted(OWNED['desktops'])]
    report['stations'] = [absent_query(n, lambda x: win32service.OpenWindowStation(x, False, 1), {2}) for n in sorted(OWNED['stations'])]
    report['window_classes'] = [absent_query(n, class_query, {1411}) for n in sorted(OWNED['classes'])]
    added = {(e['hwnd'], e['uid']) for e in ICON_EVENTS if e['operation'] == win32gui.NIM_ADD}
    deleted = {(e['hwnd'], e['uid']) for e in ICON_EVENTS if e['operation'] == win32gui.NIM_DELETE}
    report['notification'] = {'events': ICON_EVENTS, 'all_added_icons_deleted': added <= deleted,
        'all_owner_windows_destroyed': all(not win32gui.IsWindow(h) for h, _ in added)}
    profiles = []
    tasks = set()
    pids = {}
    for path in (ROOT / 'pytest').rglob('*.json'):
        try:
            value = json.loads(path.read_text('utf-8'))
        except (ValueError, UnicodeDecodeError):
            continue
        if path.name == 'isolate.json':
            if 'pid' in value:
                pids[value['pid']] = value.get('creation_time')
            for worker in value.get('workers', []):
                pids[worker['pid']] = worker.get('token', {}).get('creation_time_100ns')
            if 'package_sid' in value:
                key = 'Software\\Classes\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion\\AppContainer\\Mappings\\' + value['package_sid']
                mapping_exists = False
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key):
                        mapping_exists = True
                except FileNotFoundError:
                    pass
                folder = Path(value['profile_folder'])
                # Package root as well as the returned LocalState-like path.
                package = Path.home() / 'AppData/Local/Packages' / value['profile']
                profiles.append({'profile': value['profile'], 'sid': value['package_sid'],
                    'mapping_absent': not mapping_exists, 'returned_folder_absent': not folder.exists(),
                    'package_folder_absent': not package.exists()})
        if path.name in {'schedule.json','sched-limits.json'}:
            if value.get('task_name'):
                tasks.add(value['task_name'])
            tasks.update(value.get('task_names', []))
        if path.name == 'clipboard.json' and value.get('private_station_name'):
            report['stations'].append(absent_query(value['private_station_name'], lambda x: win32service.OpenWindowStation(x, False, 1), {2}))
        if path.name.startswith('receipt-') and 'pid' in value:
            pids[value['pid']] = value.get('token', {}).get('creation_time_100ns')
    import win32com.client
    service = win32com.client.Dispatch('Schedule.Service')
    service.Connect()
    folder = service.GetFolder('\\')
    task_results = []
    for name in sorted(tasks):
        try:
            folder.GetTask(name)
            task_results.append({'name': name, 'absent': False})
        except pywintypes.com_error as exc:
            code = exc.excepinfo[-1] if exc.excepinfo else exc.hresult
            task_results.append({'name': name, 'absent': code & 0xffffffff == 0x80070002, 'hresult': code})
    process_results = []
    for pid, creation in sorted(pids.items()):
        try:
            handle = win32api.OpenProcess(0x1000, False, pid)
            try:
                process_results.append({'pid': pid, 'recorded_creation': creation,
                    'absent_or_exited': win32process.GetExitCodeProcess(handle) != 259})
            finally:
                handle.Close()
        except pywintypes.error as exc:
            process_results.append({'pid': pid, 'recorded_creation': creation,
                'absent_or_exited': exc.winerror in {87,1168}, 'winerror': exc.winerror})
    report.update(profiles=profiles, tasks=task_results, processes=process_results)
    report['all_recorded_objects_absent'] = (
        all(item['absent'] for group in ['credentials','jobs','desktops','stations','window_classes'] for item in report[group])
        and report['notification']['all_added_icons_deleted'] and report['notification']['all_owner_windows_destroyed']
        and all(all(item[key] for key in ['mapping_absent','returned_folder_absent','package_folder_absent']) for item in profiles)
        and all(item['absent'] for item in task_results) and all(item['absent_or_exited'] for item in process_results))
    (ROOT / 'native-object-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
