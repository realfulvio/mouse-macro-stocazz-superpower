"""Operate only the Windows test VM display settings and capture their actual result."""
import ctypes as C
import json
import os
from pathlib import Path
import sys
import time
from PIL import ImageGrab
from pynput import mouse, keyboard
u=C.windll.user32
u.SetProcessDpiAwarenessContext(C.c_void_p(-4))
out=Path(r"C:\Projects\mouse-macro-v016\evidence\display-fixture")
out.mkdir(exist_ok=True)
action=sys.argv[1]
if action=="show":
    import runpy
    runpy.run_path(str(Path(__file__).with_name("set_test_display.py")))
    os.startfile("ms-settings:display")
    time.sleep(3)
elif action=="click":
    m=mouse.Controller();m.position=(int(sys.argv[2]),int(sys.argv[3]))
    m.click(mouse.Button.left);time.sleep(1)
elif action=="escape":
    k=keyboard.Controller();k.press(keyboard.Key.esc);k.release(keyboard.Key.esc)
    time.sleep(.5)
ImageGrab.grab(all_screens=True).save(out/(action+".png"))
(out/(action+".json")).write_text(json.dumps({"dpi":u.GetDpiForSystem(),"screen":[u.GetSystemMetrics(0),u.GetSystemMetrics(1)]}))
