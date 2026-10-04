"""Capture real Windows UI from a running source or exact-package process."""
import ctypes as C
from ctypes import wintypes as W
from pathlib import Path
import subprocess
import sys
import time
from PIL import ImageGrab
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from macro import windows_backend as B
u=C.windll.user32
u.FindWindowW.argtypes=[W.LPCWSTR,W.LPCWSTR];u.FindWindowW.restype=W.HWND
u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
u.SetWindowPos.argtypes=[W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT]
out=ROOT/'evidence'/'preview';out.mkdir(parents=True,exist_ok=True)
from pynput import keyboard
k=keyboard.Controller();k.press(keyboard.Key.esc);k.release(keyboard.Key.esc)
p=subprocess.Popen([sys.executable,str(ROOT/'windows_main.py')])
try:
 hwnd=None
 for _ in range(100):
  hwnd=u.FindWindowW('MouseMacroSuperpower017',None)
  if hwnd:break
  time.sleep(.1)
 assert hwnd,'No panel'
 u.SetWindowPos(hwnd,W.HWND(-1),80,60,0,0,0x11)
 for mode in ('compact','expanded'):
  time.sleep(2)
  ImageGrab.grab(all_screens=True).save(out/(mode+'-desktop.png'))
  ImageGrab.grab(bbox=tuple(B.window_rect(hwnd))).save(out/(mode+'.png'))
  if mode=='compact':u.PostMessageW(hwnd,0x111,24,0)
finally:
 if hwnd:u.PostMessageW(hwnd,0x10,0,0)
 p.wait(5)
