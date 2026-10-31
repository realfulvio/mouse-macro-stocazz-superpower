"""Linux desktop integration without a terminal.

- input_access(): what the program can use right now (mouse, keyboard, uinput);
- grant_access(): installs the uaccess udev rule through pkexec, so the system's
  graphical password prompt replaces `sudo` in a terminal;
- integrate_appimage(): adds the portable AppImage to the applications menu,
  so after the first double click it is also found in the menu;
- missing_libraries() and startup_failure(): when the window cannot open, tell
  the user why instead of exiting silently.
"""
from __future__ import annotations

import glob
import os
from pathlib import Path
import shutil
import subprocess

RULE_FILE = '/etc/udev/rules.d/70-mouse-macro.rules'
# Kept identical to scripts/setup-linux-input.sh (checked by the tests).
RULES = """# Mouse Macro: mouse recording and global shortcut devices, active seat only.
SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_INPUT_MOUSE}=="1", TAG+="uaccess"
SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_INPUT_KEYBOARD}=="1", TAG+="uaccess"
SUBSYSTEM=="misc", KERNEL=="uinput", TAG+="uaccess"
"""
# Run as root by pkexec, read from standard input: the AppImage mount and the
# PyInstaller folder are often not readable by root, stdin always is.
GRANT_SCRIPT = f"""set -e
modprobe uinput 2>/dev/null || true
mkdir -p /etc/udev/rules.d
cat > {RULE_FILE}.tmp <<'RULES'
{RULES}RULES
mv -f {RULE_FILE}.tmp {RULE_FILE}
udevadm control --reload-rules
udevadm trigger --subsystem-match=input --action=change
udevadm trigger --subsystem-match=misc --action=change
udevadm settle --timeout=10 || true
"""
APP_ID = 'mouse-macro-stocazz-superpower'
DESKTOP_NAME = f'{APP_ID}.desktop'
# The prebuilt Flet window always reports this class: the menu entry claims it so
# the taskbar shows the program icon instead of a generic one.
WM_CLASS = 'com.appveyor.flet'


def clean_env(env=None):
    """Environment for external programs: a PyInstaller binary points
    LD_LIBRARY_PATH at its own bundled libraries, which can break system tools."""
    env = dict(os.environ if env is None else env)
    for name in ('LD_LIBRARY_PATH', 'LD_PRELOAD'):
        original = env.pop(f'{name}_ORIG', None)
        if original:
            env[name] = original
        else:
            env.pop(name, None)
    return env


def in_flatpak():
    return bool(os.environ.get('FLATPAK_ID')) or os.path.exists('/.flatpak-info')


def _usable(path, mode):
    try:
        fd = os.open(path, mode | os.O_NONBLOCK)
    except OSError:
        return False
    os.close(fd)
    return True


def input_access(devices_glob='/dev/input/event*', uinput='/dev/uinput'):
    """True/False per capability. `events` is True when at least one input
    device can be read: without the rule none of them can."""
    events = [path for path in sorted(glob.glob(devices_glob))]
    return {
        'events': any(_usable(path, os.O_RDONLY) for path in events),
        'uinput': _usable(uinput, os.O_WRONLY),
        'rule': os.path.exists(RULE_FILE),
    }


def can_grant():
    """The graphical prompt needs pkexec on the host (not inside Flatpak)."""
    return not in_flatpak() and shutil.which('pkexec') is not None


def grant_access(timeout=300):
    """Install the rule with the system password prompt. Returns (ok, detail)."""
    pkexec = shutil.which('pkexec')
    if in_flatpak() or not pkexec:
        return False, 'pkexec non disponibile'
    try:
        done = subprocess.run([pkexec, '/bin/sh', '-s'], input=GRANT_SCRIPT, text=True,
                              capture_output=True, timeout=timeout, env=clean_env())
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)
    if done.returncode in (126, 127):  # dialog dismissed or not authorized
        return False, 'annullato'
    if done.returncode:
        return False, (done.stderr or done.stdout or f'codice {done.returncode}').strip()
    return True, ''


