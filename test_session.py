import threading
import time
import tempfile
from pathlib import Path
import unittest
from macro.session import Session, State, validate_gestures
from macro.events import Macro, MacroEvent, LEFT_DOWN, LEFT_UP, MOVE_ABS
from macro.engine import PlaybackOptions, play


def gesture():
    return [MacroEvent(0, LEFT_DOWN,x=10,y=20),MacroEvent(.01,LEFT_UP,x=10,y=20)]


class Recorder:
    def __init__(self, events=None):
        self.events = events or gesture()
        self.layout = {}
        self.started = 0
        self.stopped = 0
    def start(self): self.started += 1
    def stop(self):
        self.stopped += 1
        return self.events


class Player:
    def __init__(self):
        self.seen = []
        self.closed = 0
        self.released = []
        self.pressed = threading.Event()
        self.tabs = 0
    def select_browser(self, event, layout): return 'Chrome'
    def apply_event(self, event):
        self.seen.append(event.kind)
        if event.kind == LEFT_DOWN: self.pressed.set()
    def release_held(self, held): self.released.append(set(held))
    def next_tab(self, stop): self.tabs += 1
    def close(self): self.closed += 1


class SessionTests(unittest.TestCase):
    def test_incompatible_commands_and_stop_long_pause_no_overlap(self):
        recorder, player = Recorder(), Player()
        session = Session(lambda:recorder, lambda:player)
        session.toggle_record()
        session.toggle_play(PlaybackOptions(repeat_count=1))
        self.assertEqual(session.state, State.RECORDING)
        session.toggle_record()
        self.assertEqual(recorder.stopped,1)
        session.macro.events[1].t = 10
        session.toggle_play(PlaybackOptions(repeat_count=1))
        self.assertTrue(player.pressed.wait(1))
        session.toggle_record()
        self.assertEqual(recorder.started,1)
        before=time.perf_counter()
        session.request_stop()
        session.worker.join(1)
        self.assertLess(time.perf_counter()-before,.3)
        self.assertEqual(session.state, State.READY)
        self.assertEqual(player.released,[{'left'}])
        self.assertEqual(player.closed,1)
        self.assertFalse(session.worker.is_alive())

    def test_recovery_after_error_and_invalid_file_preserves_macro(self):
        session = Session(Recorder,Player)
        original=Macro('windows',gesture())
        session.macro=original
        with tempfile.TemporaryDirectory() as folder:
            invalid=Path(folder)/'bad.mmr';invalid.write_text('{}')
            self.assertFalse(session.load(invalid))
            self.assertEqual(session.state,State.ERROR)
            self.assertIs(session.macro,original)
            session.toggle_play(PlaybackOptions(repeat_count=1,min_click_hold_seconds=.01,min_action_gap_seconds=.01),False)
            session.worker.join(1)
            self.assertEqual(session.state,State.READY)
            path=Path(folder)/'macro.mmr'
            self.assertTrue(session.save(path))
            self.assertTrue(session.load(path))
            self.assertEqual(session.macro.events,original.events)

    def test_close_during_drag_releases_and_joins(self):
        player=Player(); session=Session(Recorder,lambda:player)
        session.macro=Macro('windows',[MacroEvent(0,LEFT_DOWN),MacroEvent(10,MOVE_ABS),MacroEvent(11,LEFT_UP)])
        session.toggle_play(PlaybackOptions(repeat_count=1),False)
        self.assertTrue(player.pressed.wait(1))
        session.close()
        self.assertEqual(session.state,State.CLOSED)
        self.assertFalse(session.worker.is_alive())
        self.assertEqual(player.released,[{'left'}])
        self.assertEqual(player.closed,1)

    def test_failed_recording_keeps_previous_macro_and_does_not_trim_drag(self):
        recorder=Recorder([MacroEvent(0,LEFT_DOWN),MacroEvent(.2,MOVE_ABS,x=20),MacroEvent(.4,LEFT_UP,x=20)])
        session=Session(lambda:recorder,Player)
        session.toggle_record();session.toggle_record()
        self.assertEqual([e.kind for e in session.macro.events],[LEFT_DOWN,MOVE_ABS,LEFT_UP])
        previous=session.macro
        recorder.events=[MacroEvent(0,LEFT_DOWN)]
        session.toggle_record();session.toggle_record()
        self.assertEqual(session.state,State.ERROR)
        self.assertIs(session.macro,previous)

    def test_one_tab_change_between_cycles_and_none_after_last(self):
        player=Player();session=Session(Recorder,lambda:player)
        session.macro=Macro('windows',gesture())
        session.toggle_play(PlaybackOptions(repeat_count=3,min_click_hold_seconds=.01,min_action_gap_seconds=.01))
        session.worker.join(1)
        self.assertEqual(session.completed,3)
        self.assertEqual(player.tabs,2)
        self.assertEqual(player.seen,[LEFT_DOWN,LEFT_UP]*3)

    def test_double_click_is_preserved_without_shortening_other_action_gaps(self):
        events=[MacroEvent(0,LEFT_DOWN,x=10),MacroEvent(.01,LEFT_UP,x=10),
                MacroEvent(.17,LEFT_DOWN,x=10),MacroEvent(.18,LEFT_UP,x=10),
                MacroEvent(.8,LEFT_DOWN,x=100),MacroEvent(.81,LEFT_UP,x=100)]
        seen=[]
        options=PlaybackOptions(repeat_count=2,speed=2,min_click_hold_seconds=.12,
                                min_action_gap_seconds=.65,double_click_seconds=.5)
        play(events,options,lambda e:seen.append((e.kind,time.perf_counter())),lambda h:None,None,threading.Event())
        for offset in (0,6):
            self.assertLess(seen[offset+2][1]-seen[offset][1],.5)
            self.assertGreaterEqual(seen[offset+4][1]-seen[offset+3][1],.65-.001)
        self.assertGreaterEqual(seen[6][1]-seen[5][1],.65-.001)

    def test_press_failure_still_releases_possibly_sent_input(self):
        released=[]
        def fail(event): raise RuntimeError('error after injection')
        with self.assertRaises(RuntimeError):
            play(gesture(),PlaybackOptions(repeat_count=1),fail,lambda held:released.append(set(held)),None,threading.Event())
        self.assertEqual(released,[{'left'}])

