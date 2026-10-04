"""Packaged native mouse acceptance across two native windows and desktop."""
import json, os, subprocess, sys, time, zipfile, hashlib
from pathlib import Path

def target(path):
    import tkinter as tk
    root=tk.Tk();root.title('Native mouse target A');root.geometry('260x480+20+80')
    other=tk.Toplevel(root);other.title('Native mouse target B');other.geometry('260x480+300+80')
    counts={n:{k:0 for k in ('down','up','double','wheel','drag')} for n in ('A','B')}
    def save():Path(path).write_text(json.dumps(counts))
    held=set()
    def hit(n,k):
        if k=='up':
            if n not in held:return  # Tk can receive an unmatched desktop/panel release.
            held.remove(n)
        if k=='down':held.add(n)
        counts[n][k]+=1;save()
    for n,w in (('A',root),('B',other)):
        c=tk.Canvas(w,bg='#ead9ea');c.pack(fill='both',expand=True)
        for event,k in (('<ButtonPress-1>','down'),('<ButtonRelease-1>','up'),('<MouseWheel>','wheel'),('<B1-Motion>','drag')):
            c.bind(event,lambda e,n=n,k=k:hit(n,k))
        def double(e,n=n):hit(n,'down');hit(n,'double')
        c.bind('<Double-Button-1>',double)
    reset=Path(path).with_suffix('.reset')
    def poll():
        if reset.exists():
            reset.unlink();held.clear()
            for v in counts.values():
                for k in v:v[k]=0
            save()
        root.after(25,poll)
    save();poll();root.mainloop()

if len(sys.argv)>1 and sys.argv[1]=='--target':target(sys.argv[2]);raise SystemExit
import run_desktop as r
from macro.session import VERSION
from pynput import keyboard,mouse

def main():
    out=r.OUT;counters=out/'native-counts.json'
    archive=r.ROOT/'dist/windows'/f'MouseMacroStocazzSuperpower-Windows-v{VERSION}.zip'
    r.RESULT['environment']={'version':VERSION,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'screen':r.B.screen_geometry(),'targets':'Native Tk A/B and desktop'}
    with zipfile.ZipFile(archive) as z:z.extractall(out/'extracted')
    package=out/'extracted'/f'MouseMacroStocazzSuperpower-Windows-v{VERSION}'
    native=subprocess.Popen([sys.executable,__file__,'--target',str(counters)], creationflags=subprocess.CREATE_NO_WINDOW)
    env=os.environ.copy();env['PATH']=r'C:\Windows\System32;C:\Windows'
    r.PROC=subprocess.Popen([str(package/f'Mouse Macro v{VERSION}.exe')],cwd=package,env=env)
    try:
        r.APP=r.wait(lambda:r.U.FindWindowW('MouseMacroSuperpower017',None),15,'startup')
        rect=r.B.window_rect(r.APP);screen=r.B.screen_geometry()
        r.U.SetWindowPos(r.APP,r.W.HWND(-1),screen[2]-(rect[2]-rect[0])-2,20,0,0,0x11)
        r.wait(lambda:counters.exists(),10,'native targets')
        # Hide the QA runner's console; it must not cover the desktop/targets.
        import ctypes
        @ctypes.WINFUNCTYPE(r.W.BOOL, r.W.HWND, r.W.LPARAM)
        def hide_console(hwnd, unused):
            cls=ctypes.create_unicode_buffer(256);r.U.GetClassNameW(hwnd,cls,256)
            if cls.value=='ConsoleWindowClass':r.U.ShowWindow(hwnd,0)
            return True
        r.U.EnumWindows(hide_console,0)
        cls=ctypes.create_unicode_buffer(256)
        r.U.GetClassNameW(r.B.root_at(580,650),cls,256)
        assert cls.value in ('Progman','WorkerW'), ('Desktop covered by',cls.value)
        r.configure(1,1,False);r.screenshot('native-targets-ready')
        r.tap(keyboard.Key.f9);r.wait(lambda:r.state()=='REGISTRAZIONE',3,'record')
        for point in ((100,200),(400,200),(580,650),(100,250)):
            r.click(*point);time.sleep(.7)
        r.M.position=(100,280)
        for i in range(2):
            r.M.press(mouse.Button.left);time.sleep(.05);r.M.release(mouse.Button.left)
            if i==0:time.sleep(.09)
        time.sleep(.7);r.M.position=(100,360);r.M.scroll(0,-1);time.sleep(.7)
        r.M.position=(400,400);r.M.press(mouse.Button.left);time.sleep(.15)
        for x in range(410,451,10):r.M.position=(x,400);time.sleep(.06)
        r.M.release(mouse.Button.left);time.sleep(.2)
        r.tap(keyboard.Key.f9);r.app_idle(5)
        observed=json.loads(counters.read_text())
        assert observed['A']['down']==observed['A']['up']==4,observed
        assert observed['B']['down']==observed['B']['up']==2,observed
        assert observed['A']['double']==observed['A']['wheel']==1,observed
        assert observed['B']['drag']>0,observed
        r.log('global_recording_windows_and_desktop',passed=True,counts=observed)
        times={}
        for speed in (1,2):
            r.configure(1,speed,False)
            reset=counters.with_suffix('.reset');reset.touch();r.wait(lambda:not reset.exists(),3,'reset')
            started=time.perf_counter();r.tap(keyboard.Key.f10)
            r.wait(lambda:r.state()=='RIPRODUZIONE',3,'play');r.app_idle(30)
            elapsed=time.perf_counter()-started;actual=json.loads(counters.read_text())
            for n in ('A','B'):
                for k in ('down','up','double','wheel'):assert actual[n][k]==observed[n][k],(speed,observed,actual)
            assert actual['B']['drag']>0,actual
            assert not r.U.GetAsyncKeyState(1)&0x8000
            times[speed]=elapsed;r.log('global_replay',passed=True,speed=speed,seconds=elapsed,counts=actual)
        assert times[2]<times[1]*.8,times
        r.log('global_speed_gain',passed=True,times=times);r.screenshot('global-passed')
    finally:
        if r.APP:r.U.PostMessageW(r.APP,0x10,0,0)
        native.terminate();native.wait(5)
        if r.PROC:r.PROC.wait(5)
if __name__=='__main__':main()
