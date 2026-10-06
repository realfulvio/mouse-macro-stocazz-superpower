"""DPI-scaled GDI+ rendering for real Win32 controls; no web/client runtime."""
from __future__ import annotations
import ctypes as C
from ctypes import wintypes as W
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

P = C.c_void_p
F = C.c_float
D = C.windll.gdiplus
G = C.windll.gdi32
U = C.windll.user32
ROOT = Path(__file__).resolve().parent / 'assets'
STATES = ('pronto', 'registrazione', 'riproduzione', 'errore')
UNICORN = dict(background='#1A0F2E', surface='#2A1642', alt='#3B1D6B', border='#4B2A7A',
               text='#F9F7FF', muted='#C7B8E6', record='#FF2D93', play='#8B5CF6',
               ready='#3ED072', warning='#FFC83D', error='#FF4D6D', disabled='#493A67', faded='#8E82A9',
               header_top='#332049', header_bottom='#251735', header_text='#F9F7FF', header_muted='#C7B8E6',
               header_a='#FFC83D', header_b='#FF2D93', chrome='#322047', chrome_hover='#3B1D6B',
               surface_bottom='#21132F', surface_hover='#36234E', input='#21132F',
               button='#322047', button_hover='#3B1D6B', on_accent='#F9F7FF',
               record_hover='#FF55A8', record_pressed='#C91F6C', record_bottom='#E61980', record_edge='#FF76BB',
               play_hover='#A78BFA', play_pressed='#6D48D7', play_bottom='#6740AF',
               dot_ok='#3ED072', dot_new='#FFC83D', dot_off='#8E82A9')
PALIO = dict(background='#F6E7C8', surface='#FFF6DF', alt='#EBD3A0', border='#D2AE6B',
             text='#3A1710', muted='#6E5238', record='#C23B22', play='#1F5D8C',
             ready='#2E8B4F', warning='#8A5A00', error='#B3261E', disabled='#D9C9A6', faded='#9A8A6C',
             header_top='#9A2F1E', header_bottom='#7A2216', header_text='#FFF1D2', header_muted='#E8C9A8',
             header_a='#F2B632', header_b='#FFE2B0', chrome='#8A2818', chrome_hover='#A8402C',
             surface_bottom='#F4E3BE', surface_hover='#F6E7C8', input='#FFFDF5',
             button='#F1DDB0', button_hover='#EBD3A0', on_accent='#FFF6DF',
             record_hover='#D9533A', record_pressed='#9E2D18', record_bottom='#A93018', record_edge='#E8745C',
             play_hover='#2F78AD', play_pressed='#164767', play_bottom='#184E78',
             dot_ok='#7BE0A0', dot_new='#FFD36B', dot_off='#D9B7A0')
# `regions` crops the supplied unicorn PNGs (they carry catalog captions);
# None means the whole, already tight-cropped, image.
SKINS = {
    'unicorno': dict(label='Unicorno', prefix='unicorn', colors=UNICORN,
                     regions={'pronto': (180, 194, 126, 113), 'registrazione': (184, 191, 144, 114),
                              'riproduzione': (179, 181, 151, 119), 'errore': (209, 181, 134, 123)}),
    'palio': dict(label='Palio', prefix='palio', colors=PALIO, regions=None),
}
DEFAULT_SKIN = 'unicorno'
CURRENT = {'skin': DEFAULT_SKIN}
COLORS = dict(UNICORN)

def apply_skin(name):
    name = name if name in SKINS else DEFAULT_SKIN
    COLORS.update(SKINS[name]['colors'])
    CURRENT['skin'] = name
    return name

class RectF(C.Structure):
    _fields_ = [('x',F),('y',F),('width',F),('height',F)]
class Startup(C.Structure):
    _fields_ = [('version',W.UINT),('callback',P),('background',W.BOOL),('codecs',W.BOOL)]
class Paint(C.Structure):
    _fields_ = [('hdc',W.HDC),('erase',W.BOOL),('rect',W.RECT),('restore',W.BOOL),('update',W.BOOL),('reserved',C.c_byte*32)]
