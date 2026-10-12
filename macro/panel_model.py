"""Portable panel preferences and playback profiles; no desktop dependencies."""
import json
import math
import os
import re
from pathlib import Path

from .engine import PlaybackOptions, LoopMode

SKINS = {
    'unicorno': dict(background='#1A0F2E', surface='#2A1642', border='#4B2A7A',
                     text='#F9F7FF', muted='#DED5EF', record='#FF2D93', play='#8B5CF6',
                     ready='#3ED072', warning='#FFC83D', error='#FF4D6D'),
    'palio': dict(background='#F6E7C8', surface='#FFF6DF', border='#D2AE6B',
                 text='#3A1710', muted='#60452E', record='#C23B22', play='#1F5D8C',
                 ready='#2E8B4F', warning='#8A5A00', error='#B3261E'),
}


def parse_repeats(text):
    text = str(text).strip()
    if not re.fullmatch(r'[0-9]{1,3}', text) or not 1 <= int(text) <= 999:
        raise ValueError('Imposta da 1 a 999 ripetizioni.')
    return int(text)


def playback_options(repeats='1', speed=1.0, slow=False, varied=False,
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
                           protect_wheel_actions=True,
                           timing_variation_seconds=.25 if varied else 0.0)


def settings_path():
    root = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')
    return root/'MouseMacroStocazzSuperpower'/'linux-panel.json'


def read_settings(path):
    try:
        value = json.loads(Path(path).read_text('utf-8'))
        if not isinstance(value, dict):
            return {}
        # Input injection preferences are intentionally reset on every launch.
        return {'skin': value.get('skin') if value.get('skin') in SKINS else 'unicorno',
                'device': value.get('device') if isinstance(value.get('device'), str) else None,
                'double_click_ms': value.get('double_click_ms', '400')}
    except (OSError, ValueError):
        return {}


def write_settings(path, value):
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value), 'utf-8')
        os.replace(temporary, path)
        return True
    except OSError:
        return False
