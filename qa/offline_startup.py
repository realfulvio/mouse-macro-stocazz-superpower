"""Validate the exact distributed ZIP with the VM network link disconnected."""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile
from PIL import ImageGrab
root=Path(__file__).resolve().parents[1]
out=root/"evidence"/"offline-startup"
out.mkdir(parents=True,exist_ok=True)
archive=root/"dist/windows/MouseMacroStocazzSuperpower-Windows-v0.17.0-beta.zip"
u=C.windll.user32
u.FindWindowW.argtypes=[W.LPCWSTR,W.LPCWSTR];u.FindWindowW.restype=W.HWND
u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
result={"package_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"passed":False}
p=None
try:
    assert not u.FindWindowW("MouseMacroSuperpower017",None),"Previous panel still open"
    with zipfile.ZipFile(archive) as z:z.extractall(out/"extracted")
    package=out/"extracted/MouseMacroStocazzSuperpower-Windows-v0.17.0-beta"
    env=os.environ.copy();env["PATH"]=r"C:\Windows\System32;C:\Windows"
    start=time.perf_counter()
    p=subprocess.Popen([str(package/"Mouse Macro v0.17.0-beta.exe")],cwd=package,env=env)
    hwnd=None
    for _ in range(150):
        hwnd=u.FindWindowW("MouseMacroSuperpower017",None)
        if hwnd:break
        time.sleep(.1)
    assert hwnd,"Offline startup failed"
    result["seconds"]=time.perf_counter()-start
    ps=f"Get-CimInstance Win32_Process | Where-Object ParentProcessId -EQ {p.pid} | Select-Object ExecutablePath | ConvertTo-Json -Compress"
    raw=subprocess.check_output(["powershell","-NoProfile","-Command",ps],creationflags=subprocess.CREATE_NO_WINDOW,text=True)
    child=json.loads(raw)
    result["child_executable"]=child["ExecutablePath"]
    assert Path(child["ExecutablePath"])==package/"runtime/pythonw.exe",child
    result["bundled_runtime_confirmed"]=True
    ImageGrab.grab(all_screens=True).save(out/"offline-panel.png")
    u.PostMessageW(hwnd,0x10,0,0);p.wait(5)
    assert p.returncode==0
    result["exit_code"]=p.returncode
    result["passed"]=True
except Exception:
    import traceback
    result["error"]=traceback.format_exc()
finally:
    if p and p.poll() is None:
        hwnd=u.FindWindowW("MouseMacroSuperpower017",None)
        if hwnd:u.PostMessageW(hwnd,0x10,0,0)
    (out/"results.json").write_text(json.dumps(result,indent=2))
