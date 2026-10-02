"""Diagnostic packaging variant: original interpreter name and explicit launch."""
from pathlib import Path
import argparse, hashlib, json, zipfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--portable',type=Path,required=True,help='Existing portable ZIP to transform')
parser.add_argument('--output',type=Path,required=True,help='Diagnostic candidate ZIP destination')
args=parser.parse_args()
base=args.portable
out=args.output
if base.resolve()==out.resolve(): parser.error('Input and output must differ')
out.parent.mkdir(parents=True,exist_ok=True)
prefix='MouseMacroStocazzSuperpower/'
with zipfile.ZipFile(base) as old,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
    info=json.loads(old.read(prefix+'app/build_info.json'))
    info['build_method']='diagnostic packaging candidate: original signed pythonw.exe filename, explicit script invocation, no automatic sitecustomize startup'
    info['compatibility_validation']='NOT validated with SentinelOne or Internet download / Smart App Control'
    info['source_sha256'].pop(prefix+'app/sitecustomize.py',None)
    for f in old.infolist():
        name=f.filename
        if name in (prefix+'Mouse Macro Stocazz Superpower (English).exe',prefix+'app/sitecustomize.py'):continue
        data=old.read(f)
        if name==prefix+'Mouse Macro Stocazz Superpower.exe':name=prefix+'pythonw.exe'
        elif name==prefix+'app/build_info.json':data=(json.dumps(info,indent=2)+'\n').encode()
        elif name==prefix+'LEGGIMI - README.txt':
            data=('CANDIDATA DIAGNOSTICA - NON VALIDATA CON ANTIVIRUS / SMART APP CONTROL\n\n'
                  'Aprire il launcher .cmd italiano o inglese. Il runtime firmato mantiene il\n'
                  'nome pythonw.exe; lo script viene avviato esplicitamente. Nessuna protezione\n'
                  'viene modificata. Gli script scaricati possono essere bloccati dalle policy.\n'
                  'Se appare un avviso, conservare i dettagli e interrompere la prova.\n\n'
                  'Diagnostic candidate. Launch the Italian or English .cmd file. The signed\n'
                  'runtime uses its original name; explicit script startup replaces automatic\n'
                  'sitecustomize startup. Antivirus and Smart App Control acceptance unverified.\n\n'
                  'Project and design: hcok\n').encode()
        new.writestr(name,data)
    for suffix,language in (('','it'),(' (English)','en')):
        launcher='@echo off\r\nsetlocal\r\n"%~dp0pythonw.exe" -B "%~dp0app\\start.py" '+language+'\r\n'
        new.writestr(prefix+'Mouse Macro Stocazz Superpower'+suffix+'.cmd',launcher.encode('ascii'))
with zipfile.ZipFile(base) as old,zipfile.ZipFile(out) as new:
    assert new.read(prefix+'pythonw.exe')==old.read(prefix+'Mouse Macro Stocazz Superpower.exe')
    for f in old.namelist():
        if f.startswith(prefix+'python/') or f.endswith('.dll'):
            assert old.read(f)==new.read(f),f
    assert prefix+'app/sitecustomize.py' not in new.namelist()
print('Runtime and dependencies unchanged; automatic startup removed')
print(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name)
