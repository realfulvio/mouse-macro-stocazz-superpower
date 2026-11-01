"""Tastiera nelle macro e macro avviabile (parte indipendente dal sistema)."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from macro import engine
from macro.engine import PlaybackEnd, PlaybackOptions, play
from macro.events import (KEY_DOWN, KEY_PREFIX, KEY_UP, LEFT_DOWN, LEFT_UP, MOVE_ABS, Macro,
                          MacroEvent, valid_key_name)
from macro.export import export_launcher, launcher_text, safe_stem
from macro.keys import (EXTENDED_VKS, KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP, RESERVED_VKS,
                        key_flags, key_name, vk_of_name, vk_of_pynput_key)
from macro.runner import parse_run_args
from macro.session import Session, State, validate_gestures


def typed(text_vks, start=0.0, gap=0.05):
    events, t = [], start
    for vk in text_vks:
        events.append(MacroEvent(t, KEY_DOWN, key=key_name(vk)))
        events.append(MacroEvent(t + gap / 2, KEY_UP, key=key_name(vk)))
        t += gap
    return events


class KeyNames(unittest.TestCase):
    def test_names_and_validation(self):
        self.assertEqual(key_name(65), 'vk:65')
        self.assertEqual(vk_of_name('vk:65'), 65)
        for bad in ('', 'a', 'vk:', 'vk:0', 'vk:255', 'vk:-1', 'vk:6x', 'vk:1234', None, 65):
            self.assertFalse(valid_key_name(bad), bad)
            with self.assertRaises(ValueError):
                vk_of_name(bad)

    def test_pynput_keys_are_read_through_vk(self):
        self.assertEqual(vk_of_pynput_key(SimpleNamespace(vk=65)), 65)
        self.assertEqual(vk_of_pynput_key(SimpleNamespace(value=SimpleNamespace(vk=0xA2))), 0xA2)
        self.assertIsNone(vk_of_pynput_key(SimpleNamespace(vk=None)))
        self.assertIsNone(vk_of_pynput_key(SimpleNamespace()))
        self.assertIsNone(vk_of_pynput_key(SimpleNamespace(vk=True)))

    def test_flags_mark_extended_keys_and_releases(self):
        self.assertEqual(key_flags(0x41, False), 0)
        self.assertEqual(key_flags(0x41, True), KEYEVENTF_KEYUP)
        self.assertEqual(key_flags(0x25, False), KEYEVENTF_EXTENDEDKEY)  # freccia sinistra
        self.assertEqual(key_flags(0x25, True), KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP)
        self.assertTrue({0x78, 0x79, 0x7A} <= RESERVED_VKS)
        self.assertFalse(EXTENDED_VKS & RESERVED_VKS)


class MacroFile(unittest.TestCase):
    def roundtrip(self, macro):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'm.mmr'
            macro.save(str(path))
            return Macro.load(str(path))

    def test_keys_survive_save_and_load(self):
        events = [MacroEvent(0, LEFT_DOWN, x=5, y=6), MacroEvent(.1, LEFT_UP, x=5, y=6)] + typed([65, 66], .2)
        loaded = self.roundtrip(Macro('windows', events, [0, 0, 100, 100]))
        self.assertEqual([(e.kind, e.key) for e in loaded.events[2:]],
                         [(KEY_DOWN, 'vk:65'), (KEY_UP, 'vk:65'), (KEY_DOWN, 'vk:66'), (KEY_UP, 'vk:66')])

    def test_old_files_without_key_field_still_load(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'old.mmr'
            path.write_text(json.dumps({'platform': 'windows', 'screen': [], 'layout': {}, 'events': [
                {'t': 0, 'kind': LEFT_DOWN, 'dx': 0, 'dy': 0, 'x': 1, 'y': 2, 'wheel': 0, 'snap': ''}]}))
            self.assertEqual(Macro.load(str(path)).events[0].key, '')

    def test_invalid_key_data_is_rejected(self):
        for event in (MacroEvent(0, KEY_DOWN, key='a'), MacroEvent(0, KEY_DOWN),
                      MacroEvent(0, LEFT_DOWN, key='vk:65')):
            with self.assertRaises(ValueError):
                self.roundtrip(Macro('windows', [event]))

    def test_linux_macros_use_evdev_codes_and_windows_ones_are_rejected(self):
        loaded = self.roundtrip(Macro('linux', [MacroEvent(0, KEY_DOWN, key='kc:30'), MacroEvent(.1, KEY_UP, key='kc:30')]))
        self.assertEqual([e.key for e in loaded.events], ['kc:30', 'kc:30'])
        for platform, bad in (('linux', 'vk:65'), ('linux', 'kc:0'), ('linux', 'kc:249'), ('windows', 'kc:30')):
            with self.assertRaises(ValueError, msg=(platform, bad)):
                self.roundtrip(Macro(platform, [MacroEvent(0, KEY_DOWN, key=bad)]))


class Validation(unittest.TestCase):
    def test_keyboard_only_macro_is_valid(self):
        validate_gestures(typed([65, 66, 67]))

    def test_key_release_without_press_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_gestures([MacroEvent(0, KEY_UP, key='vk:65'), MacroEvent(.1, LEFT_DOWN), MacroEvent(.2, LEFT_UP)])

    def test_key_left_down_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_gestures([MacroEvent(0, KEY_DOWN, key='vk:65')])

    def test_auto_repeat_is_tolerated(self):
        validate_gestures([MacroEvent(0, KEY_DOWN, key='vk:65'), MacroEvent(.1, KEY_DOWN, key='vk:65'),
                           MacroEvent(.2, KEY_UP, key='vk:65')])

    def test_mouse_only_macros_still_need_a_click_or_wheel_or_key(self):
        with self.assertRaises(ValueError):
            validate_gestures([MacroEvent(0, MOVE_ABS, x=1, y=1)])


class Playback(unittest.TestCase):
    def run_play(self, events, stop=None, fail_on=None):
        clock = SimpleNamespace(now=100.0)
        seen, released = [], []
        stop = stop or threading.Event()

        def wait(deadline, stop_event):
            clock.now = max(clock.now, deadline())
            return not stop_event.is_set()

        def emit(event):
            seen.append(event)
            if fail_on is not None and len(seen) == fail_on:
                raise OSError('boom')

        with patch.object(engine.time, 'perf_counter', lambda: clock.now), patch.object(engine, '_wait_until', wait):
            try:
                end = play(events, PlaybackOptions(repeat_count=2), emit, lambda held: released.append(set(held)),
                           None, stop)
            except OSError:
                end = None
        return end, seen, released

    def test_keys_are_replayed_in_order_and_every_cycle(self):
        events = typed([65, 66])
        end, seen, released = self.run_play(events)
        self.assertEqual(end, PlaybackEnd.DONE)
        self.assertEqual([e.key for e in seen], [e.key for e in events] * 2)
        self.assertEqual(released, [])

    def test_failure_with_key_down_releases_it(self):
        events = typed([65])
        end, seen, released = self.run_play(events, fail_on=1)   # fails while sending the press
        self.assertIsNone(end)
        self.assertEqual(released, [{KEY_PREFIX + 'vk:65'}])

    def test_stop_while_key_is_down_releases_it(self):
        stop = threading.Event()
        events = typed([65, 66])
        original = engine.play

        clock = SimpleNamespace(now=100.0)
        released, seen = [], []

        def wait(deadline, stop_event):
            clock.now = max(clock.now, deadline())
            return not stop_event.is_set()

        def emit(event):
            seen.append(event)
            if event.kind == KEY_DOWN and len(seen) == 3:   # second key pressed, then Stop
                stop.set()

        with patch.object(engine.time, 'perf_counter', lambda: clock.now), patch.object(engine, '_wait_until', wait):
            end = original(events, PlaybackOptions(repeat_count=1), emit, lambda h: released.append(set(h)), None, stop)
        self.assertEqual(end, PlaybackEnd.STOPPED)
        self.assertEqual(released, [{KEY_PREFIX + 'vk:66'}])

    def test_keys_do_not_break_mouse_gestures(self):
        events = [MacroEvent(0, LEFT_DOWN, x=1, y=1), MacroEvent(.2, LEFT_UP, x=1, y=1)] + typed([65], .5)
        end, seen, released = self.run_play(events)
        self.assertEqual(end, PlaybackEnd.DONE)
        self.assertEqual([e.kind for e in seen[:4]], [LEFT_DOWN, LEFT_UP, KEY_DOWN, KEY_UP])


class SessionWithKeys(unittest.TestCase):
    def test_keyboard_macro_loads_and_plays_through_session(self):
        played = []

        class Player:
            def apply_event(self, e): played.append(e.kind)
            def release_held(self, h): pass
            def next_tab(self, s): pass
            def close(self): pass

        session = Session(None, Player, screen=lambda: [], platform='windows')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'k.mmr'
            Macro('windows', typed([65, 66]), []).save(str(path))
            self.assertTrue(session.load(path))
        session.toggle_play(PlaybackOptions(repeat_count=1, min_action_gap_seconds=0, speed=20), next_tab=False)
        session.worker.join(5)
        self.assertEqual(session.state, State.READY)
        self.assertEqual(played, [KEY_DOWN, KEY_UP, KEY_DOWN, KEY_UP])


class Launcher(unittest.TestCase):
    def test_stem_is_safe_for_cmd(self):
        self.assertEqual(safe_stem(r'C:\x\fatture 2026 (v2).mmr'), 'fatture 2026 (v2)')
        self.assertEqual(safe_stem('a&b%c!d^e.mmr'), 'a_b_c_d_e')
        self.assertEqual(safe_stem('...'), 'macro')
        self.assertLessEqual(len(safe_stem('x' * 500)), 80)

    def test_launcher_text(self):
        text = launcher_text('Mia macro', 5, 2, slow=True, human=True, next_tab=True)
        self.assertIn('--run "%~dp0Mia macro.mmr" --repeat 5 --speed 2 --slow --human --next-tab', text)
        self.assertIn('app\\macro\\runner.py', text)   # sceglie solo versioni che sanno eseguire --run
        self.assertTrue(text.isascii())
        self.assertTrue(all(line.endswith('\r') for line in text.split('\n')[:-1]))

    def test_launcher_rejects_bad_values(self):
        for args in ((0, 1), (1000, 1), (True, 1), ('3', 1), (1, 3), (1, 0)):
            with self.assertRaises(ValueError, msg=args):
                launcher_text('m', *args)

    def test_export_writes_both_files_next_to_each_other(self):
        macro = Macro('windows', typed([65]), [])
        with tempfile.TemporaryDirectory() as folder:
            cmd, mmr = export_launcher(macro, Path(folder) / 'a&b.cmd', 3, 1)
            self.assertEqual((cmd.name, mmr.name), ('a_b.cmd', 'a_b.mmr'))
            self.assertEqual(Macro.load(str(mmr)).events[0].key, 'vk:65')
            self.assertIn('a_b.mmr', cmd.read_text('ascii'))

    def test_failed_validation_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                export_launcher(Macro('windows', typed([65]), []), Path(folder) / 'm.cmd', 0, 1)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_session_export_reports_and_refuses_invalid_macro(self):
        session = Session(None, None, platform='windows')
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(session.export(Path(folder) / 'x.cmd'))   # macro vuota
            self.assertEqual(session.state, State.ERROR)
            session.state = State.READY
            session.macro = Macro('windows', typed([65]), [])
            self.assertTrue(session.export(Path(folder) / 'x.cmd', 2, 2))
            self.assertTrue((Path(folder) / 'x.cmd').exists())
            self.assertIn('x.cmd', session.message)


class InfiniteAndLinuxLauncher(unittest.TestCase):
    def test_infinite_replaces_the_repeat_count(self):
        text = launcher_text('m', 5, 1, infinite=True)
        self.assertIn('--infinite --speed 1', text)
        self.assertNotIn('--repeat', text)
        self.assertEqual(launcher_text('m', 5, 1).count('--infinite'), 0)
        launcher_text('m', 0, 1, infinite=True)   # il numero è ignorato quando è infinito

    def test_run_arguments_accept_infinite(self):
        request = parse_run_args(['--run', 'm.mmr', '--infinite'])
        self.assertTrue(request.infinite)
        self.assertFalse(parse_run_args(['--run', 'm.mmr']).infinite)
        self.assertEqual(parse_run_args(['--open', 'a b.mmr', '--repeat', '2'], '--open').path, 'a b.mmr')
        with self.assertRaises(ValueError):
            parse_run_args(['--run', 'm.mmr'], '--open')

    def test_linux_script_is_valid_executable_and_sanitized(self):
        from macro.export import linux_script_text
        macro = Macro('linux', [MacroEvent(0, KEY_DOWN, key='kc:30'), MacroEvent(.1, KEY_UP, key='kc:30')])
        with tempfile.TemporaryDirectory() as folder:
            script, mmr = export_launcher(macro, Path(folder) / "a$(x)'b.sh", 3, 2, human=True, platform='linux')
            self.assertEqual((script.name, mmr.name), ('a_(x)_b.sh', 'a_(x)_b.mmr'))
            text = script.read_text('ascii')
            self.assertTrue(script.stat().st_mode & 0o100)
            self.assertEqual(Macro.load(str(mmr)).events[0].key, 'kc:30')
        self.assertTrue(text.startswith('#!/usr/bin/env bash\n'))
        self.assertIn('--open "$DIR/a_(x)_b.mmr" --repeat 3 --speed 2 --human', text)
        self.assertNotIn('$(x)', text)
        self.assertIn('--infinite', linux_script_text('m', infinite=True))
        with self.assertRaises(ValueError):
            linux_script_text('m', 1000)


class RunArguments(unittest.TestCase):
    def test_arguments(self):
        request = parse_run_args(['--run', 'C:\\m.mmr', '--repeat', '7', '--speed', '2', '--human'])
        self.assertEqual((request.path, request.repeats, request.speed, request.human, request.slow),
                         ('C:\\m.mmr', 7, 2, True, False))
        self.assertEqual(parse_run_args(['--run', 'm.mmr']).repeats, 1)

    def test_bad_arguments(self):
        for argv in (['--run'], ['--run', 'm.txt'], ['--run', 'm.mmr', '--repeat', '0'],
                     ['--run', 'm.mmr', '--repeat', '1000'], ['--run', 'm.mmr', '--repeat', 'x'],
                     ['--run', 'm.mmr', '--speed', '3'], ['--run', 'm.mmr', '--repeat']):
            with self.assertRaises(ValueError, msg=argv):
                parse_run_args(argv)


if __name__ == '__main__':
    unittest.main()
