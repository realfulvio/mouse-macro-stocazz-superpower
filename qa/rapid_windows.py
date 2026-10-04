"""Focused interactive acceptance on the exact ZIP: timing, inputs, tabs and stops.
Reuses the v0.17 desktop fixture and native input helpers, without full visual QA.
Run: python qa/rapid_windows.py evidence/v018/desktop
"""
from __future__ import annotations
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import zipfile

import run_desktop as r
from macro.events import Macro, MacroEvent, LEFT_DOWN, LEFT_UP, MOVE_ABS, WHEEL
from macro.session import VERSION
from pynput import keyboard
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def replay(driver, speed, repeats=1, next_tab=False):
    r.configure(repeats, speed, next_tab)
    r.focus(driver)
    tracepath = Path(os.environ['LOCALAPPDATA'])/'MouseMacroStocazzSuperpower'/'ultimo-replay.json'
    before = tracepath.stat().st_mtime_ns if tracepath.exists() else 0
    start = time.perf_counter()
    r.tap(keyboard.Key.f10)
    r.wait(lambda: r.state() == 'RIPRODUZIONE', 3, 'playing')
    r.app_idle(40)
    r.wait(lambda: tracepath.exists() and tracepath.stat().st_mtime_ns != before, 3, 'new trace')
    trace = json.loads(tracepath.read_text('utf-8'))
    end = next(x for x in reversed(trace['records']) if x['type'] == 'playback_end')
    assert end['outcome'] == 'done' and end['completed_cycles'] == repeats, end
    assert trace['options']['speed'] == speed
    (r.OUT/f'trace-{len(r.RESULT["checks"])}-{speed}x.json').write_text(json.dumps(trace, indent=2), 'utf-8')
    return {'engine_seconds': end['elapsed_seconds'], 'wall_seconds': time.perf_counter()-start,
            'counts': r.counts(driver)}


def save_macro(driver, name, events):
    hwnd = r.focus(driver)
    path = r.OUT/(name+'.mmr')
    Macro('windows', events, r.B.screen_geometry(), r.B.browser_layout(hwnd)).save(path)
    r.file_dialog(path)
    return path


