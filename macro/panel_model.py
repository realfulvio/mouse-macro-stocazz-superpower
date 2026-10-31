"""Portable panel preferences and playback profiles; no desktop dependencies."""
from dataclasses import asdict
import json
import math
import os
import re
from pathlib import Path

from .engine import PlaybackOptions, LoopMode

def load_skin(name):
    """Declarative theme data (palette, clips, crops, sizes) shared by Linux and Windows."""
    path = Path(__file__).resolve().parent.parent / 'assets' / 'skins' / f'{name}.json'
    return json.loads(path.read_text('utf-8'))


# The Linux package has its own release line (tags linux-v*); the Windows
# VERSION in macro/session.py is unrelated.
LINUX_VERSION = '1.1.1'

BAMBOLA = load_skin('bambola')  # theme data lives in assets/skins/bambola.json
SKINS = {
    'bambola': BAMBOLA['palette']['linux'],
    'unicorno': dict(background='#1A0F2E', surface='#2A1642', border='#4B2A7A',
                     text='#F9F7FF', muted='#DED5EF', record='#FF2D93', play='#8B5CF6',
                     ready='#3ED072', warning='#FFC83D', error='#FF4D6D'),
    'palio': dict(background='#F6E7C8', surface='#FFF6DF', border='#D2AE6B',
                 text='#3A1710', muted='#60452E', record='#C23B22', play='#1F5D8C',
                 ready='#2E8B4F', warning='#8A5A00', error='#B3261E'),
}
DEFAULT_SKIN = 'bambola'
DARK_SKINS = ('unicorno', 'bambola')
UPDATE_DOT = {'current': 'ready', 'available': 'warning'}  # other states: 'border'
WINDOW_LIMITS = {'width': (420, 4000), 'height': (380, 4000), 'left': (-20000, 20000), 'top': (-20000, 20000)}


def parse_repeats(text):
    text = str(text).strip()
    if not re.fullmatch(r'[0-9]{1,3}', text) or not 1 <= int(text) <= 999:
        raise ValueError('Imposta da 1 a 999 ripetizioni.')
    return int(text)


def playback_options(repeats='1', speed=1.0, slow=False, human=False,
                     mode='count', minutes='10', double_click_ms='400'):
    modes = {'count': LoopMode.REPEAT_COUNT, 'infinite': LoopMode.INFINITE,
             'duration': LoopMode.DURATION}
    if mode not in modes or speed not in (1.0, 2.0):
        raise ValueError('Modalità o velocità non valida.')
    count = parse_repeats(repeats) if mode == 'count' else None
    try:
        duration = float(minutes) * 60 if mode == 'duration' else 600.0
        click_ms = int(double_click_ms)
    except (TypeError, ValueError) as error:
        raise ValueError('Imposta una durata e un tempo di doppio clic validi.') from error
    if not math.isfinite(duration) or duration <= 0 or not 100 <= click_ms <= 1000:
        raise ValueError('Durata positiva; doppio clic da 100 a 1000 ms.')
    return PlaybackOptions(mode=modes[mode], repeat_count=count, duration_seconds=duration,
                           speed=speed, pause_threshold_seconds=.35 if slow else 2.0,
                           max_pause_speedup=1.0, min_click_hold_seconds=.12,
                           min_action_gap_seconds=1.2 if slow else .65/speed,
                           double_click_seconds=click_ms/1000, double_click_gap_seconds=.08,
                           protect_wheel_actions=True, humanize=bool(human))


def config_dir():
    root = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')
    return root/'MouseMacroStocazzSuperpower'


def settings_path():
    return config_dir()/'linux-panel.json'


def _window(value):
    if not isinstance(value, dict):
        return {}
    window = {}
    for key, (low, high) in WINDOW_LIMITS.items():
        number = value.get(key)
        if type(number) in (int, float) and math.isfinite(number) and low <= number <= high:
            window[key] = int(number)
    return window


def read_settings(path):
    try:
        value = json.loads(Path(path).read_text('utf-8'))
    except (OSError, ValueError):
        value = {}
    if not isinstance(value, dict):
        value = {}
    click = str(value.get('double_click_ms', '400'))
    # Input injection preferences (speed, next tab, human movement) are reset
    # on every launch, as on Windows; only presentation and devices persist.
    return {'skin': value.get('skin') if value.get('skin') in SKINS else DEFAULT_SKIN,
            'device': value.get('device') if isinstance(value.get('device'), str) else None,
            'double_click_ms': click if click.isdecimal() and 100 <= int(click) <= 1000 else '400',
            'check_updates': value.get('check_updates', True) if isinstance(value.get('check_updates', True), bool) else True,
            'window': _window(value.get('window'))}


def write_settings(path, value):
    return write_text_atomic(path, json.dumps(value))


def write_text_atomic(path, text):
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.tmp')
        temporary.write_text(text, 'utf-8')
        os.replace(temporary, path)
        return True
    except OSError:
        return False


def save_replay_trace(folder, version, options, outcome, records):
    """Write ultimo-replay.json like the Windows panel; never raises."""
    settings = asdict(options) if options is not None else {}
    if options is not None:
        settings['mode'] = options.mode.value
    data = {'version': version, 'platform': 'linux', 'options': settings,
            'outcome': outcome, 'records': records}
    return write_text_atomic(Path(folder)/'ultimo-replay.json', json.dumps(data, indent=2, ensure_ascii=False))


def save_error_log(folder, text, name='errore.log'):
    return write_text_atomic(Path(folder)/name, text)
