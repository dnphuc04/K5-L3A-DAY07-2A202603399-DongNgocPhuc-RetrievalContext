"""Verify fresh-test evidence and unchanged historical artifacts, without API calls."""
from datetime import datetime
from collections import Counter
from .common import BASE,ROOT,read,write,sha,verify_benchmark

def check():
    errors=[]
    try:verify_benchmark()
    except Exception as exc:errors.append(str(exc))
    lock=read(BASE/'pipeline_freeze.json')
    for name,digest in lock['files_sha256'].items():
        if sha(ROOT/name)!=digest:errors.append('Frozen file changed: '+name)
    folder=BASE/'results/test_reasoned';meta=read(folder/'run.json')
    gold=read(BASE/'benchmarks/test.gold.json');inputs=read(BASE/'benchmarks/test.inputs.json')
    groups=Counter(q['primary_group'] for q in gold)
    if groups!=Counter(table=6,diagram=5,chart=5,multi_hop=4,text=4,unanswerable=6):errors.append('Group/count mismatch')
    if meta['config']!=lock['config'] or meta['input_ids']!=[q['id'] for q in inputs]:errors.append('Test config/subset changed')
    if any(set(q)!={'id','question'} for q in inputs):errors.append('Gold fields in predictor inputs')
    if meta['code_sha256']!=read(BASE/'results/dev_reasoned/run.json')['code_sha256']:errors.append('Predictor code differs from selected dev')
    if meta['pipeline_freeze_sha256']!=sha(BASE/'pipeline_freeze.json'):errors.append('Run freeze reference differs')
    if not (datetime.fromisoformat(read(BASE/'benchmarks/freeze.json')['frozen_at'])<
            datetime.fromisoformat(read(BASE/'results/dev_reasoned_smoke/run.json')['started_at'])<
            datetime.fromisoformat(lock['frozen_at'])<datetime.fromisoformat(meta['started_at'])):
        errors.append('Benchmark/dev/pipeline/test chronology invalid')
    labels=read(folder/'reviews.json')['reviews'];byid={r['id']:r for r in labels}
    if len(labels)!=30 or set(byid)!={q['id'] for q in gold}:errors.append('Need exactly 30 unique test reviews')
    for q in gold:
        path=folder/f"{q['id']}.json";t=read(path);r=byid[q['id']]
        cs=[c for claim in t['claims'] for c in claim['citations']]
        if sha(path)!=r['trace_sha256'] or len(r['citations'])!=len(cs) or not r['reason']:errors.append('Stale/incomplete review '+q['id'])
        if t['status']=='error' and r['passed']:errors.append('Error marked pass')
        for c in cs:
            if int(c['source_id'].rsplit('p',1)[1]) not in t['viewed_pages']:errors.append('Unviewed source cited '+q['id'])
    score=read(folder/'graded_summary.json')
    if score['N']!=30 or score['n']!=sum(r['passed'] for r in labels):errors.append('Score mismatch')
    old=read(ROOT/'advanced/results/test_guarded/graded_summary.json')
    if (old['n'],old['N'])!=(23,30):errors.append('Old test score changed')
    coverage=read(ROOT/'advanced/coverage_check.json')
    if coverage['rendered_pages']!=297 or coverage['render_errors']:errors.append('Incomplete inherited source coverage')
    receipt=BASE/'evaluation_receipt.json'
    if receipt.exists():
        for name,digest in read(receipt)['files_sha256'].items():
            if sha(ROOT/name)!=digest:errors.append('Receipt mismatch '+name)
    return {'checks_passed':not errors,'errors':errors,'historical_test_unchanged':{'n':23,'N':30},
        'fresh_test':{'n':score['n'],'N':score['N'],'system_errors':score['errors']},
        'at_least_90_percent':10*score['n']>=9*score['N'],
        'chronology':'fresh benchmark -> dev experiments/reviews -> selected pipeline freeze -> full fresh test',
        'scope':'Integrity/evidence preflight, not an award of rubric points or independent external grading.'}

if __name__=='__main__':
    result=check();write(BASE/'submission_check.json',result);print(result)
    if result['errors']:raise SystemExit(1)
