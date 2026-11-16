"""Iniettore di riferimento: riproduce la spec con SendInput e attese QPC (ideale, senza l'errore di un registratore).
Serve a 'registrare' le macro di strumenti che si registrano da soli (TinyTask): l'input arriva ai loro hook come input reale."""
import ctypes, json, sys, time
from ctypes import wintypes as W

u, k = ctypes.windll.user32, ctypes.windll.kernel32
try: u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception: pass
freq = ctypes.c_int64(); k.QueryPerformanceFrequency(ctypes.byref(freq))
def now():
    c = ctypes.c_int64(); k.QueryPerformanceCounter(ctypes.byref(c)); return c.value / freq.value

class MI(ctypes.Structure):
    _fields_ = [("dx", W.LONG), ("dy", W.LONG), ("data", W.DWORD), ("flags", W.DWORD), ("time", W.DWORD), ("extra", ctypes.c_size_t)]
class IN(ctypes.Structure):
    class U(ctypes.Union): _fields_ = [("mi", MI)]
    _anonymous_ = ("u",); _fields_ = [("type", W.DWORD), ("u", U)]

def _send(flags, x=0, y=0, data=0):
    if u.SendInput(1, ctypes.byref(IN(0, IN.U(MI(x, y, data & 0xFFFFFFFF, flags, 0, 0)))), ctypes.sizeof(IN)) != 1:
        raise OSError("SendInput rifiutata")

def move(x, y):
    w, h = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    _send(0x0001 | 0x8000, round(x * 65535 / (w - 1)), round(y * 65535 / (h - 1)))

def play(spec):
    t0 = now()
    for e in spec["events"]:
        while now() - t0 < e["t"]:
            if e["t"] - (now() - t0) > 0.004: time.sleep(0.001)
        move(e["x"], e["y"])
        _send({"ldown": 0x0002, "lup": 0x0004, "wheel": 0x0800}[e["kind"]], data=e.get("data", 0))

if __name__ == "__main__":
    play(json.load(open(sys.argv[1])))
