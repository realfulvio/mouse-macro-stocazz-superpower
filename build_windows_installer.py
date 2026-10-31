"""Build the Windows setup program from the package folder of build_native_windows.py.

Run it after build_native_windows.py, on Windows with Inno Setup 6. The setup
installs exactly the files of the ZIP (minus the portable launchers) and its
SHA-256 is added to the same SHA256SUMS file used by the updater.
"""
from pathlib import Path
import hashlib, os, shutil, struct, subprocess, sys
from build_native_windows import ROOT, PACKAGE, VERSION

SETUP = f'MouseMacroStocazzSuperpower-Setup-v{VERSION}.exe'


def find_iscc():
    candidates = [os.environ.get('ISCC'), shutil.which('ISCC'), shutil.which('iscc')]
    for base in (os.environ.get('ProgramFiles(x86)'), os.environ.get('ProgramFiles'), os.environ.get('LOCALAPPDATA')):
        if base:
            candidates.append(str(Path(base)/'Inno Setup 6'/'ISCC.exe'))
            candidates.append(str(Path(base)/'Programs'/'Inno Setup 6'/'ISCC.exe'))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise SystemExit('Inno Setup 6 non trovato: installalo o imposta ISCC.')


def main():
    stage = ROOT/'build'/'native'/PACKAGE
    if not (stage/'runtime'/'pythonw.exe').is_file() or not (stage/'app'/'windows_main.py').is_file():
        raise SystemExit('Prima esegui build_native_windows.py')
    out = ROOT/'dist'/'windows'
    sums = out/f'SHA256SUMS-v{VERSION}.txt'
    if not sums.is_file():
        raise SystemExit(f'{sums.name} mancante: prima esegui build_native_windows.py')
    subprocess.run([find_iscc(), '/Qp', f'/DAppVersion={VERSION}', f'/DSource={stage}', f'/DOutputDir={out}',
                    str(ROOT/'installer'/'MouseMacroStocazzSuperpower.iss')], check=True)
    setup = out/SETUP
    data = setup.read_bytes()
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    if data[:2] != b'MZ' or data[pe:pe+4] != b'PE\0\0':
        raise SystemExit('Il setup prodotto non è un eseguibile Windows')
    digest = hashlib.sha256(data).hexdigest()
    lines = [line for line in sums.read_text('ascii').splitlines() if not line.endswith('  '+SETUP)]
    sums.write_text('\n'.join([*lines, f'{digest}  {SETUP}'])+'\n', 'ascii')
    print(str(setup), digest, flush=True)


if __name__ == '__main__':
    main()
