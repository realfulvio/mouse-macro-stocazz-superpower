"""Modalita' "movimento umano": percorsi variati, clic invariati, spenta di default."""
import math
import random
import threading
import unittest

from macro import engine
from macro.engine import PlaybackOptions, _humanize_cycle, play
from macro.events import LEFT_DOWN, LEFT_UP, MOVE_ABS, MOVE_REL, RIGHT_DOWN, RIGHT_UP, WHEEL, MacroEvent


def path_macro(held=False):
    """Click in (100,100), poi un tragitto di 20 punti fino a (700,420), click, tragitto di ritorno."""
    events = [MacroEvent(0.0, MOVE_ABS, x=100, y=100), MacroEvent(0.05, LEFT_DOWN, x=100, y=100),
              MacroEvent(0.20, LEFT_UP, x=100, y=100)]
    if held:  # trascinamento: movimenti con tasto premuto
        events = events[:2]
    t = 0.3
    for k in range(1, 21):
        events.append(MacroEvent(t, MOVE_ABS, x=100 + 30 * k, y=100 + 16 * k))
        t += 0.02
    if held:
        events.append(MacroEvent(t, LEFT_UP, x=700, y=420))
    else:
        events += [MacroEvent(t + .05, LEFT_DOWN, x=700, y=420), MacroEvent(t + .2, LEFT_UP, x=700, y=420)]
    return events


def times_of(events):
    return [e.t for e in events]


class HumanizeCycleTests(unittest.TestCase):
    def test_structure_and_clicks_are_unchanged(self):
        events = path_macro()
        out, times = _humanize_cycle(events, times_of(events), random.Random(1))
        self.assertEqual([e.kind for e in out], [e.kind for e in events])
        for before, after in zip(events, out):
            if before.kind != MOVE_ABS:
                self.assertEqual((before.x, before.y, before.kind), (after.x, after.y, after.kind))
        for index, evt in enumerate(events):  # i tempi di pressioni e rilasci non cambiano
            if evt.kind != MOVE_ABS:
                self.assertEqual(times[index], evt.t)

    def test_run_endpoints_are_exact_and_middle_changes(self):
        events = path_macro()
        out, _ = _humanize_cycle(events, times_of(events), random.Random(2))
        run = [i for i, e in enumerate(events) if e.kind == MOVE_ABS and e.t >= 0.3]
        self.assertEqual((out[run[0]].x, out[run[0]].y), (events[run[0]].x, events[run[0]].y))
        self.assertEqual((out[run[-1]].x, out[run[-1]].y), (events[run[-1]].x, events[run[-1]].y))
        self.assertTrue(any((out[i].x, out[i].y) != (events[i].x, events[i].y) for i in run[1:-1]))

    def test_deviation_is_bounded(self):
        events = path_macro()
        for seed in range(50):
            out, _ = _humanize_cycle(events, times_of(events), random.Random(seed))
            for before, after in zip(events, out):
                self.assertLessEqual(math.hypot(after.x - before.x, after.y - before.y),
                                     engine.HUMAN_MAX_DEVIATION * 1.5 + 2)

    def test_times_are_monotonic_and_end_before_the_next_gesture(self):
        events = path_macro()
        for seed in range(50):
            _, times = _humanize_cycle(events, times_of(events), random.Random(seed))
            self.assertEqual(times, sorted(times))
            for index, evt in enumerate(events):
                following = next((e.t for e in events[index:] if e.kind != MOVE_ABS), None)
                if evt.kind == MOVE_ABS and following is not None:
                    self.assertLessEqual(times[index], following + 1e-9)

    def test_each_cycle_is_different(self):
        events = path_macro()
        a, _ = _humanize_cycle(events, times_of(events), random.Random(3))
        b, _ = _humanize_cycle(events, times_of(events), random.Random(4))
        self.assertNotEqual([(e.x, e.y) for e in a], [(e.x, e.y) for e in b])

    def test_drag_with_button_held_is_untouched(self):
        events = path_macro(held=True)
        out, times = _humanize_cycle(events, times_of(events), random.Random(5))
        self.assertEqual([(e.x, e.y) for e in out], [(e.x, e.y) for e in events])
        self.assertEqual(times, times_of(events))

    def test_short_moves_and_input_are_not_modified(self):
        events = [MacroEvent(0, MOVE_ABS, x=10, y=10), MacroEvent(0.01, MOVE_ABS, x=12, y=11),
                  MacroEvent(0.02, MOVE_ABS, x=13, y=12), MacroEvent(0.03, WHEEL, x=13, y=12, wheel=-1)]
        out, times = _humanize_cycle(events, times_of(events), random.Random(6))
        self.assertEqual([(e.x, e.y) for e in out], [(e.x, e.y) for e in events])
        self.assertEqual(times, times_of(events))

    def test_source_events_are_not_mutated(self):
        events = path_macro()
        snapshot = [(e.x, e.y, e.t) for e in events]
        _humanize_cycle(events, times_of(events), random.Random(7))
        self.assertEqual([(e.x, e.y, e.t) for e in events], snapshot)


