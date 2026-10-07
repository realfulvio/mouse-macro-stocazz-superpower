"""Render the actual GDI+ panel offscreen; no desktop input or settings changes.

This checks rendering at fixed DPI, not interactive or monitor acceptance.
Requires Pillow. --package-root selects an extracted release ZIP.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package-root', type=Path)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(args.package_root / 'app' if args.package_root else root))
import windows_main as ui
from PIL import Image


class Header(C.Structure):
    _fields_ = [('size', W.DWORD), ('width', W.LONG), ('height', W.LONG),
                ('planes', W.WORD), ('bits', W.WORD), ('compression', W.DWORD),
                ('image_size', W.DWORD), ('xppm', W.LONG), ('yppm', W.LONG),
                ('used', W.DWORD), ('important', W.DWORD)]


class BitmapInfo(C.Structure):
    _fields_ = [('header', Header), ('colors', W.DWORD * 3)]


g = ui.G
ui.api(g, 'CreateDIBSection', W.HBITMAP,
       [W.HDC, C.POINTER(BitmapInfo), W.UINT, C.POINTER(C.c_void_p), W.HANDLE, W.DWORD])
ui.api(g, 'SetViewportOrgEx', W.BOOL, [W.HDC, C.c_int, C.c_int, C.POINTER(W.POINT)])
args.out.mkdir(parents=True, exist_ok=True)
theme = ui.Theme()
results = []
try:
    for dpi in (96, 120, 144, 192):
        for mode in ('compact', 'expanded', 'recording', 'playing', 'stopping'):
            p = ui.Panel.__new__(ui.Panel)
            p.theme = theme; p.dpi = dpi; p.hover = None
            p.active_view = mode in ('recording', 'playing', 'stopping')
            p.expanded = mode == 'expanded'
            p.width, p.height = ui.ACTIVE_SIZE if p.active_view else (640, 608) if p.expanded else (340, 600)
            p.repeats = 999; p.speed = 2; p.next_tab = False; p.slow = False
            p.human = False
            p.mouse_description = 'Mouse: Logitech G502 HERO'
            p.record_started = time.monotonic() - 62
            p.play_started = time.monotonic() - 62
            p.session = SimpleNamespace(state={'recording':ui.State.RECORDING,
                'playing':ui.State.PLAYING,'stopping':ui.State.STOPPING}.get(mode,ui.State.READY),
                completed=998, macro=SimpleNamespace(events=[]), recorder=SimpleNamespace(current_event_count=12345),
                message='Macro pronta. Ripristina lo stato iniziale, poi F10.')
            width, height = round(p.width*dpi/96), round(p.height*dpi/96)
            dc = g.CreateCompatibleDC(None)
            bits = C.c_void_p()
            info = BitmapInfo(Header(C.sizeof(Header),width,-height,1,32,0,width*height*4,0,0,0,0))
            bmp = g.CreateDIBSection(dc,C.byref(info),0,C.byref(bits),None,0)
            if not dc or not bmp or not bits.value:
                raise C.WinError()
            old = g.SelectObject(dc,bmp)
            try:
                def client(hwnd, rect):
                    r = C.cast(rect,C.POINTER(W.RECT)).contents
                    r.left=r.top=0;r.right=width;r.bottom=height
                    return True
                with patch.object(ui.U,'BeginPaint',return_value=dc), \
                     patch.object(ui.U,'EndPaint',return_value=True), \
                     patch.object(ui.U,'GetClientRect',side_effect=client), \
                     patch.object(ui.U,'IsWindowEnabled',return_value=True):
                    p.paint(None)
                    boxes = {12:(208,12,72,40)} if p.active_view else {}
                    if not p.active_view:
                        boxes.update({201:(p.width-98,7,28,28),202:(p.width-66,7,28,28),203:(p.width-34,7,28,28)})
                        boxes.update({10:(16,244,298,64),11:(326,244,298,64),24:(16,324,608,44),
                            21:(32,410,34,38),23:(112,410,34,38),25:(32,457,114,30),
                            31:(192,402,162,38),32:(192,442,162,38),40:(386,399,220,38),41:(386,444,220,38),
                            101:(192,495,162,38),102:(366,495,240,38),104:(20,558,104,34),110:(346,562,266,30)}
                            if p.expanded else {10:(16,322,308,64),11:(16,398,308,64),24:(16,478,308,44),104:(20,538,98,34),110:(146,535,178,46)})
                    p.boxes = boxes
                    for cid,(x,y,w,h) in boxes.items():
                        pw,ph=round(w*dpi/96),round(h*dpi/96)
                        g.SetViewportOrgEx(dc,round(x*dpi/96),round(y*dpi/96),None)
                        p.draw_control(SimpleNamespace(id=cid,rect=W.RECT(0,0,pw,ph),hdc=dc,state=0,hwnd=None))
                    g.SetViewportOrgEx(dc,0,0,None)
                raw=C.string_at(bits,width*height*4)
                image=Image.frombytes('RGB',(width,height),raw,'raw','BGRX')
                path=args.out/f'{mode}-{dpi}.png'
                image.save(path)
                results.append({'mode':mode,'dpi':dpi,'pixels':[width,height],'file':path.name})
            finally:
                g.SelectObject(dc,old);g.DeleteObject(bmp);g.DeleteDC(dc)
finally:
    theme.close()
(args.out/'rendering.json').write_text(json.dumps({'scope':'OFFSCREEN_GDI_ONLY_NO_DESKTOP_INPUT',
    'version':ui.VERSION,'native_edit_control_rendered':False,'renders':results},indent=2),'utf-8')
print('OFFSCREEN_GDI_RENDER_OK',len(results))
