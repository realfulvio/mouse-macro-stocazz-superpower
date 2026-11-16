"""Paired waits from exact ZIPs: AB/BA order, process CPU, lateness and stop.

No input injection: complements, never replaces the external event logger.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import zipfile

WORKER = r'''
import importlib, json, sys, threading, time
sys.path.insert(0, sys.argv[1])
e = importlib.import_module('macro.engine')
spacing = .008
samples = []
start_cpu = time.process_time()
start = time.perf_counter()
stop = threading.Event()
for i in range(1, 65):
    target = start + i * spacing
    assert e._wait_until(lambda: target, stop)
    samples.append((time.perf_counter() - target) * 1000)
elapsed = time.perf_counter() - start
cpu = (time.process_time() - start_cpu) / elapsed * 100
latency=[]
for _ in range(10):
    stop.clear()
    t = threading.Timer(.003, stop.set)
    t.start()
    before=time.perf_counter()
    assert not e._wait_until(lambda: before+10,stop)
    latency.append((time.perf_counter()-before)*1000)
    t.join()
print(json.dumps(dict(cpu=cpu,lateness_ms=samples,stop_ms=latency)))
'''


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',required=True)
    p.add_argument('--candidate',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    roots={}
    for kind in ('baseline','candidate'):
        with zipfile.ZipFile(getattr(a,kind)) as z:
            z.extractall(out/kind)
            roots[kind]=out/kind/z.namelist()[0].split('/')[0]
    records=[]
    for repeat in range(30):
        order=('baseline','candidate') if repeat%2==0 else ('candidate','baseline')
        for kind in order:
            root=roots[kind].resolve()
            result=json.loads(subprocess.check_output([str(root/'runtime/python.exe'),'-c',WORKER,str(root/'app')],text=True))
            records.append(dict(repeat=repeat,kind=kind,**result))
    (out/'wait-probe.json').write_text(json.dumps(records,indent=2))
    for root in roots.values():
        import shutil
        shutil.rmtree(root)
    print('WAIT_PROBE',json.dumps(records),flush=True)


if __name__=='__main__':main()