class DrawItem(C.Structure):
    _fields_ = [('type',W.UINT),('id',W.UINT),('item',W.UINT),('action',W.UINT),('state',W.UINT),
                ('hwnd',W.HWND),('hdc',W.HDC),('rect',W.RECT),('data',C.c_size_t)]

def api(lib,name,result,args):
    f=getattr(lib,name);f.restype=result;f.argtypes=args;return f

def gd(name,args): return api(D,name,C.c_int,args)
for name,args in {
 'GdiplusStartup':[C.POINTER(C.c_size_t),C.POINTER(Startup),P], 'GdiplusShutdown':[C.c_size_t],
 'GdipGraphicsClear':[P,W.DWORD],
 'GdipCreateFromHDC':[W.HDC,C.POINTER(P)],'GdipDeleteGraphics':[P],
 'GdipSetSmoothingMode':[P,C.c_int],'GdipSetInterpolationMode':[P,C.c_int],
 'GdipSetTextRenderingHint':[P,C.c_int],'GdipScaleWorldTransform':[P,F,F,C.c_int],
 'GdipSetPageUnit':[P,C.c_int],
 'GdipCreateSolidFill':[W.DWORD,C.POINTER(P)],'GdipDeleteBrush':[P],
 'GdipCreateLineBrushFromRect':[C.POINTER(RectF),W.DWORD,W.DWORD,C.c_int,C.c_int,C.POINTER(P)],
 'GdipCreatePen1':[W.DWORD,F,C.c_int,C.POINTER(P)],'GdipDeletePen':[P],
 'GdipCreatePath':[C.c_int,C.POINTER(P)],'GdipDeletePath':[P],'GdipStartPathFigure':[P],
 'GdipAddPathArc':[P,F,F,F,F,F,F],'GdipAddPathLine':[P,F,F,F,F],
 'GdipAddPathBezier':[P,F,F,F,F,F,F,F,F],'GdipClosePathFigure':[P],
 'GdipDrawPath':[P,P,P],'GdipFillPath':[P,P,P],
 'GdipFillRectangle':[P,P,F,F,F,F],'GdipFillEllipse':[P,P,F,F,F,F],
 'GdipDrawEllipse':[P,P,F,F,F,F],'GdipDrawLine':[P,P,F,F,F,F],
 'GdipCreateFontFamilyFromName':[W.LPCWSTR,P,C.POINTER(P)],'GdipDeleteFontFamily':[P],
 'GdipCreateFont':[P,F,C.c_int,C.c_int,C.POINTER(P)],'GdipDeleteFont':[P],
 'GdipNewPrivateFontCollection':[C.POINTER(P)],'GdipPrivateAddFontFile':[P,W.LPCWSTR],
 'GdipDeletePrivateFontCollection':[C.POINTER(P)],
 'GdipCreateStringFormat':[C.c_int,C.c_int,C.POINTER(P)],'GdipDeleteStringFormat':[P],
 'GdipSetStringFormatAlign':[P,C.c_int],'GdipSetStringFormatLineAlign':[P,C.c_int],
 'GdipSetStringFormatTrimming':[P,C.c_int],
 'GdipDrawString':[P,W.LPCWSTR,C.c_int,P,C.POINTER(RectF),P,P],
 'GdipLoadImageFromFile':[W.LPCWSTR,C.POINTER(P)],'GdipDisposeImage':[P],
 'GdipDrawImageRectRect':[P,P,F,F,F,F,F,F,F,F,C.c_int,P,P,P],
}.items(): gd(name,args)
api(G,'CreateCompatibleDC',W.HDC,[W.HDC]);api(G,'CreateCompatibleBitmap',W.HBITMAP,[W.HDC,C.c_int,C.c_int])
api(G,'SelectObject',W.HGDIOBJ,[W.HDC,W.HGDIOBJ]);api(G,'DeleteObject',W.BOOL,[W.HGDIOBJ])
api(G,'DeleteDC',W.BOOL,[W.HDC]);api(G,'BitBlt',W.BOOL,[W.HDC,C.c_int,C.c_int,C.c_int,C.c_int,W.HDC,C.c_int,C.c_int,W.DWORD])
api(U,'BeginPaint',W.HDC,[W.HWND,C.POINTER(Paint)]);api(U,'EndPaint',W.BOOL,[W.HWND,C.POINTER(Paint)])
api(U,'InvalidateRect',W.BOOL,[W.HWND,P,W.BOOL]);api(U,'GetClientRect',W.BOOL,[W.HWND,C.POINTER(W.RECT)])

