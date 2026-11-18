#!/usr/bin/env python3
"""Paired comparison of two exact Windows ZIPs on the SAME runner (order ABBA).

Separate jobs land on different hosts (Intel vs AMD, different load), so a CPU
difference between them says little about the code. Here both packages run on
one host, alternating, and every metric is reported per run and as medians:

  startup   from CreateProcess to a visible panel whose message loop answers
            (WM_NULL), pythonw.exe -B app/windows_main.py as the launchers do;
  idle      process CPU (% of one core), private memory, GDI/USER objects and
            handles of the running panel, at the start and at the end of a window
            (growth = leak);
  active    CPU while recording and while replaying (bench/ci/profile_idle.py
            --mode active, run with the package's own python.exe and app);
  imports   -X importtime of `import windows_main` (one run each, for the cost
            breakdown, not for the comparison).

The update check is switched off in the settings file for the whole comparison:
both versions would otherwise query the GitHub API at every start and the rate
limit (60 requests per hour) would decide what is measured.

  python bench/ci/paired_compare.py --baseline a.zip --candidate b.zip --out paired
"""
import argparse
import ctypes
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'bench'), str(ROOT / 'bench' / 'ci')]
CLASS = 'MouseMacroSuperpower017'
SETTINGS = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'MouseMacroStocazzSuperpower' / 'panel-v016.json'

u = ctypes.WinDLL('user32', use_last_error=True)
k = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi')


class PMC(ctypes.Structure):  # PROCESS_MEMORY_COUNTERS_EX
    _fields_ = [('cb', W.DWORD), ('PageFaultCount', W.DWORD), ('PeakWorkingSetSize', ctypes.c_size_t),
                ('WorkingSetSize', ctypes.c_size_t), ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                ('QuotaPagedPoolUsage', ctypes.c_size_t), ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                ('QuotaNonPagedPoolUsage', ctypes.c_size_t), ('PagefileUsage', ctypes.c_size_t),
                ('PeakPagefileUsage', ctypes.c_size_t), ('PrivateUsage', ctypes.c_size_t)]


for fn, res, args in (
        (u.FindWindowW, W.HWND, [W.LPCWSTR, W.LPCWSTR]),
        (u.IsWindowVisible, W.BOOL, [W.HWND]),
        (u.GetWindowThreadProcessId, W.DWORD, [W.HWND, ctypes.POINTER(W.DWORD)]),
        (u.SendMessageTimeoutW, ctypes.c_ssize_t, [W.HWND, W.UINT, W.WPARAM, W.LPARAM, W.UINT, W.UINT,
                                                   ctypes.POINTER(ctypes.c_size_t)]),
        (u.PostMessageW, W.BOOL, [W.HWND, W.UINT, W.WPARAM, W.LPARAM]),
        (u.GetGuiResources, W.DWORD, [W.HANDLE, W.DWORD]),
        (k.OpenProcess, W.HANDLE, [W.DWORD, W.BOOL, W.DWORD]),
        (k.CloseHandle, W.BOOL, [W.HANDLE]),
        (k.GetProcessTimes, W.BOOL, [W.HANDLE] + [ctypes.POINTER(ctypes.c_ulonglong)] * 4),
        (k.GetProcessHandleCount, W.BOOL, [W.HANDLE, ctypes.POINTER(W.DWORD)]),
        (psapi.GetProcessMemoryInfo, W.BOOL, [W.HANDLE, ctypes.POINTER(PMC), W.DWORD])):
    fn.restype, fn.argtypes = res, args


def extract(archive, dest):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, archive
        prefix = z.namelist()[0].split('/')[0]
        z.extractall(dest)
    package = Path(dest) / prefix
    assert (package / 'runtime' / 'pythonw.exe').is_file() and (package / 'app' / 'windows_main.py').is_file()
    version = json.loads((package / 'build_info.json').read_text('utf-8'))['version']
    return package, version


