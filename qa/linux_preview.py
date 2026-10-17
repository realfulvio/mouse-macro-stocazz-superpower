"""Show the Linux panel in a given state without input devices (screenshots, QA).

Usage: python qa/linux_preview.py [ready|recording|playing|options|updates] [it|en]
"""
from pathlib import Path
import asyncio
import os
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import flet as ft

import linux_main
from macro.events import LEFT_DOWN, LEFT_UP, MOVE_REL, MacroEvent
from macro.session import State

STATE = sys.argv[1] if len(sys.argv) > 1 else 'ready'
LANGUAGE = sys.argv[2] if len(sys.argv) > 2 else 'it'


class FakeRecorder:
    current_event_count = 128


async def start(page):
    folder = tempfile.mkdtemp(prefix='mm-preview-')
    panel = linux_main.LinuxPanel(page, LANGUAGE, preferences=Path(folder) / 'settings.json')
    panel.devices = [('/dev/input/event5', 'Logitech G304')]
    panel.mouse.value = '/dev/input/event5'
    panel.session.macro.events = [MacroEvent(0, MOVE_REL, dx=5, dy=3), MacroEvent(.2, LEFT_DOWN),
                                  MacroEvent(.3, LEFT_UP), MacroEvent(14.0, MOVE_REL, dx=-5, dy=-3)]
    panel.update = {'state': 'available', 'latest': '1.0.1', 'release': {'version': '1.0.1'}}
    panel.render()
    await asyncio.sleep(2)
    if STATE == 'recording':
        panel.session.recorder = FakeRecorder()
        panel.session.state = State.RECORDING
    elif STATE == 'playing':
        panel.last_options = linux_main.playback_options('20')
        panel.repeat.value = '20'
        panel.session.completed = 7
        panel.session.state = State.PLAYING
    elif STATE == 'options':
        panel.toggle_options()
    elif STATE == 'updates':
        panel.update_menu()
    panel.render()
    if STATE in ('recording', 'playing'):
        panel.started -= 83
        panel.render()


if os.environ.get('WAYLAND_DISPLAY'):
    import flet.app as flet_app
    flet_app.is_linux_server = lambda: False
ft.run(start, assets_dir=str(Path(linux_main.__file__).resolve().parent / 'assets'))