def argb(color):
    return int(color.lstrip('#'),16)|0xff000000

def ptrcall(fn,*args):
    p=P();status=fn(*args,C.byref(p))
    if status: raise RuntimeError(f'{fn.__name__}: GDI+ {status}')
    return p

class Theme:
    def __init__(self):
        self.token=C.c_size_t();D.GdiplusStartup(C.byref(self.token),C.byref(Startup(1,None,False,False)),None)
        self.collection=ptrcall(D.GdipNewPrivateFontCollection)
        for weight in ('Regular','Bold'):
            if D.GdipPrivateAddFontFile(self.collection,str(ROOT/'fonts'/f'Outfit-{weight}.ttf')):
                raise RuntimeError('Font Outfit non disponibile')
        self.family=ptrcall(D.GdipCreateFontFamilyFromName,'Outfit',self.collection)
        self.body_family=ptrcall(D.GdipCreateFontFamilyFromName,'Segoe UI',None)
        self.fonts={};self.images={};self.sizes={};self.icons={}
        self.load_images()
        for path in (ROOT/'icons').glob('*.svg'): self.icons[path.stem]=ET.parse(path).getroot()
    def load_images(self):
        """(Re)load the mascot of the skin selected with apply_skin()."""
        prefix=SKINS[CURRENT['skin']]['prefix']
        images={state:ptrcall(D.GdipLoadImageFromFile,str(ROOT/'horses'/f'{prefix}_{state}.png')) for state in STATES}
        sizes={}
        for state,image in images.items():
            w=C.c_uint();h=C.c_uint()
            D.GdipGetImageWidth(image,C.byref(w));D.GdipGetImageHeight(image,C.byref(h))
            sizes[state]=(0,0,w.value,h.value)
        for p in self.images.values():D.GdipDisposeImage(p)
        self.images,self.sizes=images,sizes
    def close(self):
        for p in self.fonts.values():D.GdipDeleteFont(p)
        for p in self.images.values():D.GdipDisposeImage(p)
        D.GdipDeleteFontFamily(self.body_family)
        D.GdipDeleteFontFamily(self.family);D.GdipDeletePrivateFontCollection(C.byref(self.collection))
        D.GdiplusShutdown(self.token)
    def font(self,size,bold,display=False):
        key=(size,bold,display)
        family=self.family if display else self.body_family
        if key not in self.fonts:self.fonts[key]=ptrcall(D.GdipCreateFont,family,size,int(bold),2)
        return self.fonts[key]

