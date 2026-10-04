"""Focused v0.17/current Windows timing comparison, including play()'s final guard.

No native desktop needed: compile the actual Panel initialization/options methods
without Win32 setup and run the unchanged engine with a deterministic clock.
"""
from __future__ import annotations
import ast
import json
from pathlib import Path
import queue
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from macro import engine
from macro.engine import PlaybackOptions
from macro.events import LEFT_DOWN, LEFT_UP, MOVE_ABS, MacroEvent


def panel_settings():
    tree = ast.parse((ROOT/'windows_main.py').read_text('utf-8'))
    panel = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Panel')
    init = next(n for n in panel.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
    # Keep the real settings initialization; stop at the first native UI dependency.
    init.body = init.body[:next(i for i, n in enumerate(init.body)
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name) and n.value.func.id == 'Theme')]
    panel.body = [init, next(n for n in panel.body if isinstance(n, ast.FunctionDef) and n.name == 'options')]
    namespace = {'queue': queue, 'PlaybackOptions': PlaybackOptions,
                 'U': SimpleNamespace(GetDoubleClickTime=lambda: 500)}
    exec(compile(ast.Module(body=[panel], type_ignores=[]), str(ROOT/'windows_main.py'), 'exec'), namespace)
    return namespace['Panel']()


def legacy_options(speed, slow=False):
    return PlaybackOptions(repeat_count=1, speed=speed, max_pause_speedup=1.0,
        min_click_hold_seconds=.12, min_action_gap_seconds=1.2 if slow else .65,
        double_click_seconds=.5, double_click_gap_seconds=.08, protect_wheel_actions=True)


def click_sequence(gaps):
    events = [MacroEvent(0, LEFT_DOWN), MacroEvent(.03, LEFT_UP)]
    t = .03
    for i, gap in enumerate(gaps, 1):
        t += gap
        events.extend([MacroEvent(t, LEFT_DOWN, x=i*100), MacroEvent(t+.03, LEFT_UP, x=i*100)])
        t += .03
    return events


def timing_cases():
    return {
        'short_movements': [MacroEvent(i*.1, MOVE_ABS, x=i) for i in range(11)],
        'realistic_clicks': click_sequence([.4, .7, 1.0, 1.5, .6]),
        'double_and_close_clicks': [MacroEvent(0, LEFT_DOWN), MacroEvent(.03, LEFT_UP),
            MacroEvent(.17, LEFT_DOWN), MacroEvent(.20, LEFT_UP),
            MacroEvent(.45, LEFT_DOWN, x=100), MacroEvent(.48, LEFT_UP, x=100)],
        'page_loading': click_sequence([.7, 6.0, .7]),
    }


def virtual_play(events, options, apply=None, next_tab=True):
    clock = SimpleNamespace(now=100.0)
    sent, progress, tabs, released = [], [], [], []
    stop = threading.Event()
    def wait(deadline, stopped):
        if stopped.is_set(): return False
        clock.now = max(clock.now, deadline())
        return True
    def emit(event):
        sent.append((event, clock.now-100))
        if apply: apply(event, clock, stop)
    with patch.object(engine.time, 'perf_counter', lambda: clock.now), \
            patch.object(engine, '_wait_until', wait):
        end = engine.play(events, options, emit, lambda held: released.append(set(held)),
            progress.append, stop, between_cycles=(lambda: tabs.append(clock.now-100)) if next_tab else None)
    return SimpleNamespace(duration=clock.now-100, sent=sent, end=end,
                           progress=progress, tabs=tabs, released=released)


def comparison():
    result = {}
    panel = panel_settings()
    for name, events in timing_cases().items():
        rows = {}
        for speed in (1, 2):
            panel.speed = speed
            for policy, options in (('before', legacy_options(speed)), ('after', panel.options())):
                plan = engine._compute_scaled_times(events, options)
                rows[f'{policy}_{speed}x'] = {'last_event_seconds': round(plan[-1], 6),
                    'playback_seconds': round(virtual_play(events, options).duration, 6)}
        result[name] = rows
    return result


if __name__ == '__main__':
    print(json.dumps(comparison(), indent=2))
