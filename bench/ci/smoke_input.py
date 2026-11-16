"""Smoke test sul runner: inietta 3 clic con SendInput e stampa schermo/DPI. Il logger esterno gira in parallelo."""
import ctypes, sys, time
from ctypes import wintypes as W
u = ctypes.windll.user32
u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
w, h = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
print(f"schermo primario {w}x{h}, DPI finestra desktop {u.GetDpiForSystem()}, monitor {u.GetSystemMetrics(80)}", flush=True)

class MI(ctypes.Structure):
    _fields_ = [("dx", W.LONG), ("dy", W.LONG), ("data", W.DWORD), ("flags", W.DWORD), ("time", W.DWORD), ("extra", ctypes.c_size_t)]
class IN(ctypes.Structure):
    class U(ctypes.Union): _fields_ = [("mi", MI)]
    _anonymous_ = ("u",); _fields_ = [("type", W.DWORD), ("u", U)]

def send(flags, x=0, y=0):
    r = u.SendInput(1, ctypes.byref(IN(0, IN.U(MI(x, y, 0, flags, 0, 0)))), ctypes.sizeof(IN))
    return r

time.sleep(2)
for i, (fx, fy) in enumerate([(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)]):
    x, y = round(w * fx), round(h * fy)
    r1 = send(0x0001 | 0x8000, round(x * 65535 / (w - 1)), round(y * 65535 / (h - 1)))
    r2 = send(0x0002); time.sleep(0.15); r3 = send(0x0004)
    print(f"clic {i+1} atteso ({x},{y}) SendInput={r1},{r2},{r3} cursore={ctypes.wintypes.POINT().x}", flush=True)
    time.sleep(0.8)