class Canvas:
    def __init__(self,theme,hdc,width,height,scale,text_hint=5):
        self.theme=theme;self.hdc=hdc;self.width=width;self.height=height
        self.dc=G.CreateCompatibleDC(hdc);self.bmp=G.CreateCompatibleBitmap(hdc,width,height)
        self.old=G.SelectObject(self.dc,self.bmp);self.g=ptrcall(D.GdipCreateFromHDC,self.dc)
        D.GdipSetSmoothingMode(self.g,4);D.GdipSetInterpolationMode(self.g,7)
        # Work in physical bitmap pixels and apply logical DPI scaling once.
        D.GdipSetPageUnit(self.g,2)  # UnitPixel
        # ClearType on opaque panels; grayscale antialiasing on the layered bar
        # avoids colored fringes when Windows composites the translucent window.
        D.GdipSetTextRenderingHint(self.g,text_hint)
        D.GdipScaleWorldTransform(self.g,scale,scale,0)
    def close(self):
        D.GdipDeleteGraphics(self.g)
        G.BitBlt(self.hdc,0,0,self.width,self.height,self.dc,0,0,0xcc0020)
        G.SelectObject(self.dc,self.old);G.DeleteObject(self.bmp);G.DeleteDC(self.dc)
    def clear(self,color):D.GdipGraphicsClear(self.g,argb(color))
    def brush(self,color):return ptrcall(D.GdipCreateSolidFill,argb(color))
    def rect(self,x,y,w,h,color):
        b=self.brush(color);D.GdipFillRectangle(self.g,b,x,y,w,h);D.GdipDeleteBrush(b)
    def path(self,x,y,w,h,r):
        p=ptrcall(D.GdipCreatePath,0)
        for xx,yy,a in [(x,y,180),(x+w-2*r,y,270),(x+w-2*r,y+h-2*r,0),(x,y+h-2*r,90)]:
            D.GdipAddPathArc(p,xx,yy,2*r,2*r,a,90)
        D.GdipClosePathFigure(p);return p
    def rounded(self,x,y,w,h,r,color,border=None,bottom=None):
        p=self.path(x,y,w,h,r)
        b=ptrcall(D.GdipCreateLineBrushFromRect,C.byref(RectF(x,y,w,h)),argb(color),argb(bottom),1,0) if bottom else self.brush(color)
        D.GdipFillPath(self.g,b,p);D.GdipDeleteBrush(b)
        if border:
            pen=ptrcall(D.GdipCreatePen1,argb(border),1,2);D.GdipDrawPath(self.g,pen,p);D.GdipDeletePen(pen)
        D.GdipDeletePath(p)
    def line(self,x,y,xx,yy,color,width=1):
        p=ptrcall(D.GdipCreatePen1,argb(color),width,2);D.GdipDrawLine(self.g,p,x,y,xx,yy);D.GdipDeletePen(p)
    def ellipse(self,x,y,w,h,color,outline=False):
        if outline:
            p=ptrcall(D.GdipCreatePen1,argb(color),2,2);D.GdipDrawEllipse(self.g,p,x,y,w,h);D.GdipDeletePen(p)
        else:
            b=self.brush(color);D.GdipFillEllipse(self.g,b,x,y,w,h);D.GdipDeleteBrush(b)
    def text(self,text,x,y,w,h,size=14,color=None,bold=False,align=0,wrap=False,display=False):
        size=size+2 if size<=15 else size+1 if size<20 else size  # larger text, easier to read on the dark UI
        b=self.brush(color or COLORS['text']);fmt=ptrcall(D.GdipCreateStringFormat,0 if wrap else 0x1000,0)
        D.GdipSetStringFormatAlign(fmt,align);D.GdipSetStringFormatLineAlign(fmt,1)
        D.GdipSetStringFormatTrimming(fmt,3)
        D.GdipDrawString(self.g,str(text),-1,self.theme.font(size,bold,display),C.byref(RectF(x,y,w,h)),fmt,b)
        D.GdipDeleteStringFormat(fmt);D.GdipDeleteBrush(b)
    def horse(self,state,x,y,w,h):
        # Supplied PNGs include catalog captions. Display the illustration region
        # only; original files are preserved byte for byte in assets/horses.
        regions=SKINS[CURRENT['skin']]['regions'] or self.theme.sizes
        sx,sy,sw,sh=regions[state]
        ratio=min(w/sw,h/sh);dw,dh=sw*ratio,sh*ratio
        D.GdipDrawImageRectRect(self.g,self.theme.images[state],x+(w-dw)/2,y+(h-dh)/2,dw,dh,sx,sy,sw,sh,2,None,None,None)
    def icon(self,name,x,y,size,color):
        # Render the supplied SVG primitives as vectors at the actual DPI.
        scale=size/24
        for e in self.theme.icons[name]:
            tag=e.tag.split('}')[-1];a=e.attrib
            if tag=='circle':
                r=float(a['r'])*scale
                self.ellipse(x+float(a['cx'])*scale-r,y+float(a['cy'])*scale-r,2*r,2*r,color,a.get('fill')!='currentColor')
            elif tag=='rect':
                xx=x+float(a['x'])*scale;yy=y+float(a['y'])*scale
                self.rounded(xx,yy,float(a['width'])*scale,float(a['height'])*scale,float(a.get('rx',0))*scale,color)
            elif tag=='path':
                p=svg_path(a['d'],x,y,scale)
                if a.get('fill')=='currentColor':
                    b=self.brush(color);D.GdipFillPath(self.g,b,p);D.GdipDeleteBrush(b)
                else:
                    pen=ptrcall(D.GdipCreatePen1,argb(color),2*scale,2)
                    D.GdipDrawPath(self.g,pen,p);D.GdipDeletePen(pen)
                D.GdipDeletePath(p)

