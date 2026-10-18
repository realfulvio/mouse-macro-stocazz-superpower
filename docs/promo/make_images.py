#!/usr/bin/env python3
"""Generate the promo images: HTML pages rendered by headless Firefox, cropped with ImageMagick.

PROMO_DIR/html/img must contain the Outfit fonts, the screenshots referenced below and the
cropped horses (horse-unicorn*.png, horse-palio*.png, dialog-updates.png).
Usage: PROMO_DIR=... python3 make_images.py [page ...]
"""
import os, subprocess, sys, shutil
from pathlib import Path

P = Path(os.environ.get('PROMO_DIR', '/srv/dev/scratch/promo'))
H, OUT = P / 'html', P / 'out'
ONLY = set(sys.argv[1:])

CSS = """
@font-face{font-family:Outfit;src:url(img/Outfit-Regular.ttf);font-weight:400}
@font-face{font-family:Outfit;src:url(img/Outfit-Bold.ttf);font-weight:700}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:%(w)dpx;height:%(h)dpx;overflow:hidden}
body{font-family:Outfit,sans-serif;color:#F9F7FF;position:relative;
 background:
  radial-gradient(900px 520px at 88%% 18%%,rgba(255,45,147,.30),transparent 60%%),
  radial-gradient(800px 600px at 8%% 100%%,rgba(139,92,246,.40),transparent 60%%),
  radial-gradient(500px 300px at 50%% 0%%,rgba(255,200,61,.10),transparent 70%%),
  linear-gradient(135deg,#140a24 0%%,#24113d 45%%,#3a1450 100%%)}
.grain{position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.035) 1px,transparent 1px);background-size:6px 6px;pointer-events:none}
.shot{border-radius:16px;box-shadow:0 30px 60px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.10);display:block}
.label{display:inline-flex;align-items:center;gap:8px;padding:7px 14px;border-radius:999px;font-weight:700;font-size:18px;
 background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.18);backdrop-filter:blur(6px)}
.dot{width:10px;height:10px;border-radius:50%%;display:inline-block}
.y{color:#FFC83D}.p{color:#FF2D93}.v{color:#B79BFF}.m{color:#DED5EF}
h1{font-weight:700;letter-spacing:-.02em;line-height:1}
.pill{display:inline-block;padding:8px 16px;border-radius:12px;font-weight:700;font-size:20px;margin:0 8px 10px 0}
.code{font-family:'DejaVu Sans Mono',monospace;font-size:17px;background:rgba(0,0,0,.40);border:1px solid rgba(255,255,255,.14);
 border-radius:12px;padding:12px 16px;color:#FFE7A3;word-break:break-all;line-height:1.45}
"""