def quiet_settings():
    """No network at start (see the module docstring); every other preference stays default."""
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(SETTINGS.read_text('utf-8'))
    except (OSError, ValueError):
        data = {}
    data = data if isinstance(data, dict) else {}
    data.update(check_updates=False, skin='bambola', skin_default='bambola', position=[1500, 40])
    SETTINGS.write_text(json.dumps(data), 'utf-8')


def panel_of(pid):
    hwnd = u.FindWindowW(CLASS, None)
    if not hwnd:
        return None
    owner = W.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
    return hwnd if owner.value == pid else None


def launch(package):
    return subprocess.Popen([str(package / 'runtime' / 'pythonw.exe'), '-B', str(package / 'app' / 'windows_main.py')],
                            cwd=package)


def close(proc):
    hwnd = panel_of(proc.pid)
    if hwnd:
        u.PostMessageW(hwnd, 0x10, 0, 0)  # WM_CLOSE, as the title-bar button
    try:
        proc.wait(timeout=20)
        return True
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)
        return False


def wait_gone(seconds=10):
    end = time.monotonic() + seconds
    while u.FindWindowW(CLASS, None) and time.monotonic() < end:
        time.sleep(0.05)


def startup_once(package):
    wait_gone()
    t0 = time.perf_counter()
    proc = launch(package)
    visible = ready = None
    result = ctypes.c_size_t()
    while time.perf_counter() - t0 < 30:
        hwnd = panel_of(proc.pid)
        if hwnd and u.IsWindowVisible(hwnd):
            if visible is None:
                visible = time.perf_counter() - t0
            if u.SendMessageTimeoutW(hwnd, 0, 0, 0, 0x2, 5000, ctypes.byref(result)):  # WM_NULL, SMTO_ABORTIFHUNG
                ready = time.perf_counter() - t0
                break
        time.sleep(0.001)
    time.sleep(0.5)  # let it paint and start its threads before closing
    clean = close(proc)
    return {'visible_s': visible, 'ready_s': ready, 'clean_exit': clean}


class Probe:
    def __init__(self, pid):
        self.handle = k.OpenProcess(0x1000 | 0x0010, False, pid)  # QUERY_LIMITED_INFORMATION | VM_READ
        assert self.handle, ctypes.get_last_error()

    def cpu(self):
        c, e, kt, ut = (ctypes.c_ulonglong() for _ in range(4))
        assert k.GetProcessTimes(self.handle, *(ctypes.byref(v) for v in (c, e, kt, ut)))
        return (kt.value + ut.value) / 1e7

    def snapshot(self):
        pmc = PMC(); pmc.cb = ctypes.sizeof(PMC)
        assert psapi.GetProcessMemoryInfo(self.handle, ctypes.byref(pmc), pmc.cb)
        handles = W.DWORD(); k.GetProcessHandleCount(self.handle, ctypes.byref(handles))
        return {'private_mib': round(pmc.PrivateUsage / 2**20, 2), 'working_set_mib': round(pmc.WorkingSetSize / 2**20, 2),
                'gdi': u.GetGuiResources(self.handle, 0), 'user': u.GetGuiResources(self.handle, 1),
                'handles': handles.value}

    def close(self):
        k.CloseHandle(self.handle)


def idle_once(package, warm, window):
    wait_gone()
    proc = launch(package)
    end = time.monotonic() + 30
    while not panel_of(proc.pid) and time.monotonic() < end:
        time.sleep(0.05)
    assert panel_of(proc.pid), 'pannello non comparso'
    time.sleep(warm)
    probe = Probe(proc.pid)
    try:
        first = probe.snapshot()
        c0, t0 = probe.cpu(), time.perf_counter()
        peak = first['private_mib']
        while time.perf_counter() - t0 < window:
            time.sleep(1)
            peak = max(peak, probe.snapshot()['private_mib'])
        c1, t1 = probe.cpu(), time.perf_counter()
        last = probe.snapshot()
    finally:
        probe.close()
        clean = close(proc)
    return {'cpu_pct_of_core': round(100 * (c1 - c0) / (t1 - t0), 3), 'private_mib_max': peak,
            'start': first, 'end': last, 'clean_exit': clean}


