"""Exercise real chrome, file cancellation and keyboard navigation on exact ZIP."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib,json,os,subprocess,time,zipfile
import run_desktop as r
from macro.session import VERSION
u=r.U
u.IsIconic.argtypes=[W.HWND];u.IsIconic.restype=W.BOOL
u.ShowWindow.argtypes=[W.HWND,C.c_int]
root=Path(__file__).resolve().parents[1]
out=root/'evidence'/'ui-controls';out.mkdir(parents=True,exist_ok=True)
r.OUT=out
archive=root/'dist'/'windows'/f'MouseMacroStocazzSuperpower-Windows-v{VERSION}.zip'
with zipfile.ZipFile(archive) as z:z.extractall(out/'extracted')
package=out/'extracted'/f'MouseMacroStocazzSuperpower-Windows-v{VERSION}'
r.tap(r.keyboard.Key.esc);time.sleep(.5);r.tap(r.keyboard.Key.esc)
old=u.FindWindowW('MouseMacroSuperpower017',None)
if old:
 u.PostMessageW(old,0x10,0,0);r.wait(lambda:not u.IsWindow(old),5,'prior panel close')
p=subprocess.Popen([str(package/f'Mouse Macro v{VERSION}.exe')],cwd=package)
r.APP=r.wait(lambda:u.FindWindowW('MouseMacroSuperpower017',None),15,'startup');app=r.APP
r.RESULT['environment']={'package_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'dpi':u.GetDpiForWindow(app)}
try:
 r.tap(r.keyboard.Key.esc)
 g=r.B.screen_geometry();r0=r.B.window_rect(app)
 u.SetWindowPos(app,W.HWND(-1),min(900,g[2]-(r0[2]-r0[0])-70),40,0,0,0x11)
 before=r.B.window_rect(app)
 r.M.position=(before[0]+110,before[1]+18);r.M.press(r.mouse.Button.left);time.sleep(.1)
 r.M.position=(before[0]+160,before[1]+58);time.sleep(.2);r.M.release(r.mouse.Button.left);time.sleep(.2)
 after=r.B.window_rect(app)
 assert after[0]-before[0]==50 and after[1]-before[1]==40,(before,after)
 r.log('header_drag',passed=True)
 r.control(202);r.wait(lambda:u.IsWindowVisible(u.GetDlgItem(app,21)),3)
 r.control(25);assert r.text(u.GetDlgItem(app,22))=='20'
 r.control(24);assert not u.IsWindowVisible(u.GetDlgItem(app,21))
 r.control(24);assert r.text(u.GetDlgItem(app,22))=='20'
 r.log('expand_collapse_retains_options',passed=True,preset=20)
 r.control(102);dialog=r.wait(lambda:u.FindWindowW('#32770','Carica macro'),3,'load dialog')
 time.sleep(.6);r.tap(r.keyboard.Key.esc);r.wait(lambda:not u.IsWindow(dialog),3)
 assert not u.IsWindowEnabled(u.GetDlgItem(app,11))
 r.log('cancel_load_preserves_empty_macro',passed=True)
 r.control(104);dialog=r.wait(lambda:u.FindWindowW('#32770',f'Mouse Macro {VERSION} · hcok'),3,'guide')
 r.screenshot('guide-panel');r.ImageGrab.grab(bbox=tuple(r.B.window_rect(dialog))).save(out/'guide.png')
 time.sleep(.6);r.tap(r.keyboard.Key.esc);r.wait(lambda:not u.IsWindow(dialog),3)
 r.log('guide_open_close',passed=True)
 # Explicit activation is distinct from the no-activation browser workflow.
 r.K.press(r.keyboard.Key.alt);r.K.release(r.keyboard.Key.alt);u.SetForegroundWindow(app)
 r.wait(lambda:u.GetForegroundWindow()==app,3,'explicit panel activation')
 before=int(r.text(u.GetDlgItem(app,22)))
 # Find a focused visible native child by moving with the actual Tab key.
 class GUI(C.Structure):
  _fields_=[('size',W.DWORD),('flags',W.DWORD),('active',W.HWND),('focus',W.HWND),('capture',W.HWND),('menu',W.HWND),('move',W.HWND),('caret',W.HWND),('rect',W.RECT)]
 u.GetGUIThreadInfo.argtypes=[W.DWORD,C.POINTER(GUI)]
 u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)];u.GetWindowThreadProcessId.restype=W.DWORD
 tid=u.GetWindowThreadProcessId(app,None)
 for _ in range(30):
  r.tap(r.keyboard.Key.tab)
  info=GUI();info.size=C.sizeof(GUI);assert u.GetGUIThreadInfo(tid,C.byref(info))
  if info.focus==u.GetDlgItem(app,23):break
 else:raise AssertionError('No keyboard focus on repeat +')
 r.screenshot('keyboard-focus')
 r.tap(r.keyboard.Key.space)
 r.wait(lambda:int(r.text(u.GetDlgItem(app,22)))==before+1,3,'space activates button')
 r.log('keyboard_tab_space',passed=True)
 r.control(201);r.wait(lambda:u.IsIconic(app),3,'minimize')
 u.ShowWindow(app,4);r.wait(lambda:not u.IsIconic(app),3,'restore')
 r.log('minimize_restore',passed=True)
 r.control(203);r.wait(lambda:not u.IsWindow(app),3,'close X');p.wait(5)
 assert p.returncode==0
 r.log('native_close_button',passed=True,exit_code=p.returncode)
 r.RESULT['passed']=True
finally:
 if u.IsWindow(app):u.PostMessageW(app,0x10,0,0)
 p.wait(5)
 (out/'results.json').write_text(json.dumps(r.RESULT,indent=2))
