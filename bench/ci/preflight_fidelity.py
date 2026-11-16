"""Same external logger/reference/analyzer as bench.yml, against a source checkout.

This is a source A/B for preflight changes, not a measurement of the release ZIP.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import run_tool
import analyze
import reference_macro


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--runs', type=int, default=30)
    a = ap.parse_args()
    source, out = Path(a.source).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    w, h = run_tool.set_display()
    events = reference_macro.build(w, h)
    spec = dict(width=w, height=h, events=events)
    (out / 'reference.spec.json').write_text(json.dumps(spec))
    macro = out / 'reference.mmr'
    macro.write_text(json.dumps(reference_macro.to_mmr(events, w, h, 0, 0)))
    pythonw = Path(sys.executable).with_name('pythonw.exe')
    runs = out / 'fedelta'
    runs.mkdir(exist_ok=True)
    for i in range(1, a.runs + 1):
        logger = subprocess.Popen([sys.executable, str(run_tool.ROOT / 'bench/logger/inputlogger.py'),
            '--out', str(runs / f'run_{i:02d}.csv'), '--duration', str(events[-1]['t'] + 10), '--no-moves'])
        time.sleep(1.2)
        player = subprocess.Popen([str(pythonw), '-B', str(source / 'windows_main.py'),
            '--run', str(macro), '--repeat', '1'], cwd=source)
        time.sleep(3)
        run_tool.press('ENTER')
        logger.wait(timeout=40)
        try:
            code = player.wait(timeout=10)
            if code:
                raise RuntimeError(f'player exited {code}')
        finally:
            if player.poll() is None:
                player.kill()
        time.sleep(1)
        print(f'run {i}/{a.runs}', flush=True)
    thresholds = json.loads((run_tool.ROOT / 'bench/thresholds.json').read_text())
    result = analyze.evaluate(spec, sorted(map(str, runs.glob('run_*.csv'))), thresholds)
    result['source_commit'] = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    result['timed_code_sha256'] = {p: hashlib.sha256((source / p).read_bytes()).hexdigest()
        for p in ('macro/engine.py', 'macro/windows_backend.py')}
    result['condition'] = 'source, Python 3.13, shared Windows runner; not release ZIP'
    (out / 'sommario_fedelta.json').write_text(json.dumps(result, indent=2))
    print('SOURCE_FIDELITY', json.dumps({k: v for k, v in result.items() if k != 'per_run'}), flush=True)


if __name__ == '__main__':
    main()