def active_once(package, macro, warm, window):
    wait_gone()
    python = package / 'runtime' / 'python.exe'
    cmd = [str(python), str(ROOT / 'bench/ci/profile_idle.py'), '--app-root', str(package / 'app'),
           '--mode', 'active', '--warm', str(warm), '--window', str(window), '--macro', str(macro)]
    p = subprocess.run(cmd, capture_output=True, text=True, errors='replace', timeout=300)
    records = [json.loads(line.split(' ', 1)[1]) for line in p.stdout.splitlines() if line.startswith('RISULTATO ')]
    assert p.returncode == 0 and len(records) == 1 and 'error' not in records[0], (p.returncode, p.stdout[-2000:], p.stderr[-2000:])
    return records[0]


def import_profile(package):
    """Cumulative import time per top-level module of `import windows_main` (microseconds)."""
    python = package / 'runtime' / 'python.exe'
    p = subprocess.run([str(python), '-X', 'importtime', '-B', '-c', 'import windows_main'], cwd=package / 'app',
                       capture_output=True, text=True, errors='replace', timeout=120)
    rows = []
    for line in p.stderr.splitlines():
        if line.startswith('import time:') and '|' in line and 'self [us]' not in line:
            self_us, cumulative, name = (part.strip() for part in line[len('import time:'):].split('|'))
            rows.append((int(cumulative), int(self_us), name))
    top = [r for r in rows if not r[2].startswith(' ')]
    script = subprocess.run([str(python), '-B', '-c',
                             "import time;s=open('windows_main.py','rb').read();t=time.perf_counter();"
                             "compile(s,'windows_main.py','exec');print(time.perf_counter()-t)"],
                            cwd=package / 'app', capture_output=True, text=True, timeout=60)
    return {'total_ms': round(sum(r[0] for r in top) / 1000, 1),
            'top': [{'module': n.strip(), 'cumulative_ms': round(c / 1000, 2), 'self_ms': round(s / 1000, 2)}
                    for c, s, n in sorted(rows, reverse=True)[:30]],
            'compile_windows_main_ms': round(float(script.stdout.strip() or 'nan') * 1000, 2),
            'returncode': p.returncode}


def median(values):
    values = [v for v in values if v is not None]
    return round(statistics.median(values), 4) if values else None


