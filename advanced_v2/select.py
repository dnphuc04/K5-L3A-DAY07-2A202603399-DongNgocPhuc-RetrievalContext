"""Select only fully reviewed dev and seal predictor before fresh test."""
from datetime import datetime,timezone
from .common import BASE,ROOT,read,write,sha,verify_benchmark
from .run import CODE

def main():
    verify_benchmark()
    if (BASE/'pipeline_freeze.json').exists() or any((BASE/'results').glob('test_*')):
        raise ValueError('Selection already sealed/test started')
    benchmark=read(BASE/'benchmarks/freeze.json')
    if sha(BASE/'legacy_snapshot.json')!=benchmark['legacy_snapshot_sha256']:raise ValueError('Legacy snapshot changed')
    policy=read(BASE/'selection_policy.json');candidates=[]
    for name in policy['candidates']:
        r=read(BASE/f'results/dev_{name}/graded_summary.json')
        reviews=read(BASE/f'results/dev_{name}/reviews.json')['reviews']
        citations=[c for q in reviews for c in q['citations']]
        r['citation_support_rate']=sum(c['supported'] for c in citations)/len(citations) if citations else 0
        candidates.append(r)
    best=max(candidates,key=lambda r:(r['rate'],-r['errors'],r['citation_support_rate'],-r['latency_ms_sum']))
    name=best['run'].split('_',1)[1];config=read(BASE/f'configs/{name}.json')
    # Predictor source used by the winning dev run must still be exact.
    for n,h in read(BASE/f'results/dev_{name}/run.json')['code_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('Winning dev code changed: '+n)
    write(BASE/'dev_comparison.json',{'split':'dev','policy':policy,'selected':name,'candidates':candidates,
        'historical_baseline':{'path':'advanced/results/test_guarded/graded_summary.json',
            'sha256':sha(ROOT/'advanced/results/test_guarded/graded_summary.json'),'n':23,'N':30,
            'role':'Former test on same questions, now development baseline only; old file unchanged.'},
        'fresh_test_evaluated':False})
    files=set(CODE+['advanced_v2/grade.py','advanced_v2/select.py','advanced_v2/selection_policy.json',
        'advanced_v2/benchmarks/freeze.json','advanced_v2/legacy_snapshot.json','advanced_v2/dev_comparison.json',f'advanced_v2/configs/{name}.json'])
    for folder in (BASE/'results').glob('dev_*'):
        files.update(str(p.relative_to(ROOT)).replace('\\','/') for p in folder.glob('*.json'))
    write(BASE/'pipeline_freeze.json',{'frozen_at':datetime.now(timezone.utc).isoformat(),
        'stage':'After complete dev review; before any fresh holdout evaluation','config':config,
        'files_sha256':{n:sha(ROOT/n) for n in sorted(files)}})
    print('Frozen selected:',name,best['n'],'/30 dev')

if __name__=='__main__':main()
