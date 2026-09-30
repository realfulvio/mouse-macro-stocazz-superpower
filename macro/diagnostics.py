"""Command-line verification of the packaged app without desktop input."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace


class PageProbe:
    def __init__(self):
        self.window = SimpleNamespace()
        self.controls = []
        self.services = []
        self.dialogs = []

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self, *controls):
        pass

    def show_dialog(self, dialog):
        self.dialogs.append(dialog)

    def pop_dialog(self):
        self.dialogs.pop()


def self_test(report_path, language='it'):
    from flet.version import flet_version
    import main as app
    from localization import translate
    from macro.backend import current_platform, list_mice
    from macro.engine import PlaybackOptions, _compute_scaled_times
    from macro.events import LEFT_DOWN, LEFT_UP, Macro, MacroEvent

    checks = {}
    result = {'version': app.VERSION, 'language': language, 'platform': current_platform(),
              'flet': flet_version, 'checks': checks}
    try:
        macro = Macro(current_platform(), [MacroEvent(0, LEFT_DOWN), MacroEvent(.01, LEFT_UP)])
        with tempfile.TemporaryDirectory() as folder:
            filename = str(Path(folder) / 'roundtrip.mmr')
            macro.save(filename)
            checks['file_roundtrip'] = Macro.load(filename) == macro
        times = _compute_scaled_times(macro.events, PlaybackOptions(speed=3))
        checks['minimum_50ms_at_3x'] = times[1] - times[0] >= .05
        checks['translation'] = translate('Pronto', language) == ('Ready' if language == 'en' else 'Pronto')
        checks['backend_import'] = True
        if current_platform() == 'linux':
            from macro.linux_backend import LinuxPlayer
            result['detected_mouse_count'] = len(list_mice())
            player = LinuxPlayer()
            try:
                player._ensure()
                checks['uinput_create_close_without_events'] = True
            finally:
                player.close()
        else:
            from macro.windows_backend import screen_geometry
            checks['screen_geometry'] = len(screen_geometry()) == 4

        # UI creation exercises the real controls, while no native hotkeys are registered.
        platform = app.current_platform
        mice = app.list_mice
        try:
            app.current_platform = lambda: 'linux'
            app.list_mice = lambda: []
            page = PageProbe()
            app.main(page, language=language)
            checks['ui_creation'] = bool(page.controls) and len(page.services) == 2
            checks['window_defaults'] = (page.window.width, page.window.height) == (560, 720)
        finally:
            app.current_platform = platform
            app.list_mice = mice
        result['ok'] = all(checks.values())
    except Exception as ex:
        result['ok'] = False
        result['error_type'] = type(ex).__name__
    Path(report_path).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return 0 if result['ok'] else 1
