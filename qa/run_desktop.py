"""Headful browser acceptance suite. Sends native Windows inputs to the shipped EXE.
WebDriver is used ONLY to provision local pages/tabs and read actual DOM counters.
Run in an unlocked interactive desktop, never in SSH session 0.
"""
from __future__ import annotations
import ctypes as C
from ctypes import wintypes as W
import functools
import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from macro import windows_backend as B
from pynput import keyboard,mouse
from PIL import ImageGrab
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

U=C.windll.user32
U.FindWindowW.argtypes=[W.LPCWSTR,W.LPCWSTR];U.FindWindowW.restype=W.HWND
U.GetDlgItem.argtypes=[W.HWND,C.c_int];U.GetDlgItem.restype=W.HWND
U.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
U.SetForegroundWindow.argtypes=[W.HWND]
U.SetWindowPos.argtypes=[W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT]
U.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM];U.SendMessageW.restype=C.c_ssize_t
U.GetWindowLongW.argtypes=[W.HWND,C.c_int]
U.IsWindowEnabled.argtypes=[W.HWND]
U.IsWindow.argtypes=[W.HWND]
U.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
U.GetAsyncKeyState.argtypes=[C.c_int]
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evidence'/'desktop'
OUT.mkdir(parents=True,exist_ok=True)
RESULT={'environment':{},'checks':[]}
DPI_SMOKE='--dpi-smoke' in sys.argv
M=B.CheckedMouse(); K=keyboard.Controller()
APP=None; PROC=None


def log(name, **details):
    RESULT['checks'].append({'name':name, **details})
    (OUT/'results.json').write_text(json.dumps(RESULT,indent=2),'utf-8')
    print(name,details,flush=True)


def wait(fn, timeout=10, desc='condition'):
    start=time.perf_counter()
    while time.perf_counter()-start<timeout:
        value=fn()
        if value: return value
        time.sleep(.01)
    screenshot('timeout-'+desc[:30].replace(' ','-').replace(':',''))
    raise AssertionError('Timeout '+desc+'; state='+state()+'; message='+text(U.GetDlgItem(APP,2)) if APP else 'No app')


def text(hwnd):
    buf=C.create_unicode_buffer(2048);U.GetWindowTextW(hwnd,buf,len(buf));return buf.value

def state(): return text(U.GetDlgItem(APP,1)) if APP else ''

def screenshot(name):
    ImageGrab.grab(all_screens=True).save(OUT/(name+'.png'))

def tap(key):
    K.press(key);time.sleep(.045);K.release(key);time.sleep(.06)

def click(x,y,hold=.13):
    M.position=(int(x),int(y));time.sleep(.04);M.press(mouse.Button.left);time.sleep(hold);M.release(mouse.Button.left);time.sleep(.08)