def main():
    assert r.U.GetForegroundWindow(), 'Requires an unlocked interactive desktop'
    archive = r.ROOT/'dist'/'windows'/f'MouseMacroStocazzSuperpower-Windows-v{VERSION}.zip'
    old = r.U.FindWindowW('MouseMacroSuperpower017', None)
    if old:
        r.U.PostMessageW(old, 0x10, 0, 0)
        r.wait(lambda: not r.U.IsWindow(old), 4, 'old app close')
    install = r.OUT/'extracted'
    with zipfile.ZipFile(archive) as z: z.extractall(install)
    package = install/f'MouseMacroStocazzSuperpower-Windows-v{VERSION}'
    env = os.environ.copy(); env['PATH'] = r'C:\Windows\System32;C:\Windows'
    r.PROC = subprocess.Popen([str(package/f'Mouse Macro v{VERSION}.exe')], cwd=package, env=env)
    driver = None; server = None
    try:
        r.APP = r.wait(lambda: r.U.FindWindowW('MouseMacroSuperpower017', None), 15, 'package startup')
        rect = r.B.window_rect(r.APP); screen = r.B.screen_geometry()
        r.U.SetWindowPos(r.APP, r.W.HWND(-1), screen[2]-(rect[2]-rect[0])-2, 20, 0, 0, 0x11)
        r.RESULT['environment'] = {'version': VERSION, 'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'screen': screen, 'dpi': r.U.GetDpiForWindow(r.APP), 'interactive': True}
        r.expand_options()
        assert r.text(r.U.GetDlgItem(r.APP, 40)).endswith('disattivato')
        r.control(25); assert r.text(r.U.GetDlgItem(r.APP, 22)) == '20'
        r.log('startup_default_off_preset20', passed=True, python_excluded_from_path=True)
        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(r.ROOT/'qa')))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}/page.html'
        opts = Options(); opts.add_argument('--no-first-run'); opts.add_argument('--no-default-browser-check')
        driver = webdriver.Chrome(options=opts, service=Service(log_output=str(r.OUT/'chromedriver.log')))
        driver.set_window_rect(x=0, y=0, width=min(900, screen[2]-370), height=min(730, screen[3]-55))
        driver.get(url+'?id=timing&delay=250')
        # The existing recorded-macro exercise checks real single/double/drag/wheel input.
        r.configure(1, 1, False)
        observed = r.record(driver, full=True)
        r.log('recording_real_inputs', passed=True, counts=observed)
        for speed in (1, 2):
            r.reset(driver)
            result = replay(driver, speed)
            c = result['counts']
            assert c['a']==c['b']==c['doubleClicks']==c['drags']==c['wheelEvents']==1 and c['lost']==0, c
            r.log('recorded_replay', passed=True, speed=speed, **result)
        a, b = r.point(driver, 'a'), r.point(driver, 'b')
        events=[]; t=0
        for i, gap in enumerate((0, .4, .7, 1, 1.5, .6)):
            if i: t += .03+gap
            x, y = a if i%2==0 else b
            events += [MacroEvent(t, LEFT_DOWN, x=x, y=y), MacroEvent(t+.03, LEFT_UP, x=x, y=y)]
        saved = save_macro(driver, 'realistic-clicks', events)
        durations={}
        for speed in (1, 2):
            r.reset(driver); result = replay(driver, speed); c=result['counts']
            assert c['a']==c['b']==3 and c['receivedA']==c['receivedB']==3 and c['lost']==0, c
            durations[speed]=result['engine_seconds']
            r.log('realistic_replay', passed=True, speed=speed, **result)
        assert durations[2] < durations[1]*.65, durations
        r.log('realistic_speed_gain', passed=True, normal=durations[1], fast=durations[2])
        loading=[]; t=0
        for i, gap in enumerate((0, .7, 6, .7)):
            if i: t += .03+gap
            x,y=a if i%2==0 else b
            loading += [MacroEvent(t,LEFT_DOWN,x=x,y=y),MacroEvent(t+.03,LEFT_UP,x=x,y=y)]
        save_macro(driver,'page-loading',loading)
        loading_times={}
        for speed in (1,2):
            r.reset(driver); result=replay(driver,speed); c=result['counts']
            assert c['a']==c['b']==2 and c['lost']==0,c
            loading_times[speed]=result['engine_seconds']
            r.log('loading_replay',passed=True,speed=speed,**result)
        assert loading_times[2]<loading_times[1],loading_times
        save_macro(driver,'preset-one-click',events[:2])
        r.reset(driver);result=replay(driver,2,repeats=20)
        assert result['counts']['a']==20 and result['counts']['lost']==0,result
        r.log('preset20_replay',passed=True,**result)
        # Native Ctrl+Tab listener proves zero OFF, exactly one ON between two cycles.
        first=driver.current_window_handle
        driver.switch_to.new_window('tab'); driver.get(url+'?id=second&delay=250')
        second=driver.current_window_handle
        driver.switch_to.window(first)
        r.file_dialog(saved)
        for enabled in (False, True):
            for handle in (first, second):
                driver.switch_to.window(handle); r.reset(driver)
            driver.switch_to.window(first)
            tab_events=[]
            def on_press(key):
                if key == keyboard.Key.tab: tab_events.append(time.perf_counter())
            with keyboard.Listener(on_press=on_press):
                result=replay(driver, 2, repeats=2, next_tab=enabled)
                # WebDriver's current handle is not updated by native tab changes.
            current_browser_title=r.text(r.U.GetForegroundWindow())
            counts={}
            for handle in (first,second):
                driver.switch_to.window(handle); counts[handle]=r.counts(driver)
            expected = 3 if enabled else 6
            assert counts[first]['a']==counts[first]['b']==expected, counts
            assert counts[second]['a']==counts[second]['b']==(3 if enabled else 0), counts
            assert len(tab_events)==(1 if enabled else 0), tab_events
            assert ('second' if enabled else 'timing') in current_browser_title, current_browser_title
            r.log('tabs_on' if enabled else 'tabs_off', passed=True, tab_inputs=len(tab_events), counts=counts,
                  final_foreground_title=current_browser_title, no_tab_after_last=True)
        driver.switch_to.window(first)
        # Stop during a long wait; emergency while holding a drag.
        pause=[MacroEvent(0,LEFT_DOWN,x=a[0],y=a[1]),MacroEvent(.03,LEFT_UP,x=a[0],y=a[1]),
               MacroEvent(10,LEFT_DOWN,x=b[0],y=b[1]),MacroEvent(10.03,LEFT_UP,x=b[0],y=b[1])]
        save_macro(driver,'stop-pause',pause)
        r.reset(driver);r.configure(1,2,False);r.focus(driver);r.tap(keyboard.Key.f10)
        r.wait(lambda:r.counts(driver)['a']==1,3,'first click')
        started=time.perf_counter();r.K.press(keyboard.Key.f10)
        try:r.wait(lambda:r.state()=='PRONTO',2,'F10 stop')
        finally:r.K.release(keyboard.Key.f10)
        latency=time.perf_counter()-started
        assert latency<.3 and r.counts(driver)['b']==0 and not r.U.GetAsyncKeyState(1)&0x8000
        r.log('stop_F10',passed=True,latency_seconds=latency)
        drag=r.point(driver,'drag')
        save_macro(driver,'emergency-drag',[MacroEvent(0,LEFT_DOWN,x=drag[0],y=drag[1]),
            MacroEvent(.3,MOVE_ABS,x=drag[0]+40,y=drag[1]),MacroEvent(10,LEFT_UP,x=drag[0]+40,y=drag[1])])
        r.reset(driver);r.focus(driver);r.tap(keyboard.Key.f10)
        r.wait(lambda:r.counts(driver)['down']==1,3,'drag press')
        started=time.perf_counter();r.emergency();latency=time.perf_counter()-started
        r.wait(lambda:r.counts(driver)['up']==1,2,'drag safety release')
        assert latency<.3 and not r.U.GetAsyncKeyState(1)&0x8000
        r.log('emergency_CtrlAltF11',passed=True,latency_seconds=latency,mouse_released=True)
        r.screenshot('final-panel')
        r.RESULT['passed']=True
    except Exception:
        r.RESULT['passed']=False
        r.screenshot('failed')
        raise
    finally:
        (r.OUT/'results.json').write_text(json.dumps(r.RESULT,indent=2),'utf-8')
        if driver:driver.quit()
        if server:server.shutdown()
        if r.APP:r.U.PostMessageW(r.APP,0x10,0,0)
        if r.PROC:r.PROC.wait(5)


if __name__=='__main__':
    main()
