"""Acceptance of an exact Windows ZIP; runs only on a disposable Windows runner."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import winreg
import zipfile

import run_tool
import reference_macro
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[2]
U, K = C.windll.user32, C.windll.kernel32
for dll, name, result, args in (
    (U, 'FindWindowW', W.HWND, [W.LPCWSTR, W.LPCWSTR]),
    (U, 'GetDlgItem', W.HWND, [W.HWND, C.c_int]),
    (U, 'SendMessageW', C.c_ssize_t, [W.HWND, W.UINT, W.WPARAM, W.LPARAM]),
    (U, 'PostMessageW', W.BOOL, [W.HWND, W.UINT, W.WPARAM, W.LPARAM]),
    (U, 'GetWindowTextW', C.c_int, [W.HWND, W.LPWSTR, C.c_int]),
    (U, 'GetWindowThreadProcessId', W.DWORD, [W.HWND, C.POINTER(W.DWORD)]),
    (K, 'OpenProcess', W.HANDLE, [W.DWORD, W.BOOL, W.DWORD]),
    (K, 'QueryFullProcessImageNameW', W.BOOL, [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]),
    (K, 'CloseHandle', W.BOOL, [W.HANDLE]),
):
    fn = getattr(dll, name); fn.restype, fn.argtypes = result, args


def wait(fn, what, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        result = fn()
        if result:
            return result
        time.sleep(.05)
    raise AssertionError('Timeout: ' + what)


def panel_check(package, version, out, name):
    hwnd = wait(lambda: U.FindWindowW('MouseMacroSuperpower017', None), 'pannello')
    title = C.create_unicode_buffer(1024); U.GetWindowTextW(hwnd, title, len(title))
    assert version in title.value, title.value
    pid = W.DWORD(); U.GetWindowThreadProcessId(hwnd, C.byref(pid))
    process = K.OpenProcess(0x1000, False, pid.value)
    assert process
    try:
        path = C.create_unicode_buffer(32768); length = W.DWORD(len(path))
        assert K.QueryFullProcessImageNameW(process, 0, path, C.byref(length))
        assert Path(path.value).resolve() == (package / 'runtime/pythonw.exe').resolve(), path.value
    finally:
        K.CloseHandle(process)
    time.sleep(1)  # let the native window paint before the evidence screenshot
    ImageGrab.grab(all_screens=True).save(out / (name + '.png'))
    U.PostMessageW(hwnd, 0x10, 0, 0)
    wait(lambda: not U.FindWindowW('MouseMacroSuperpower017', None), 'chiusura pannello')
    return dict(title=title.value, interpreter=path.value, passed=True)


def launcher(package, version, install, out):
    proc = subprocess.Popen([str(package / f'Mouse Macro v{version}.exe')], cwd=package)
    dialog = wait(lambda: U.FindWindowW('#32770', 'Mouse Macro ' + version), 'domanda installazione')
    button = U.GetDlgItem(dialog, 6 if install else 7)  # IDYES / IDNO
    assert button
    U.SendMessageW(button, 0xF5, 0, 0)  # BM_CLICK
    assert proc.wait(timeout=30) == 0
    target = package
    if install:
        home = Path(os.environ['LOCALAPPDATA']) / 'MouseMacroStocazzSuperpower'
        target = home / 'Portable' / package.name
        assert (home / 'Mouse Macro Stocazz Superpower.exe').is_file()
        key = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\MouseMacroStocazzSuperpower'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            assert winreg.QueryValueEx(handle, 'DisplayVersion')[0] == version
        folders = json.loads(subprocess.check_output(['pwsh', '-NoProfile', '-Command',
            "@([Environment]::GetFolderPath('Programs'),[Environment]::GetFolderPath('DesktopDirectory')) | ConvertTo-Json -Compress"], text=True))
        assert all((Path(folder) / 'Mouse Macro Stocazz Superpower.lnk').is_file() for folder in folders)
    return panel_check(target, version, out, 'installed' if install else 'portable-exe')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', required=True)
    ap.add_argument('--sha256', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--expect-warning', action='store_true')
    a = ap.parse_args()
    archive, out = Path(a.archive).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert digest == a.sha256, 'hash ZIP diverso dal candidato'
    result = dict(archive_sha256=digest, checks={}, passed=False)
    try:
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            prefix = z.namelist()[0].split('/')[0] + '/'
            assert all(p.startswith(prefix) and '..' not in Path(p).parts for p in z.namelist())
            manifest = json.loads(z.read(prefix + 'build_info.json'))
            for name, expected in manifest['sha256'].items():
                assert hashlib.sha256(z.read(prefix + name)).hexdigest() == expected, name
            z.extractall(out / 'extracted')
        package = out / 'extracted' / prefix.rstrip('/')
        version = manifest['version']; result['version'] = version
        if a.expect_warning:
            assert (package / 'app/macro/windows_integrity.py').is_file()
        w, h = run_tool.set_display(); result['screen'] = [w, h]
        result['checks']['portable_exe'] = launcher(package, version, False, out)
        subprocess.Popen(['cmd.exe', '/c', str(package / f'Mouse Macro v{version} (senza exe).cmd')], cwd=package)
        result['checks']['cmd'] = panel_check(package, version, out, 'portable-cmd')
        result['checks']['install'] = launcher(package, version, True, out)
        ref = out / 'reference.mmr'
        ref.write_text(json.dumps(reference_macro.to_mmr(reference_macro.build(w, h), w, h, 0, 0)))
        python = str(package / 'runtime/python.exe')
        base = [python, str(ROOT / 'bench/ci/profile_idle.py'), '--app-root', str(package / 'app')]
        def probe(name, cmd, timeout=180, required=()):
            p = subprocess.run(cmd, capture_output=True, text=True, errors='replace', timeout=timeout)
            (out / (name + '.txt')).write_text(p.stdout + p.stderr, encoding='utf-8')
            assert p.returncode == 0, name + ': ' + p.stderr[-1000:]
            records = [json.loads(line.split(' ', 1)[1]) for line in p.stdout.splitlines() if line.startswith('RISULTATO ')]
            assert all('error' not in r and 'riferimento_errore' not in r for r in records), records
            if required:
                assert len(records) == 1 and all(k in records[0] for k in required), (name, records)
                provenance = [json.loads(line.split(' ', 1)[1]) for line in p.stdout.splitlines() if line.startswith('PROVENIENZA ')]
                assert len(provenance) == 1, provenance
                assert Path(provenance[0]['app']).resolve() == (package / 'app/windows_main.py').resolve(), provenance
                assert Path(provenance[0]['interprete']).resolve() == Path(python), provenance
            result['checks'][name] = records or {'passed': True}
        probe('pixels', base + ['--mode', 'verify'])
        for i in range(3):
            probe('idle_' + str(i), base + ['--mode', 'cpu', '--warm', '10', '--window', '20'], required=('cpu_pct_of_core',))
            probe('active_' + str(i), base + ['--mode', 'active', '--warm', '8', '--window', '15', '--macro', str(ref)], required=('registrazione_cpu_pct', 'riproduzione_cpu_pct', 'riproduzione_riferimento_cpu_pct'))
        cmd = [sys.executable, str(ROOT / 'bench/ci/uipi_test.py'), '--out', str(out / 'uipi'),
               '--app-python', python, '--app-root', str(package / 'app')]
        if a.expect_warning:
            cmd += ['--expect-warning']
        probe('uipi', cmd, 400)
        result['passed'] = True
    finally:
        (out / 'acceptance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print('PACKAGE_ACCEPTANCE', json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