T = {
 'it': dict(tag='Registra il mouse.<br>Ripeti quanto vuoi.', sub='Un pannello compatto, sempre in primo piano. Nessun installer, nessun Python da installare.',
            win='Windows 11', lin='Linux · X11 e Wayland', free='Gratis per uso personale',
            f=[('Barra attiva compatta','Contatori e Stop grande mentre registra o riproduce.'),
               ('1–999 ripetizioni · 2×','Normale o Rapida, con click e doppi click protetti.'),
               ('Movimento umano','Percorsi e pause cambiano a ogni giro; i clic restano lì.'),
               ('Skin Unicorno e Palio','Scuro viola o chiaro con il sauro di contrada.'),
               ('Aggiornamenti verificati','Pallino di stato, download con controllo SHA-256.'),
               ('Solo il mouse','Niente tastiera, niente schermate, una sola richiesta di rete anonima.')],
            feat_title='Tutto quello che serve, niente di più',
            wtitle='Per Windows', wsub='v1.1.1 · avvio da PowerShell o ZIP portable con exe e .cmd senza exe',
            wb=['Pannello sempre in primo piano che non ruba il focus','Barra semitrasparente da 288×64 durante l’attività','Ctrl+Tab tra un giro e l’altro, Pagine lente','Modello del mouse rilevato'],
            ltitle='Per Linux', lsub='linux-v1.0.0 · X11 e Wayland, evdev + uinput, interfaccia IT/EN',
            lb=['Stesse funzioni della versione Windows','Installazione con un comando, nessun sudo','Movimento umano anche con spostamenti relativi','Diagnostica in ~/.config, preferenze ricordate'],
            priv=[('✕','#FF4D6D','Tastiera: mai registrata'),('✕','#FF4D6D','Schermate: nessuna'),('1','#FFC83D','Rete: solo il controllo aggiornamenti')],
            stitle='Due skin, stessa potenza', unic='Unicorno', palio='Palio', sdesc_u='Viola scuro, predefinita', sdesc_p='Chiara, sauro con i nastri di contrada'),
 'en': dict(tag='Record your mouse.<br>Replay it as often as you like.', sub='A compact always-on-top panel. No installer, no Python to install.',
            win='Windows 11', lin='Linux · X11 and Wayland', free='Free for personal use',
            f=[('Compact activity bar','Counters and a big Stop while recording or playing.'),
               ('1–999 repeats · 2×','Normal or Fast, clicks and double clicks protected.'),
               ('Human-like movement','Paths and pauses change every cycle; clicks stay put.'),
               ('Unicorn and Palio skins','Dark violet or light with the Palio chestnut.'),
               ('Verified updates','Status dot, downloads checked with SHA-256.'),
               ('Mouse only','No keyboard, no screenshots, one anonymous network call.')],
            feat_title='Everything you need, nothing more',
            wtitle='For Windows', wsub='v1.1.1 · start from PowerShell or the portable ZIP (exe or exe-free .cmd)',
            wb=['Always-on-top panel that never steals focus','288×64 semi-transparent bar while active','Ctrl+Tab between cycles, Slow pages','Detected mouse model'],
            ltitle='For Linux', lsub='linux-v1.0.0 · X11 and Wayland, evdev + uinput, IT/EN interface',
            lb=['Same features as the Windows version','One-command install, no sudo','Human-like movement with relative motion too','Diagnostics in ~/.config, remembered preferences'],
            priv=[('✕','#FF4D6D','Keyboard: never recorded'),('✕','#FF4D6D','Screenshots: none'),('1','#FFC83D','Network: update check only')],
            stitle='Two skins, same power', unic='Unicorn', palio='Palio', sdesc_u='Dark violet, default', sdesc_p='Light, chestnut with Palio ribbons'),
}
PS = 'irm https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.ps1 | iex'
SH = 'curl -fsSL https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.sh | bash'

def page(name, w, h, body):
    html = f"<!doctype html><html><head><meta charset=utf-8><style>{CSS % dict(w=w, h=h)}</style></head><body><div class=grain></div>{body}</body></html>"
    (H / f'{name}.html').write_text(html, 'utf-8')
    return name, w, h

def logo(size=64):
    return f"""<div style="display:flex;align-items:center;gap:16px">
 <img src="img/horse-unicorn.png" style="width:{size+16}px;height:{size+16}px;object-fit:contain;filter:drop-shadow(0 6px 14px rgba(255,45,147,.5))">
 <div><div style="font-weight:700;font-size:{size*0.5:.0f}px;line-height:1">Mouse Macro</div>
 <div style="font-weight:700;font-size:{size*0.42:.0f}px"><span class=y>Stocazz</span> <span class=p>Superpower</span></div></div></div>"""