def ratio(a, b):
    return round(b / a, 4) if a else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--startups', type=int, default=20, help='per package')
    ap.add_argument('--idle-rounds', type=int, default=4, help='per package')
    ap.add_argument('--idle-warm', type=float, default=10)
    ap.add_argument('--idle-window', type=float, default=20)
    ap.add_argument('--active-rounds', type=int, default=2, help='per package')
    a = ap.parse_args()
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    import run_tool, reference_macro
    width, height = run_tool.set_display()
    packages, info = {}, {}
    for role, archive in (('baseline', a.baseline), ('candidate', a.candidate)):
        archive = Path(archive).resolve()
        package, version = extract(archive, out / role)
        packages[role] = package
        info[role] = {'version': version, 'zip_bytes': archive.stat().st_size,
                      'zip_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                      'files': sum(1 for p in package.rglob('*') if p.is_file())}
    macro = out / 'reference.mmr'
    macro.write_text(json.dumps(reference_macro.to_mmr(reference_macro.build(width, height), width, height, 0, 0)))
    quiet_settings()
    order = lambda n: [('baseline', 'candidate') if i % 2 == 0 else ('candidate', 'baseline') for i in range(n)]
    runs = {role: {'startup': [], 'idle': [], 'active': []} for role in packages}
    result = {'screen': [width, height], 'cpu': os.environ.get('PROCESSOR_IDENTIFIER', ''), 'packages': info, 'runs': runs}

    def save():
        (out / 'paired.json').write_text(json.dumps(result, indent=1), 'utf-8')

    for role in packages:  # cold-ish first start of each package: discarded, it fills the file cache
        startup_once(packages[role])
    for pair in order(a.startups):
        for role in pair:
            runs[role]['startup'].append(startup_once(packages[role]))
    save()
    for pair in order(a.idle_rounds):
        for role in pair:
            runs[role]['idle'].append(idle_once(packages[role], a.idle_warm, a.idle_window))
            print('IDLE', role, json.dumps(runs[role]['idle'][-1]), flush=True)
    save()
    for pair in order(a.active_rounds):
        for role in pair:
            runs[role]['active'].append(active_once(packages[role], macro, 8, 15))
            print('ACTIVE', role, json.dumps(runs[role]['active'][-1]), flush=True)
    save()
    result['imports'] = {role: import_profile(packages[role]) for role in packages}

    def row(name, values, unit, lower_is_better=True):
        base, cand = median(values('baseline')), median(values('candidate'))
        return {'metric': name, 'unit': unit, 'baseline': base, 'candidate': cand,
                'candidate_over_baseline': ratio(base, cand)}

    st = lambda key: (lambda role: [r[key] for r in runs[role]['startup']])
    idle = lambda key: (lambda role: [r[key] for r in runs[role]['idle']])
    growth = lambda key: (lambda role: [r['end'][key] - r['start'][key] for r in runs[role]['idle']])
    act = lambda key: (lambda role: [r.get(key) for r in runs[role]['active']])
    table = [
        row('Avvio: pannello visibile', st('visible_s'), 's'),
        row('Avvio: pannello pronto (risponde)', st('ready_s'), 's'),
        row('CPU a riposo', idle('cpu_pct_of_core'), '% di un core'),
        row('Memoria privata a riposo, massimo', idle('private_mib_max'), 'MiB'),
        row('Oggetti GDI a riposo (fine finestra)', lambda r: [x['end']['gdi'] for x in runs[r]['idle']], 'n'),
        row('Crescita oggetti GDI nella finestra', growth('gdi'), 'n'),
        row('Crescita handle nella finestra', growth('handles'), 'n'),
        row('Crescita memoria privata nella finestra', growth('private_mib'), 'MiB'),
        row('CPU in registrazione', act('registrazione_cpu_pct'), '% di un core'),
        row('CPU in riproduzione (flusso denso)', act('riproduzione_cpu_pct'), '% di un core'),
        row('CPU in riproduzione (macro di riferimento)', act('riproduzione_riferimento_cpu_pct'), '% di un core'),
        {'metric': 'Pacchetto ZIP', 'unit': 'MB', 'baseline': round(info['baseline']['zip_bytes'] / 1e6, 3),
         'candidate': round(info['candidate']['zip_bytes'] / 1e6, 3),
         'candidate_over_baseline': ratio(info['baseline']['zip_bytes'], info['candidate']['zip_bytes'])},
        {'metric': 'Tempo di import di windows_main (1 prova)', 'unit': 'ms',
         'baseline': result['imports']['baseline']['total_ms'], 'candidate': result['imports']['candidate']['total_ms'],
         'candidate_over_baseline': ratio(result['imports']['baseline']['total_ms'], result['imports']['candidate']['total_ms'])},
    ]
    result['summary'] = table
    save()
    lines = [f"### Confronto appaiato sullo stesso host: {info['baseline']['version']} → {info['candidate']['version']}",
             '', f"Host: `{result['cpu']}`, schermo {width}x{height}. Ordine ABBA. Mediane.", '',
             '| Misura | Unità | Base | Candidato | Candidato/Base |', '|---|---|---:|---:|---:|']
    for r in table:
        lines.append(f"| {r['metric']} | {r['unit']} | {r['baseline']} | {r['candidate']} | {r['candidate_over_baseline']} |")
    summary = '\n'.join(lines) + '\n'
    (out / 'paired.md').write_text(summary, 'utf-8')
    print(summary, flush=True)
    print('PAIRED', json.dumps(table), flush=True)
    for role in packages:
        print('IMPORTS', role, json.dumps(result['imports'][role]), flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(summary)


if __name__ == '__main__':
    main()
