import json,sys,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import analyze
p=Path(sys.argv[1]);raw=json.loads(p.read_text());out={}
for kind in ('baseline','candidate'):
 rows=[r for r in raw if r['kind']==kind];assert len(rows)==30
 out[kind]={
  'cpu':analyze.summary([r['cpu'] for r in rows]),
  'lateness_ms':analyze.summary([x for r in rows for x in r['lateness_ms']]),
  'stop_ms':analyze.summary([x for r in rows for x in r['stop_ms']]),
 }
out['differences']={k:out['candidate']['lateness_ms'][k]-out['baseline']['lateness_ms'][k] for k in ('median','p95','max')}
out['cpu_reduction_pct']=100*(1-out['candidate']['cpu']['mean']/out['baseline']['cpu']['mean'])
(p.parent/'wait-probe-summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
