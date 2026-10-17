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


def _core_checks(checks, language, platform):
    from localization import translate
    from macro.engine import PlaybackOptions, _compute_scaled_times
    from macro.events import LEFT_DOWN, LEFT_UP, Macro, MacroEvent

    macro = Macro(platform, [MacroEvent(0, LEFT_DOWN), MacroEvent(.01, LEFT_UP)])
    with tempfile.TemporaryDirectory() as folder:
        filename = str(Path(folder) / 'roundtrip.mmr')
        macro.save(filename)
        checks['file_roundtrip'] = Macro.load(filename) == macro
    times = _compute_scaled_times(macro.events, PlaybackOptions(speed=3))
    checks['minimum_150ms_at_3x'] = times[1] - times[0] >= .15
    sequence = macro.events + [MacroEvent(.02, LEFT_DOWN), MacroEvent(.03, LEFT_UP)]
    times = _compute_scaled_times(sequence, PlaybackOptions(speed=3, min_action_gap_seconds=.4))
    checks['independent_400ms_action_gap_at_3x'] = times[2] - times[1] >= .4 - 1e-9
    checks['translation'] = translate('Pronto', language) == ('Ready' if language == 'en' else 'Pronto')


def _linux_checks(checks, result, language):
    """Device access depends on the seat and udev rules, not on the program:
    report it as environment information so a CI runner or a user without
    uaccess still gets a meaningful verdict about the code itself."""
    from macro.linux_backend import LinuxPlayer, list_mice, mouse_models
    from linux_main import LinuxPanel, LINUX_VERSION

    result['linux_version'] = LINUX_VERSION
    environment = result.setdefault('environment', {})
    try:
        environment['detected_mouse_count'] = len(list_mice())
    except OSError as error:
        environment['detected_mouse_count'] = f'{type(error).__name__}: {error}'
    environment['mouse_models'] = mouse_models()
    player = LinuxPlayer()
    try:
        player._ensure()
        environment['uinput'] = 'ok'
    except OSError as error:
        environment['uinput'] = f'{type(error).__name__}: {error}'
    finally:
        try:
            player.close()
        except OSError:
            pass
    checks['backend_import'] = True
    with tempfile.TemporaryDirectory() as folder:
        page = PageProbe()
        panel = LinuxPanel(page, language, preferences=Path(folder) / 'settings.json')
        checks['linux_panel_creation'] = bool(page.controls) and len(page.services) == 1
        checks['linux_panel_language'] = panel.tr('Registra') == ('Record' if language == 'en' else 'Registra')


def linux_self_test(report_path, language='it'):
    """Self-test of the Linux binary: no legacy interface, no input sent."""
    from flet.version import flet_version

    checks = {}
    result = {'language': language, 'platform': 'linux', 'flet': flet_version, 'checks': checks}
    try:
        _core_checks(checks, language, 'linux')
        _linux_checks(checks, result, language)
        result['version'] = result['linux_version']
        result['ok'] = all(checks.values())
    except Exception as ex:
        result['ok'] = False
        result['error_type'] = type(ex).__name__
        result['error'] = str(ex)
    Path(report_path).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return 0 if result['ok'] else 1


def self_test(report_path, language='it'):
    from flet.version import flet_version
    import main as app
    from macro.backend import current_platform

    checks = {}
    result = {'version': app.VERSION, 'language': language, 'platform': current_platform(),
              'flet': flet_version, 'checks': checks}
    try:
        _core_checks(checks, language, current_platform())
        checks['backend_import'] = True
        if current_platform() == 'linux':
            _linux_checks(checks, result, language)
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
        result['error'] = str(ex)
    Path(report_path).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return 0 if result['ok'] else 1