class PlayTests(unittest.TestCase):
    def run_play(self, humanize, loops=2):
        events = path_macro()
        applied = []
        options = PlaybackOptions(repeat_count=loops, speed=20.0, humanize=humanize,
                                  min_click_hold_seconds=0.0, min_action_gap_seconds=0.0,
                                  max_pause_speedup=20.0)
        end = play(events, options, applied.append, lambda held: None, None, threading.Event())
        self.assertEqual(end, engine.PlaybackEnd.DONE)
        return events, applied

    def test_default_is_off_and_replays_the_recording_exactly(self):
        self.assertFalse(PlaybackOptions().humanize)
        events, applied = self.run_play(False)
        self.assertEqual([(e.kind, e.x, e.y) for e in applied], [(e.kind, e.x, e.y) for e in events] * 2)

    def test_humanized_replay_keeps_every_click_at_the_same_place(self):
        events, applied = self.run_play(True)
        clicks = lambda seq: [(e.kind, e.x, e.y) for e in seq if e.kind in (LEFT_DOWN, LEFT_UP)]
        self.assertEqual(clicks(applied), clicks(events) * 2)
        self.assertEqual(len(applied), len(events) * 2)
        self.assertNotEqual([(e.x, e.y) for e in applied[:len(events)]],
                            [(e.x, e.y) for e in applied[len(events):]])


def relative_macro(held=False):
    """Linux: tragitto libero di 20 movimenti relativi, clic, trascinamento, clic."""
    events = [MacroEvent(0.0, LEFT_DOWN), MacroEvent(0.15, LEFT_UP)]
    t = 0.3
    for k in range(20):
        events.append(MacroEvent(t, MOVE_REL, dx=30 + k % 3, dy=16 - k % 5))
        t += 0.02
    events += [MacroEvent(t, RIGHT_DOWN), MacroEvent(t + .15, RIGHT_UP)]
    t += 0.3
    events.append(MacroEvent(t, LEFT_DOWN))
    for k in range(10):  # trascinamento: deve restare identico
        events.append(MacroEvent(t + .02 * (k + 1), MOVE_REL, dx=-7, dy=3))
    events += [MacroEvent(t + .3, LEFT_UP), MacroEvent(t + .4, MOVE_REL, dx=4, dy=1),
               MacroEvent(t + .45, MOVE_REL, dx=-50, dy=-60), MacroEvent(t + .5, MOVE_REL, dx=-40, dy=-70),
               MacroEvent(t + .55, MOVE_REL, dx=-30, dy=-80), MacroEvent(t + .7, LEFT_DOWN),
               MacroEvent(t + .8, LEFT_UP)]
    return events


def segment_sums(events):
    """Somma dx/dy fra un evento non di movimento e il successivo."""
    sums, x, y = [], 0.0, 0.0
    for evt in events:
        if evt.kind == MOVE_REL:
            x, y = x + evt.dx, y + evt.dy
        else:
            sums.append((evt.kind, x, y))
            x = y = 0.0
    return sums + [('end', x, y)]


class HumanizeRelativeTests(unittest.TestCase):
    def test_sum_between_clicks_and_structure_are_unchanged(self):
        events = relative_macro()
        for seed in range(100):
            out, times = _humanize_cycle(events, times_of(events), random.Random(seed))
            self.assertEqual([e.kind for e in out], [e.kind for e in events])
            self.assertEqual(segment_sums(out), segment_sums(events))
            self.assertEqual(times, times_of(events))

    def test_free_path_changes_but_drag_and_short_paths_do_not(self):
        events = relative_macro()
        out, _ = _humanize_cycle(events, times_of(events), random.Random(11))
        free = range(2, 22)
        self.assertTrue(any((out[i].dx, out[i].dy) != (events[i].dx, events[i].dy) for i in free))
        drag = [i for i, e in enumerate(events) if e.kind == MOVE_REL and i > 24][:10]
        self.assertEqual([(out[i].dx, out[i].dy) for i in drag], [(events[i].dx, events[i].dy) for i in drag])

    def test_deltas_stay_integers_and_deviation_is_bounded(self):
        events = relative_macro()
        for seed in range(50):
            out, _ = _humanize_cycle(events, times_of(events), random.Random(seed))
            x = y = ox = oy = 0.0
            for before, after in zip(events, out):
                if before.kind != MOVE_REL:
                    x = y = ox = oy = 0.0
                    continue
                self.assertEqual(after.dx, int(after.dx))
                self.assertEqual(after.dy, int(after.dy))
                x, y, ox, oy = x + before.dx, y + before.dy, ox + after.dx, oy + after.dy
                self.assertLessEqual(math.hypot(ox - x, oy - y), engine.HUMAN_MAX_DEVIATION * 1.5 + 2)

    def test_short_relative_paths_are_not_modified(self):
        events = [MacroEvent(0, MOVE_REL, dx=2, dy=1), MacroEvent(.01, MOVE_REL, dx=3, dy=2),
                  MacroEvent(.02, MOVE_REL, dx=1, dy=1), MacroEvent(.03, LEFT_DOWN), MacroEvent(.1, LEFT_UP)]
        out, _ = _humanize_cycle(events, times_of(events), random.Random(1))
        self.assertEqual([(e.dx, e.dy) for e in out], [(e.dx, e.dy) for e in events])

    def test_humanized_relative_play_keeps_cursor_position_at_every_click(self):
        events = relative_macro()
        applied = []
        options = PlaybackOptions(repeat_count=3, speed=20.0, humanize=True, min_click_hold_seconds=0.0,
                                  min_action_gap_seconds=0.0, max_pause_speedup=20.0)
        play(events, options, applied.append, lambda held: None, None, threading.Event())
        self.assertEqual(len(applied), len(events) * 3)
        cycles = [applied[i * len(events):(i + 1) * len(events)] for i in range(3)]
        for cycle in cycles:
            self.assertEqual(segment_sums(cycle), segment_sums(events))
        self.assertNotEqual([(e.dx, e.dy) for e in cycles[0]], [(e.dx, e.dy) for e in cycles[1]])
        self.assertTrue(all(e is not o for e, o in zip(events, applied)))


if __name__ == '__main__':
    unittest.main()