pages = []
for L, t in T.items():
    # Hero 1600x640
    pages.append(page(f'hero-{L}', 1600, 640, f"""
<div style="position:absolute;left:80px;top:70px;width:700px">
 {logo(70)}
 <h1 style="font-size:70px;margin-top:44px">{t['tag']}</h1>
 <p class=m style="font-size:24px;margin-top:22px;line-height:1.35;width:620px">{t['sub']}</p>
 <div style="margin-top:30px"><span class=label><span class=dot style="background:#3ED072"></span>{t['win']}</span>
 <span class=label style="margin-left:10px"><span class=dot style="background:#FFC83D"></span>{t['lin']}</span></div>
</div>
<img src="img/horse-unicorn-run.png" style="position:absolute;left:640px;top:370px;width:300px;opacity:.95;filter:drop-shadow(0 10px 30px rgba(255,45,147,.45))">
<img class=shot src="img/v111-windows11-compact.png" style="position:absolute;left:940px;top:40px;width:280px;transform:rotate(-4deg)">
<img class=shot src="img/linux-ready-{'en' if L=='en' else 'it'}.png" style="position:absolute;left:1250px;top:28px;width:280px;transform:rotate(3deg)">
<img class=shot src="img/linux-playing-palio.png" style="position:absolute;left:1030px;top:455px;width:400px;transform:rotate(-1deg)">
"""))
    # Social 1200x630
    pages.append(page(f'social-{L}', 1200, 630, f"""
<div style="position:absolute;left:64px;top:64px;width:600px">
 {logo(60)}
 <h1 style="font-size:58px;margin-top:40px">{t['tag']}</h1>
 <div style="margin-top:34px"><span class=label><span class=dot style="background:#3ED072"></span>Windows</span>
 <span class=label style="margin-left:10px"><span class=dot style="background:#FFC83D"></span>Linux</span>
 <span class=label style="margin-left:10px">{t['free']}</span></div>
 <p class=m style="font-size:20px;margin-top:40px">github.com/realfulvio/mouse-macro-stocazz-superpower</p>
</div>
<img class=shot src="img/v111-windows11-compact.png" style="position:absolute;left:700px;top:60px;width:250px;transform:rotate(-4deg)">
<img class=shot src="img/linux-ready-palio.png" style="position:absolute;left:920px;top:80px;width:250px;transform:rotate(4deg)">
"""))
    # Feature grid 1600x1000
    shots = ['v100-playing.png|linux-recording-it.png', 'linux-options-it.png', 'v110-palio-movimento-umano.png',
             'v110-unicorno-compatto.png|v110-palio-compatto.png', 'dialog-updates.png', 'PRIVACY']
    tiles = ''
    for (title, desc), s in zip(t['f'], shots):
        imgs = s.split('|')
        if imgs[0] == 'PRIVACY':
            rows = t['priv']
            inner = '<div style="padding:22px 30px 0">' + ''.join(
                f'''<div style="display:flex;align-items:center;gap:16px;margin-bottom:12px;padding:12px 18px;border-radius:16px;background:rgba(0,0,0,.25);border:1px solid rgba(255,255,255,.10)">
<span style="width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:24px;background:{c};color:#1A0F2E">{sym}</span>
<span style="font-size:21px;font-weight:700">{txt}</span></div>''' for sym, c, txt in rows) + '</div>'
        elif imgs[0] == 'dialog-updates.png':
            inner = f"""<img class=shot src="img/dialog-updates.png" style="width:250px;margin:18px auto 0">"""
        elif len(imgs) == 2 and 'playing' in imgs[0]:
            inner = f"""<img class=shot src="img/{imgs[0]}" style="width:360px;margin:30px auto 18px"><img class=shot src="img/{imgs[1]}" style="width:300px;margin:0 auto">"""
        elif len(imgs) == 2:
            inner = f"""<div style="display:flex;gap:16px;justify-content:center;margin-top:18px"><img class=shot src="img/{imgs[0]}" style="width:150px"><img class=shot src="img/{imgs[1]}" style="width:150px"></div>"""
        else:
            inner = f"""<div style="height:262px;overflow:hidden;border-radius:16px;margin:18px 22px 0;box-shadow:0 20px 40px rgba(0,0,0,.5),0 0 0 1px rgba(255,255,255,.1)"><img src="img/{imgs[0]}" style="width:100%;display:block"></div>"""
        tiles += f"""<div style="background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(255,255,255,.03));border:1px solid rgba(255,255,255,.12);border-radius:22px;overflow:hidden;height:420px;position:relative">
 <div style="height:315px;overflow:hidden">{inner}</div>
 <div style="position:absolute;left:24px;right:24px;bottom:22px"><div style="font-weight:700;font-size:26px">{title}</div><div class=m style="font-size:18px;margin-top:6px;line-height:1.3">{desc}</div></div></div>"""
    pages.append(page(f'features-{L}', 1600, 1040, f"""
<div style="position:absolute;left:70px;top:46px;right:70px;display:flex;justify-content:space-between;align-items:center">
 <h1 style="font-size:46px">{t['feat_title']}</h1>{logo(46)}</div>
<div style="position:absolute;left:70px;right:70px;top:140px;display:grid;grid-template-columns:repeat(3,1fr);gap:28px">{tiles}</div>
"""))
    # Windows card 1600x900
    bullets = ''.join(f'<li style="margin:10px 0">{b}</li>' for b in t['wb'])
    pages.append(page(f'windows-{L}', 1600, 900, f"""
<div style="position:absolute;left:80px;top:70px;width:620px">
 <span class=label><span class=dot style="background:#3ED072"></span>{t['win']}</span>
 <h1 style="font-size:72px;margin-top:22px">{t['wtitle']}</h1>
 <p class=m style="font-size:22px;margin-top:14px;line-height:1.35">{t['wsub']}</p>
 <ul style="font-size:24px;margin:28px 0 0 26px;line-height:1.3">{bullets}</ul>
 <div style="margin-top:36px;font-weight:700;font-size:18px" class=y>PowerShell</div>
 <div class=code style="margin-top:8px;width:620px;font-size:16px">{PS}</div>
</div>
<img class=shot src="img/v111-windows11-expanded.png" style="position:absolute;left:820px;top:90px;width:640px">
<img class=shot src="img/v111-windows11-compact.png" style="position:absolute;left:740px;top:400px;width:260px;transform:rotate(-3deg)">
<img class=shot src="img/v100-playing.png" style="position:absolute;left:1080px;top:760px;width:400px">
"""))
    # Linux card 1600x900
    bullets = ''.join(f'<li style="margin:10px 0">{b}</li>' for b in t['lb'])
    pages.append(page(f'linux-{L}', 1600, 900, f"""
<div style="position:absolute;left:80px;top:70px;width:620px">
 <span class=label><span class=dot style="background:#FFC83D"></span>{t['lin']}</span>
 <h1 style="font-size:72px;margin-top:22px">{t['ltitle']}</h1>
 <p class=m style="font-size:22px;margin-top:14px;line-height:1.35">{t['lsub']}</p>
 <ul style="font-size:24px;margin:28px 0 0 26px;line-height:1.3">{bullets}</ul>
 <div style="margin-top:36px;font-weight:700;font-size:18px" class=y>Terminal</div>
 <div class=code style="margin-top:8px;width:620px;font-size:16px">{SH}</div>
</div>
<img class=shot src="img/linux-options-{'it' if L=='it' else 'it'}.png" style="position:absolute;left:760px;top:60px;width:760px">
<img class=shot src="img/linux-recording-it.png" style="position:absolute;left:80px;top:690px;width:400px;transform:rotate(-1.5deg)">
<img class=shot src="img/linux-playing-palio.png" style="position:absolute;left:1180px;top:700px;width:340px;transform:rotate(2deg)">
"""))
    # Skins 1600x820
    pages.append(page(f'skins-{L}', 1600, 820, f"""
<div style="position:absolute;left:0;right:0;top:44px;text-align:center"><h1 style="font-size:52px">{t['stitle']}</h1></div>
<div style="position:absolute;left:60px;top:150px;width:700px;height:620px;border-radius:28px;background:linear-gradient(160deg,#2A1642,#1A0F2E);border:1px solid #4B2A7A">
 <div style="position:absolute;left:34px;top:26px"><div style="font-weight:700;font-size:34px">{t['unic']}</div><div class=m style="font-size:18px">{t['sdesc_u']}</div></div>
 <img src="img/horse-unicorn.png" style="position:absolute;right:30px;top:14px;width:120px">
 <img class=shot src="img/v110-unicorno-compatto.png" style="position:absolute;left:40px;top:130px;width:260px">
 <img class=shot src="img/linux-ready-it.png" style="position:absolute;left:330px;top:140px;width:250px">
 <div style="position:absolute;left:40px;top:604px" class=m></div>
</div>
<div style="position:absolute;right:60px;top:150px;width:700px;height:620px;border-radius:28px;background:linear-gradient(160deg,#FFF6DF,#F6E7C8);border:1px solid #D2AE6B;color:#3A1710">
 <div style="position:absolute;left:34px;top:26px"><div style="font-weight:700;font-size:34px">{t['palio']}</div><div style="font-size:18px;color:#60452E">{t['sdesc_p']}</div></div>
 <img src="img/horse-palio.png" style="position:absolute;right:30px;top:12px;width:110px">
 <img class=shot src="img/v110-palio-compatto.png" style="position:absolute;left:40px;top:130px;width:260px">
 <img class=shot src="img/linux-ready-palio.png" style="position:absolute;left:330px;top:140px;width:250px">
</div>
<div style="position:absolute;left:60px;bottom:16px;font-size:16px" class=m>Windows · Linux</div>
"""))

prof = Path('/tmp/ffpromo')
for name, w, h in pages:
    if ONLY and name not in ONLY:
        continue
    shutil.rmtree(prof, ignore_errors=True); prof.mkdir()
    raw = OUT / f'{name}.raw.png'
    subprocess.run(['timeout', '90', 'firefox', '--headless', '--no-remote', '--profile', str(prof),
                    f'--window-size={w},{h}', '--screenshot', str(raw), f'file://{H}/{name}.html'],
                   check=True, capture_output=True)
    subprocess.run(['magick', str(raw), '-crop', f'{w}x{h}+0+0', '+repage', '-strip', '-define', 'png:compression-level=9',
                    str(OUT / f'{name}.png')], check=True)
    raw.unlink()
    print(name, (OUT / f'{name}.png').stat().st_size // 1024, 'KB', flush=True)