def control(cid):
    hwnd=U.GetDlgItem(APP,cid);r=B.window_rect(hwnd)
    click((r[0]+r[2])//2,(r[1]+r[3])//2)

def app_idle(timeout=90):
    wait(lambda:state() not in ('RIPRODUZIONE','ARRESTO','REGISTRAZIONE'),timeout,'idle')
    if state()=='ERRORE':raise AssertionError(text(U.GetDlgItem(APP,2)))

def configure(repeats=1,speed=1,next_tab=False):
    # Real native child controls; the 20 preset uses the real popup menu
    # elsewhere. Counter changes are deliberately visible OS mouse clicks.
    current=int(text(U.GetDlgItem(APP,22)))
    for _ in range(abs(repeats-current)):control(23 if repeats>current else 21)
    control(31 if speed==1 else 32)
    checked=bool(U.SendMessageW(U.GetDlgItem(APP,40),0xF0,0,0))
    if checked!=next_tab: control(40)
    assert int(text(U.GetDlgItem(APP,22)))==repeats


def browser_window(title):
    found=[]
    enumproc=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    def enum(hwnd,_):
        if U.IsWindowVisible(hwnd) and title in text(hwnd) and B.browser_name(hwnd):found.append(hwnd)
        return True
    cb=enumproc(enum)
    U.EnumWindows(cb,0)
    return found[0] if found else None


def focus(driver):
    title=driver.title
    hwnd=wait(lambda:browser_window(title),10,'browser hwnd '+title)
    # User-equivalent activation via title bar outside all task targets.
    r=B.window_rect(hwnd)
    click(r[0]+max(100,min(400,(r[2]-r[0])//2)),r[1]+round(60*U.GetDpiForWindow(hwnd)/96))
    if U.GetForegroundWindow()!=hwnd:
        K.press(keyboard.Key.alt);K.release(keyboard.Key.alt);U.SetForegroundWindow(hwnd)
    assert B.browser_name(U.GetForegroundWindow()), 'No browser focus'
    wait(lambda:U.GetForegroundWindow()==hwnd,3,'browser focus')
    return hwnd


def point(driver, element):
    return driver.execute_script('''let r=document.getElementById(arguments[0]).getBoundingClientRect();
return [Math.round((window.screenX+(window.outerWidth-window.innerWidth)/2+r.x+r.width/2)*devicePixelRatio),
Math.round((window.screenY+window.outerHeight-window.innerHeight+r.y+r.height/2)*devicePixelRatio)]''',element)


def counts(driver):return driver.execute_script('return counts()')

def reset(driver):driver.execute_script('reset()');time.sleep(.05)


def record(driver, panel=False, full=True):
    focus(driver)
    control(10) if panel else tap(keyboard.Key.f9)
    wait(lambda:state()=='REGISTRAZIONE',3,'recording')
    wait(lambda:not U.IsWindowEnabled(U.GetDlgItem(APP,11)),2,'play control disabled while recording')
    click(*point(driver,'a'));time.sleep(.7)
    click(*point(driver,'b'));time.sleep(.7)
    if full:
        p=point(driver,'double')
        # True OS double click (two presses within the system interval).
        M.position=tuple(p);time.sleep(.03)
        for n in range(2):
            M.press(mouse.Button.left);time.sleep(.045);M.release(mouse.Button.left)
            if n==0:time.sleep(.08)
        time.sleep(.7)
        start=point(driver,'drag');end=point(driver,'drop')
        M.position=tuple(start);time.sleep(.05);M.press(mouse.Button.left)
        for i in range(1,11):
            M.position=(int(start[0]+(end[0]-start[0])*i/10),start[1]);time.sleep(.04)
        M.release(mouse.Button.left);time.sleep(.7)
        M.position=tuple(point(driver,'scroll'));time.sleep(.05);M.scroll(0,-1);time.sleep(.15)
    control(10) if panel else tap(keyboard.Key.f9)
    app_idle(5)
    observed=counts(driver)
    if full:
        assert observed['a']==1 and observed['b']==1 and observed['doubleClicks']==1 and observed['drags']==1 and observed['wheelEvents']==1,observed
    else:assert observed['a']==1 and observed['b']==1,observed
    return observed


def choose_menu(index):
    U.GetMenuItemRect.argtypes=[W.HWND,W.HMENU,W.UINT,C.POINTER(W.RECT)]
    control(24)
    pop=wait(lambda:U.FindWindowW('#32768',None),3,'menu popup')
    menu=U.SendMessageW(pop,0x1e1,0,0)
    rect=W.RECT()
    assert U.GetMenuItemRect(None,menu,index,C.byref(rect))
    click((rect.left+rect.right)//2,(rect.top+rect.bottom)//2)


def file_dialog(path, save=False):
    choose_menu(0 if save else 1)
    dialog=wait(lambda:U.FindWindowW('#32770','Salva macro' if save else 'Carica macro'),3,'file dialog')
    # FindWindow can see the shell dialog before its filename field accepts input.
    # Focus the real field and verify the text before submitting the dialog.
    def filename_field():
        candidates=[]
        dr=B.window_rect(dialog)
        def enum(hwnd,_):
            cls=C.create_unicode_buffer(256)
            U.GetClassNameW(hwnd,cls,len(cls))
            r=B.window_rect(hwnd)
            if cls.value=='Edit' and U.IsWindowVisible(hwnd) and r[1]>(dr[1]+dr[3])//2:
                candidates.append(hwnd)
            return True
        cb=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)(enum)
        U.EnumChildWindows(dialog,cb,0)
        return candidates[0] if len(candidates)==1 else None
    field=wait(filename_field,5,'filename field')
    time.sleep(.4)
    r=B.window_rect(field)
    click((r[0]+r[2])//2,(r[1]+r[3])//2)
    with K.pressed(keyboard.Key.ctrl):K.press('a');K.release('a')
    for char in str(path):
        K.type(char);time.sleep(.015)
    value=C.create_unicode_buffer(32768)
    U.SendMessageW(field,0xD,len(value),C.addressof(value))  # WM_GETTEXT for a foreign Edit control
    assert value.value==str(path),(value.value,str(path))
    tap(keyboard.Key.enter)
    wait(lambda:not U.IsWindow(dialog),5,'dialog closed')
    time.sleep(.1)


def emergency():
    K.press(keyboard.Key.ctrl);K.press(keyboard.Key.alt);K.press(keyboard.Key.f11)
    try:wait(lambda:state() not in ('RIPRODUZIONE','ARRESTO'),2,'emergency stop')
    finally:
        K.release(keyboard.Key.f11);K.release(keyboard.Key.alt);K.release(keyboard.Key.ctrl)


def extras(driver,name):
    saved=OUT/(name+'-recorded.mmr')
    file_dialog(saved,True)
    data=json.loads(saved.read_text())
    assert any(e['kind']=='move_abs' for e in data['events'])
    pr=B.window_rect(APP)
    assert all(not (pr[0]<=e['x']<pr[2] and pr[1]<=e['y']<pr[3]) for e in data['events'] if e['kind'].endswith('_down'))
    file_dialog(saved)
    reset(driver);configure(1,2,False);focus(driver);tap(keyboard.Key.f10);wait(lambda:state()=='RIPRODUZIONE',3);app_idle(15)
    got=counts(driver);assert got['a']==1 and got['b']==1 and got['drags']==1 and got['doubleClicks']==1,got
    log(name+'_save_load_dialogs',passed=True,events=len(data['events']),counts=got,panel_clicks_excluded=True)
    invalid=OUT/(name+'-invalid.mmr');invalid.write_text('{"events":[]}')
    file_dialog(invalid)
    assert state()=='ERRORE'
    reset(driver);focus(driver);tap(keyboard.Key.f10);wait(lambda:state()=='RIPRODUZIONE',3);app_idle(15)
    assert counts(driver)['a']==1
    log(name+'_invalid_file_recovery',passed=True,prior_macro_preserved=True)
    from macro.events import Macro,MacroEvent,LEFT_DOWN,LEFT_UP,MOVE_ABS
    a=point(driver,'a');b=point(driver,'b');drag=point(driver,'drag')
    longfile=OUT/(name+'-pause10.mmr')
    Macro('windows',[MacroEvent(0,LEFT_DOWN,x=a[0],y=a[1]),MacroEvent(.15,LEFT_UP,x=a[0],y=a[1]),
        MacroEvent(10.5,LEFT_DOWN,x=b[0],y=b[1]),MacroEvent(10.65,LEFT_UP,x=b[0],y=b[1])],data['screen'],data['layout']).save(longfile)
    for trigger in ('F10','panel'):
        file_dialog(longfile);reset(driver);configure(1,2,False);focus(driver);tap(keyboard.Key.f10)
        wait(lambda:counts(driver)['a']==1,3,'first accepted click')
        before=time.perf_counter()
        if trigger=='F10':
            K.press(keyboard.Key.f10)
            try:wait(lambda:state()=='PRONTO',2,'stop long pause')
            finally:K.release(keyboard.Key.f10)
        else:
            hwnd=U.GetDlgItem(APP,11);r=B.window_rect(hwnd)
            M.position=((r[0]+r[2])//2,(r[1]+r[3])//2);M.press(mouse.Button.left);time.sleep(.025);M.release(mouse.Button.left)
            wait(lambda:state()=='PRONTO',2,'panel stop')
        latency=time.perf_counter()-before
        assert latency<.3,latency
        assert counts(driver)['b']==0 and not U.GetAsyncKeyState(1)&0x8000
        log(name+'_stop_pause10_'+trigger,passed=True,latency_ms=latency*1000,mouse_released=True,second_clicks=counts(driver)['b'])
    dragfile=OUT/(name+'-drag10.mmr')
    Macro('windows',[MacroEvent(0,LEFT_DOWN,x=drag[0],y=drag[1]),MacroEvent(.3,MOVE_ABS,x=drag[0]+40,y=drag[1]),
        MacroEvent(10,MOVE_ABS,x=drag[0]+80,y=drag[1]),MacroEvent(11,LEFT_UP,x=drag[0]+80,y=drag[1])],data['screen'],data['layout']).save(dragfile)
    file_dialog(dragfile);reset(driver);focus(driver);tap(keyboard.Key.f10)
    wait(lambda:counts(driver)['down']==1,3,'drag down')
    before=time.perf_counter();emergency();latency=time.perf_counter()-before
    assert latency<.3 and not U.GetAsyncKeyState(1)&0x8000
    wait(lambda:counts(driver)['up']==1,2,'drag release')
    log(name+'_emergency_during_drag',passed=True,latency_ms=latency*1000,mouse_released=True,counts=counts(driver))
    file_dialog(saved)
    # Overlay is rejected BEFORE any input, without relocating the panel.
    r=B.window_rect(APP)
    reset(driver);focus(driver)
    U.SetWindowPos(APP,W.HWND(-1),a[0]-25,a[1]-25,0,0,0x11)
    tap(keyboard.Key.f10)
    wait(lambda:state()=='ERRORE',3,'overlay guard')
    assert counts(driver)['receivedA']==0
    log(name+'_panel_overlay_guard',passed=True,clicks_sent_to_page=0,message=text(U.GetDlgItem(APP,2)))
    U.SetWindowPos(APP,W.HWND(-1),r[0],r[1],0,0,0x11)
    file_dialog(saved)
    original_url=driver.current_url
    driver.get(original_url.replace('delay=550','delay=900'))
    fastfile=OUT/(name+'-dense.mmr')
    Macro('windows',[MacroEvent(0,LEFT_DOWN,x=a[0],y=a[1]),MacroEvent(.01,LEFT_UP,x=a[0],y=a[1]),
        MacroEvent(.02,LEFT_DOWN,x=b[0],y=b[1]),MacroEvent(.03,LEFT_UP,x=b[0],y=b[1])],data['screen'],data['layout']).save(fastfile)
    file_dialog(fastfile);configure(1,2,False);reset(driver);focus(driver);tap(keyboard.Key.f10)
    wait(lambda:state()=='RIPRODUZIONE',3);app_idle(10)
    got=counts(driver)
    assert got['receivedA']==1 and got['receivedB']==1 and got['lost']==1,got
    log(name+'_slow_page_standard_limit',passed=True,delay_ms=900,actual=got,expected_loss=1)
    choose_menu(3)  # actual Pagine lente option
    configure(20,2,False);reset(driver);focus(driver)
    before=time.perf_counter();tap(keyboard.Key.f10);wait(lambda:state()=='RIPRODUZIONE',3);app_idle(90)
    got=counts(driver)
    assert got['a']==20 and got['b']==20 and got['lost']==0,got
    log(name+'_slow_page_prudent_profile',passed=True,delay_ms=900,cycles=20,seconds=time.perf_counter()-before,actual=got)
    choose_menu(3)
    driver.get(original_url)
    file_dialog(saved)


def main():
    global APP,PROC
    # Stop only the earlier Codex panel, if any. Never close unrelated windows.
    old=U.FindWindowW('MouseMacroCompact016',None)
    if old:U.PostMessageW(old,0x10,0,0);wait(lambda:not U.IsWindow(old),4,'old close')
    archive=ROOT/'dist'/'windows'/'MouseMacroStocazzSuperpower-Windows-v0.16.0-beta-by-codex.zip'
    install=OUT/'extracted'
    install.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:z.extractall(install)
    package=install/'MouseMacroStocazzSuperpower-Windows-v0.16.0-beta-by-codex'
    exe=package/'Mouse Macro v0.16.0-beta-by-codex.exe'
    # Omit installed Python from the launcher PATH, proving bundled runtime use.
    env=os.environ.copy();env['PATH']=r'C:\Windows\System32;C:\Windows'
    started=time.perf_counter();PROC=subprocess.Popen([str(exe)],cwd=package,env=env)
    APP=wait(lambda:U.FindWindowW('MouseMacroCompact016',None),15,'package startup')
    startup=time.perf_counter()-started
    geometry=B.screen_geometry();panel_rect=B.window_rect(APP)
    U.SetWindowPos(APP,W.HWND(-1),geometry[2]-(panel_rect[2]-panel_rect[0])-2,20,0,0,0x11)
    assert U.GetWindowLongW(APP,-20)&8
    RESULT['environment']={'desktop':B.screen_geometry(),'dpi':U.GetDpiForWindow(APP),
        'user':os.environ.get('USERNAME'),'package_sha256':__import__('hashlib').sha256(archive.read_bytes()).hexdigest(),
        'package_runtime':'official embedded Python 3.13.16','headless':False}
    RESULT['environment']['scope']='dpi_smoke' if DPI_SMOKE else 'full_acceptance'
    if DPI_SMOKE:assert U.GetDpiForWindow(APP)>96,'Higher DPI fixture was not applied'
    log('package_startup',passed=True,seconds=startup,panel_rect=B.window_rect(APP),python_not_in_path=True)
    duplicate=subprocess.Popen([str(exe)],cwd=package,env=env);duplicate.wait(5)
    assert duplicate.returncode==0 and U.FindWindowW('MouseMacroCompact016',None)==APP
    log('duplicate_launch',passed=True,second_exit=duplicate.returncode,original_panel_preserved=True)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'qa')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/page.html'
    drivers=[]
    try:
        for name in (('Firefox',) if '--firefox-only' in sys.argv else ('Chrome','Firefox')):
            if name=='Chrome':
                opts=ChromeOptions();opts.add_argument('--no-first-run');opts.add_argument('--no-default-browser-check');opts.add_argument('--disable-search-engine-choice-screen')
                driver=webdriver.Chrome(options=opts)
            else:
                opts=FirefoxOptions();opts.set_preference('browser.shell.checkDefaultBrowser',False);opts.set_preference('browser.tabs.warnOnClose',False)
                driver=webdriver.Firefox(options=opts)
            drivers.append(driver)
            log(name+'_browser_version',version=driver.capabilities.get('browserVersion'),
                dpi=U.GetDpiForWindow(APP))
            driver.set_window_rect(x=0,y=0,width=min(round(900*U.GetDpiForWindow(APP)/96),B.screen_geometry()[2]-100),height=min(round(730*U.GetDpiForWindow(APP)/96),B.screen_geometry()[3]-55))
            driver.get(url+'?id='+name+'-single&delay=550')
            assert driver.execute_script('return typeof counts')=='function',driver.page_source
            configure()
            observed=record(driver,panel=True)
            hwnd=focus(driver);assert U.GetForegroundWindow()==hwnd
            assert U.GetWindowLongW(APP,-20)&8
            screenshot(name.lower()+'-panel-dpi'+str(U.GetDpiForWindow(APP)))
            log(name+'_record_panel',passed=True,counts=observed,foreground_preserved=True)
            previous=json.loads(Path(sys.argv[2]).read_text('utf-8')) if len(sys.argv)>2 and not DPI_SMOKE and name=='Chrome' else None
            speeds=(1,2)
            if previous:
                prior=[c for c in previous['checks'] if c['name']=='Chrome_twenty_cycles' and c.get('passed')]
                assert previous['environment']['package_sha256']==RESULT['environment']['package_sha256']
                assert {c['speed'] for c in prior}=={1,2}
                log('Chrome_twenty_cycles_reused',source=str(Path(sys.argv[2])),package_sha256=RESULT['environment']['package_sha256'])
                speeds=()
            for speed in speeds:
                cycles=2 if DPI_SMOKE else 20
                reset(driver);configure(cycles,speed,False);focus(driver)
                before=time.perf_counter()
                control(11) if speed==1 else tap(keyboard.Key.f10)
                wait(lambda:state()=='RIPRODUZIONE',3,'playing')
                wait(lambda:not U.IsWindowEnabled(U.GetDlgItem(APP,10)),2,'record control disabled while playing')
                assert U.GetForegroundWindow()==hwnd
                app_idle(180);elapsed=time.perf_counter()-before
                got=counts(driver)
                expected={'a':cycles,'b':cycles,'receivedA':cycles,'receivedB':cycles,'lost':0,'doubleClicks':cycles,'doubleSingles':cycles*2,'drags':cycles,'wheelEvents':cycles,'down':cycles,'up':cycles}
                log(name+'_counts_observed',speed=speed,actual=got,expected=expected)
                assert all(got[k]==v for k,v in expected.items()),(name,speed,got,expected)
                assert U.GetForegroundWindow()==hwnd
                log(name+('_two_cycles_dpi' if DPI_SMOKE else '_twenty_cycles'),passed=True,cycles=cycles,speed=speed,seconds=elapsed,expected=expected,actual=got,lost=got['lost'])
                screenshot(name.lower()+f'-{cycles}-speed{speed}')
            if not DPI_SMOKE:extras(driver,name)
            configure(1,2,False);reset(driver)
            observed=record(driver,panel=False,full=False)
            log(name+'_record_F9',passed=True,counts=observed)
            # Three tabs in first window, two in second, with distinct counters.
            first=driver.current_window_handle
            handles=[first]
            for number in (2,3):
                driver.switch_to.new_window('tab');driver.get(url+f'?id={name}-tab{number}&delay=550');handles.append(driver.current_window_handle)
            driver.switch_to.new_window('window');driver.set_window_rect(x=0,y=0,width=min(round(900*U.GetDpiForWindow(APP)/96),B.screen_geometry()[2]-100),height=min(round(730*U.GetDpiForWindow(APP)/96),B.screen_geometry()[3]-55))
            second_handles=[driver.current_window_handle]
            driver.get(url+f'?id={name}-second1&delay=550')
            driver.switch_to.new_window('tab');driver.get(url+f'?id={name}-second2&delay=550');second_handles.append(driver.current_window_handle)
            driver.switch_to.window(first);reset(driver)
            configure(3,2,True);focus(driver);tap(keyboard.Key.f10);wait(lambda:state()=='RIPRODUZIONE',3);app_idle(30)
            tab_counts={}
            for handle in handles:
                driver.switch_to.window(handle);tab_counts[handle]=counts(driver)
            for handle in second_handles:
                driver.switch_to.window(handle);tab_counts[handle]=counts(driver)
            assert all(tab_counts[h]['a']==1 and tab_counts[h]['b']==1 for h in handles),tab_counts
            assert all(tab_counts[h]['a']==0 and tab_counts[h]['b']==0 for h in second_handles),tab_counts
            configure(2,2,True);driver.switch_to.window(second_handles[0]);focus(driver);tap(keyboard.Key.f10);wait(lambda:state()=='RIPRODUZIONE',3);app_idle(30)
            for handle in second_handles:
                driver.switch_to.window(handle);tab_counts[handle]=counts(driver)
            assert all(tab_counts[h]['a']==1 and tab_counts[h]['b']==1 for h in second_handles),tab_counts
            assert len(driver.window_handles)==5
            log(name+'_two_windows_five_tabs',passed=True,tab_counts=list(tab_counts.values()),tabs_remaining=len(driver.window_handles))
            screenshot(name.lower()+'-tabs-complete')
            # Guard must stop rather than deliver clicks into another window.
            configure(1,1,False);driver.switch_to.window(first);focus(driver)
            tap(keyboard.Key.f10);wait(lambda:state()=='RIPRODUZIONE',3)
            driver.switch_to.window(second_handles[0]);focus(driver)
            wait(lambda:state()=='ERRORE',5,'wrong window guard')
            log(name+'_focus_guard',passed=True,message=text(U.GetDlgItem(APP,2)))
            if name=='Firefox' and not DPI_SMOKE:
                file_dialog(OUT/(name+'-drag10.mmr'))
                driver.switch_to.window(first);reset(driver);configure(1,2,False);focus(driver);tap(keyboard.Key.f10)
                wait(lambda:counts(driver)['down']==1,3,'held before close')
                assert U.GetAsyncKeyState(1)&0x8000
                before=time.perf_counter()
                # A mouse click on X would release the injected drag itself,
                # invalidating the cleanup measurement. Use the native close
                # message while the button is still verifiably held.
                U.PostMessageW(APP,0x10,0,0)
                wait(lambda:not U.IsWindow(APP),3,'close during playback')
                PROC.wait(3)
                assert not U.GetAsyncKeyState(1)&0x8000 and PROC.returncode==0
                log('close_during_playback',passed=True,latency_ms=(time.perf_counter()-before)*1000,
                    mechanism='WM_CLOSE while native left button held',mouse_released=True,exit_code=PROC.returncode)
            driver.quit();drivers.remove(driver)
    finally:
        for driver in drivers:
            try:driver.quit()
            except Exception:pass
        server.shutdown()
    if U.IsWindow(APP):U.PostMessageW(APP,0x10,0,0)
    PROC.wait(5)
    log('close_lifecycle',passed=True,exit_code=PROC.returncode,panel_destroyed=not U.IsWindow(APP))
    RESULT['passed']=True
    (OUT/'results.json').write_text(json.dumps(RESULT,indent=2),'utf-8')

if __name__=='__main__':
    try:main()
    except Exception:
        RESULT['passed']=False;RESULT['error']=traceback.format_exc()
        (OUT/'results.json').write_text(json.dumps(RESULT,indent=2),'utf-8')
        print(traceback.format_exc(),flush=True)
        screenshot('failure')
        raise