def svg_path(data,ox,oy,scale):
    tokens=re.findall(r'[a-zA-Z]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',data)
    p=ptrcall(D.GdipCreatePath,0);i=0;cmd='';x=y=0;start=(0,0)
    def pt(a,b):return ox+a*scale,oy+b*scale
    def segment(a,b,c,d):D.GdipAddPathLine(p,*pt(a,b),*pt(c,d))
    while i<len(tokens):
        if tokens[i].isalpha():cmd=tokens[i];i+=1
        relative=cmd.islower();op=cmd.upper()
        if op=='Z':D.GdipClosePathFigure(p);x,y=start;cmd='';continue
        count={'M':2,'L':2,'H':1,'V':1,'C':6,'A':7}[op]
        values=list(map(float,tokens[i:i+count]));i+=count
        if op in ('M','L'):
            xx,yy=values
            if relative:xx+=x;yy+=y
            if op=='M':D.GdipStartPathFigure(p);start=(xx,yy);cmd='l' if relative else 'L'
            else:segment(x,y,xx,yy)
            x,y=xx,yy
        elif op=='H':
            xx=values[0]+(x if relative else 0);segment(x,y,xx,y);x=xx
        elif op=='V':
            yy=values[0]+(y if relative else 0);segment(x,y,x,yy);y=yy
        elif op=='C':
            coords=[(values[n]+(x if relative else 0),values[n+1]+(y if relative else 0)) for n in (0,2,4)]
            D.GdipAddPathBezier(p,*pt(x,y),*pt(*coords[0]),*pt(*coords[1]),*pt(*coords[2]));x,y=coords[2]
        elif op=='A':
            rx,ry,angle,large,sweep,xx,yy=values
            if relative:xx+=x;yy+=y
            rx,ry=abs(rx),abs(ry)
            if not rx or not ry:segment(x,y,xx,yy);x,y=xx,yy;continue
            phi=math.radians(angle);co,si=math.cos(phi),math.sin(phi)
            xp=co*(x-xx)/2+si*(y-yy)/2;yp=-si*(x-xx)/2+co*(y-yy)/2
            factor=max(1,math.sqrt(xp*xp/(rx*rx)+yp*yp/(ry*ry)));rx*=factor;ry*=factor
            denom=rx*rx*yp*yp+ry*ry*xp*xp
            k=(-1 if bool(large)==bool(sweep) else 1)*math.sqrt(max(0,(rx*rx*ry*ry-denom)/denom)) if denom else 0
            cxp=k*rx*yp/ry;cyp=-k*ry*xp/rx
            cx=co*cxp-si*cyp+(x+xx)/2;cy=si*cxp+co*cyp+(y+yy)/2
            theta=math.atan2((yp-cyp)/ry,(xp-cxp)/rx)
            end=math.atan2((-yp-cyp)/ry,(-xp-cxp)/rx);delta=(end-theta)%(2*math.pi)
            if not sweep:delta-=2*math.pi
            steps=max(8,int(abs(delta)*12))
            for n in range(1,steps+1):
                t=theta+delta*n/steps;nx=cx+co*rx*math.cos(t)-si*ry*math.sin(t);ny=cy+si*rx*math.cos(t)+co*ry*math.sin(t)
                segment(x,y,nx,ny);x,y=nx,ny
            x,y=xx,yy
    return p