class WheelBoundaryTests(unittest.TestCase):
    def test_scroll_before_tab_change_and_click_keeps_action_guard(self):
        from macro.events import WHEEL
        seen=[];tabs=[]
        events=[MacroEvent(0,WHEEL,wheel=-1),MacroEvent(.01,LEFT_DOWN),MacroEvent(.02,LEFT_UP),MacroEvent(.03,WHEEL,wheel=-1)]
        options=PlaybackOptions(repeat_count=2,speed=2,min_click_hold_seconds=.01,min_action_gap_seconds=.05,protect_wheel_actions=True)
        play(events,options,lambda e:seen.append((e.kind,time.perf_counter())),lambda h:None,None,threading.Event(),between_cycles=lambda:tabs.append(time.perf_counter()))
        self.assertGreaterEqual(seen[1][1]-seen[0][1],.05-.001)
        self.assertGreaterEqual(seen[3][1]-seen[2][1],.05-.001)
        self.assertGreaterEqual(tabs[0]-seen[3][1],.05-.001)
        self.assertGreaterEqual(seen[4][1]-seen[3][1],.05-.001)

class ConcurrentRecoveryTests(unittest.TestCase):
    def test_error_during_inflight_player_cannot_start_recording(self):
        player=Player();recorder=Recorder()
        session=Session(lambda:recorder,lambda:player)
        session.macro=Macro('windows',[MacroEvent(0,LEFT_DOWN),MacroEvent(10,LEFT_UP)])
        session.toggle_play(PlaybackOptions(repeat_count=1),False)
        self.assertTrue(player.pressed.wait(1))
        session.error('unrelated UI error')
        session.toggle_record()
        self.assertEqual(recorder.started,0)
        session.close()
        self.assertFalse(session.worker.is_alive())