def integrate_appimage(appimage=None, icon=None, data_home=None):
    """Menu entry for the portable AppImage, refreshed at every start so it
    follows renames and in-app updates. Returns the desktop file or None."""
    appimage = appimage or os.environ.get('APPIMAGE')
    if not appimage or not os.path.isfile(appimage) or os.environ.get('MMSS_NO_DESKTOP_ENTRY'):
        return None
    data = Path(data_home or os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share')
    applications = data / 'applications'
    icons = data / 'icons' / 'hicolor' / '256x256' / 'apps'
    icon_name = APP_ID
    try:
        if icon and Path(icon).is_file():
            icons.mkdir(parents=True, exist_ok=True)
            target = icons / f'{APP_ID}.png'
            if not target.exists() or target.read_bytes() != Path(icon).read_bytes():
                shutil.copyfile(icon, target)
            icon_name = str(target)
        applications.mkdir(parents=True, exist_ok=True)
        quoted = '"' + str(appimage).replace('\\', '\\\\').replace('"', '\\"') + '"'
        text = ('[Desktop Entry]\nType=Application\nName=Mouse Macro Stocazz Superpower\n'
                'Comment=Registra e riproduce i gesti del mouse\n'
                'Comment[en]=Record and replay mouse gestures\n'
                f'Exec={quoted}\nTryExec={appimage}\nIcon={icon_name}\nTerminal=false\n'
                f'Categories=Utility;\nStartupWMClass={WM_CLASS}\nX-AppImage-Integrate=false\n')
        desktop = applications / DESKTOP_NAME
        if not desktop.exists() or desktop.read_text(encoding='utf-8', errors='replace') != text:
            temporary = desktop.with_suffix('.tmp')
            temporary.write_text(text, encoding='utf-8')
            os.replace(temporary, desktop)
        return desktop
    except OSError:
        return None


def flet_clients(home=None):
    root = Path(home or Path.home()) / '.flet' / 'client'
    return sorted(root.glob('flet-desktop-*/flet/flet'), key=lambda p: p.stat().st_mtime, reverse=True)


def missing_libraries(binary):
    """Shared libraries the Flet window needs but the system lacks (from ldd)."""
    ldd = shutil.which('ldd')
    if not ldd or not binary:
        return []
    lib = Path(binary).parent / 'lib'
    env = clean_env()
    env['LD_LIBRARY_PATH'] = ':'.join(filter(None, [str(lib), env.get('LD_LIBRARY_PATH')]))
    missing = []
    for item in [Path(binary), *sorted(lib.glob('*.so'))]:
        try:
            out = subprocess.run([ldd, str(item)], capture_output=True, text=True, timeout=20, env=env).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        for line in out.splitlines():
            name, _, rest = line.strip().partition(' => ')
            if 'not found' in rest and name not in missing:
                missing.append(name)
    return missing


PACKAGES = {  # library: (Debian/Ubuntu, Fedora, Arch)
    'libsecret-1.so.0': ('libsecret-1-0', 'libsecret', 'libsecret'),
    'libgtk-3.so.0': ('libgtk-3-0', 'gtk3', 'gtk3'),
    'libEGL.so.1': ('libegl1', 'libglvnd-egl', 'libglvnd'),
    'libGL.so.1': ('libgl1', 'libglvnd-glx', 'libglvnd'),
    'libmpv.so.2': ('libmpv2', 'mpv-libs', 'mpv'),
    'libgstreamer-1.0.so.0': ('libgstreamer1.0-0', 'gstreamer1', 'gstreamer'),
}


def install_hint(missing):
    debian, fedora, arch = (sorted({PACKAGES[n][i] for n in missing if n in PACKAGES}) for i in range(3))
    if not debian:
        return ''
    return (f'Ubuntu/Debian: sudo apt install {" ".join(debian)}\n'
            f'Fedora: sudo dnf install {" ".join(fedora)}\n'
            f'Arch/CachyOS: sudo pacman -S {" ".join(arch)}')


def show_message(title, text):
    """Best-effort message box without the Flet window (which failed to open)."""
    env = clean_env()
    for command in (['zenity', '--error', '--no-wrap', f'--title={title}', f'--text={text}'],
                    ['kdialog', '--title', title, '--error', text],
                    ['notify-send', '-u', 'critical', '-a', title, title, text]):
        if shutil.which(command[0]):
            try:
                subprocess.run(command, env=env, timeout=600, capture_output=True)
                return command[0]
            except (OSError, subprocess.TimeoutExpired):
                continue
    return None


def startup_failure(log_folder, language='it'):
    """Called when the window never opened: explain why and where the log is."""
    missing = []
    clients = flet_clients()
    if clients:
        missing = missing_libraries(clients[0])
    log = Path(log_folder) / 'errore-avvio.log'
    if language == 'en':
        title = 'Mouse Macro could not start'
        text = (f'Missing system libraries: {", ".join(missing)}.\n\n{install_hint(missing)}'
                if missing else f'The window could not be opened. Details in {log}')
    else:
        title = 'Mouse Macro non si è avviato'
        text = (f'Mancano librerie di sistema: {", ".join(missing)}.\n\n{install_hint(missing)}'
                if missing else f'Impossibile aprire la finestra. Dettagli in {log}')
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, 'a', encoding='utf-8') as stream:
            stream.write(f'{title}\n{text}\nclient: {clients[0] if clients else "-"}\n'
                         f'DISPLAY={os.environ.get("DISPLAY", "")} WAYLAND_DISPLAY={os.environ.get("WAYLAND_DISPLAY", "")}\n\n')
    except OSError:
        pass
    show_message(title, text.strip())
    return missing
