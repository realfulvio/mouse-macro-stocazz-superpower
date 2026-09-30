# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

# flet legge icons.json/cupertino_icons.json dal proprio package a runtime
# (non tramite import), quindi PyInstaller non li rileva da solo e vanno
# raccolti esplicitamente come data files.
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    # vendor/flet-windows.zip = client grafico ufficiale di Flet (release GitHub della
    # stessa versione di flet): incorporato, flet non lo scarica al primo avvio, quindi
    # l'exe funziona offline e non ha il comportamento "scarica ed esegui" che fa
    # scattare gli antivirus.
    datas=[('assets', 'assets'), ('vendor/flet-windows.zip', 'flet_desktop/app')] + collect_data_files('flet'),
    hiddenimports=['flet_desktop', 'flet_desktop.win_taskbar', 'flet_desktop.version'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Mouse Macro Stocazz Superpower',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX comprime l'eseguibile ma e' una delle cause piu' comuni di falsi
    # positivi antivirus (i motori euristici la associano a packer/malware).
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
    version='version_info.txt',
)
