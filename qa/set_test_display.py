"""Interactive VM fixture setup: switch ONLY test display resolution."""
import ctypes as C,struct,json
from pathlib import Path
u=C.windll.user32
u.SetProcessDpiAwarenessContext(C.c_void_p(-4))
b=C.create_string_buffer(220);struct.pack_into('H',b,68,220)
assert u.EnumDisplaySettingsW(None,-1,b)
original=struct.unpack_from('III',b,168)
struct.pack_into('I',b,172,1920);struct.pack_into('I',b,176,1200)
struct.pack_into('I',b,72,0x00080000|0x00100000)
result=u.ChangeDisplaySettingsW(b,0)
Path(r'C:\Transfer\codex-display-result.json').write_text(json.dumps({'original':original,'requested':[1920,1200],'result':result}))
assert result==0
