"""Reproducible Windows build procedure: official embed + pinned pure Python wheels."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys, urllib.request, zipfile
VERSION = '0.18.1-beta'
ROOT = Path(__file__).resolve().parent
PACKAGE = f'MouseMacroStocazzSuperpower-Windows-v{VERSION}'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cross',action='store_true',help='Compile the Windows launcher using installed dotnet SDK 10.0.112 and official .NET 4.8 reference assemblies')
    args=parser.parse_args()
    if sys.platform != 'win32' and not args.cross:
        raise SystemExit('Eseguire su Windows x64 oppure usare --cross con SDK .NET.')
    if not args.cross and tuple(sys.version_info[:3]) != (3,13,16):
        raise SystemExit('Runtime di build richiesto: Python 3.13.16')
    cache = ROOT/'vendor'
    cache.mkdir(exist_ok=True)
    embed = cache/'python-3.13.16-embed-amd64.zip'
    if not embed.exists():
        urllib.request.urlretrieve('https://www.python.org/ftp/python/3.13.16/'+embed.name, embed)
    stage = ROOT/'build'/'native'/PACKAGE
    if stage.exists():
        shutil.rmtree(stage)
    runtime = stage/'runtime'
    app = stage/'app'
    runtime.mkdir(parents=True)
    app.mkdir()
    with zipfile.ZipFile(embed) as z:
        z.extractall(runtime)
    (runtime/'python313._pth').write_text('python313.zip\n.\nLib\n..\\app\n','utf-8')
    subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check',
        '--only-binary=:all:','--no-compile','--no-deps','--target',str(runtime/'Lib'),
        '-r',str(ROOT/'requirements-windows.txt')],check=True)
    shutil.copy2(ROOT/'windows_main.py',app/'windows_main.py')
    shutil.copy2(ROOT/'windows_visual.py',app/'windows_visual.py')
    for folder in ('horses','icons','fonts'):
        target_assets = app/'assets'/folder
        target_assets.mkdir(parents=True)
        for asset in (ROOT/'assets'/folder).iterdir():
            if folder != 'fonts' or asset.name in ('Outfit-Regular.ttf','Outfit-Bold.ttf','Outfit-OFL.txt'):
                shutil.copy2(asset,target_assets/asset.name)
    shutil.copy2(ROOT/'assets'/'icon.ico',app/'assets'/'icon.ico')
    macro = app/'macro'
    macro.mkdir()
    for name in ('__init__.py','events.py','engine.py','session.py','windows_backend.py','win_dialogs.py'):
        shutil.copy2(ROOT/'macro'/name,macro/name)
    for name in ('LICENSE','GUIDA-ITALIANA.md'):
        if (ROOT/name).exists():
            shutil.copy2(ROOT/name,stage/name)
    csc = Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe')
    exe = stage/f'Mouse Macro v{VERSION}.exe'
    if args.cross:
        references=cache/'net48-reference'
        refs=cache/'microsoft.netframework.referenceassemblies.net48.1.0.3.nupkg'
        if not refs.exists():
            urllib.request.urlretrieve('https://api.nuget.org/v3-flatcontainer/microsoft.netframework.referenceassemblies.net48/1.0.3/'+refs.name,refs)
        if not references.exists():
            with zipfile.ZipFile(refs) as z:z.extractall(references)
        refdir=references/'build'/'.NETFramework'/'v4.8'
        sdk=Path('/usr/share/dotnet/sdk/10.0.112/Roslyn/bincore/csc.dll')
        if not sdk.exists():
            raise SystemExit('SDK .NET 10.0.112 richiesto per --cross')
        subprocess.run(['dotnet',str(sdk),'/nologo','/target:winexe','/platform:x64','/optimize+',
            '/deterministic+','/nostdlib+',
            *('/reference:'+str(refdir/name) for name in ('mscorlib.dll','System.dll','System.Windows.Forms.dll')),
            '/out:'+str(exe),str(ROOT/'launcher.cs')],check=True)
    else:
        subprocess.run([str(csc),'/nologo','/target:winexe','/platform:x64','/optimize+',
            '/reference:System.Windows.Forms.dll','/out:'+str(exe),str(ROOT/'launcher.cs')],check=True)
    manifest = {'version':VERSION,'engine_base':'v0.16.0-beta',
        'runtime':'Python 3.13.16 official embeddable x64',
        'embed_sha256':hashlib.sha256(embed.read_bytes()).hexdigest(),
        'launcher':'unsigned .NET Framework launcher; original signed pythonw.exe; explicit startup',
        'compiler':'Roslyn SDK 10.0.112, net48 reference assemblies 1.0.3' if args.cross else '.NET Framework csc.exe v4.0.30319 on Windows',
        'validation':'See the release acceptance report for the exact tested ZIP hash',
        'sha256':{str(p.relative_to(stage)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(stage.rglob('*')) if p.is_file()}}
    (stage/'build_info.json').write_text(json.dumps(manifest,indent=2)+'\n','utf-8')
    out = ROOT/'dist'/'windows'
    out.mkdir(parents=True,exist_ok=True)
    target = out/(PACKAGE+'.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(stage.rglob('*')):
            if p.is_file():
                z.write(p,p.relative_to(stage.parent))
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (out/'SHA256SUMS-v0.18.1.txt').write_text(digest+'  '+target.name+'\n','ascii')
    print(str(target),digest,flush=True)

if __name__=='__main__':
    main()
