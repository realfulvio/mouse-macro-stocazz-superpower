import csv, json, statistics, sys
from pathlib import Path
bench = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(bench))
import analyze
root=Path(sys.argv[1])
thresholds=json.loads((bench/'thresholds.json').read_text())['resources']
expected={'baseline':('1.2.5','def843426d25dc0d12a5344c750a156e81f3b5567390df816337908c09174975'), 'candidate':('1.2.5','1bfeecda34a77dc8ca2e79ee3f2c7843107cbcd4cf6bac79396fcd9729b9b80f')}
result={}
for kind,(version,digest) in expected.items():
 folder=root/kind
 def find(name):
  files=list(folder.rglob(name)); assert len(files)==1,(name,files);return files[0]
 acceptance=json.loads(find('acceptance.json').read_text())
 assert acceptance['passed'] and acceptance['version']==version and acceptance['archive_sha256']==digest, acceptance
 checks=dict(gui_package=True)
 cpu={}
 for mode,field,threshold in [('idle','cpu_pct_of_core',2),('active','registrazione_cpu_pct',5),('active','riproduzione_cpu_pct',5),('active','riproduzione_riferimento_cpu_pct',5)]:
  values=[acceptance['checks'][f'{mode}_{i}'][0][field] for i in range(3)]
  cpu[field]={'windows':values,'mean':statistics.mean(values)}
  checks[field]=cpu[field]['mean']<=threshold
 fidelity=json.loads(find('sommario_fedelta.json').read_text())
 checks.update(fidelity['checks'])
 with find('risorse_riposo.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 assert len(rows)>=2 and all(int(r['procs'])>=1 for r in rows)
 values=[float(r['cpu_pct_of_core']) for r in rows if r['cpu_pct_of_core']]
 assert all(x>=0 for x in values)
 idle={'cpu_mean':statistics.mean(values),'private_mib_max':max(float(r['private_mb']) for r in rows),'samples':len(values)}
 checks['idle_60s_cpu']=idle['cpu_mean']<=thresholds['idle_cpu_pct_of_core_avg_max']
 checks['idle_memory']=idle['private_mib_max']<=thresholds['idle_private_mb_max']
 with find('avvio.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 warm=[float(r['startup_s']) for r in rows if r['ok']=='1' and r['cold']=='0']
 startup={'successful':sum(r['ok']=='1' for r in rows),'total':len(rows),'warm':analyze.summary(warm)}
 checks['startup']=(startup['successful']==startup['total']==15 and len(warm)==14 and startup['warm']['median']<=thresholds['startup_s_median_max'] and startup['warm']['p95']<=thresholds['startup_s_p95_max'])
 inv=json.loads(find('inventario.json').read_text());assert inv['sha256']==digest
 checks['package']=inv['bytes']/1e6<=thresholds['package_mb_max']
 uipi=json.loads(find('uipi.json').read_text())
 assert uipi['casi'][2]['arrivati']==uipi['attesi']
 assert uipi['casi'][3]['arrivati']==dict.fromkeys(uipi['attesi'],0)
 if kind=='candidate':
  assert uipi['casi'][3]['pannello']['partita'] is False and uipi['casi'][3]['pannello']['giri_completati']==0
  assert 'Esegui come amministratore' in uipi['casi'][3]['pannello']['messaggio']
  find('warning-medium.png')
 result[kind]={'version':version,'sha256':digest,'inventory':inv,'cpu':cpu,'idle_60s':idle,'startup':startup,'fidelity':{k:v for k,v in fidelity.items() if k!='per_run'},'uipi':uipi,'checks':checks}
result['threshold_downgrades']=[key for key,value in result['baseline']['checks'].items() if value and not result['candidate']['checks'][key]]
result['criterion']='No previously passing frozen threshold becomes failing; CPU profiles use means of three equal windows. Shared-runner interval p95 remains reported, not certified.'
(root/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
assert result['candidate']['cpu']['riproduzione_cpu_pct']['mean'] < result['baseline']['cpu']['riproduzione_cpu_pct']['mean'], 'Dense CPU did not decrease'
raise SystemExit(bool(result['threshold_downgrades']))
