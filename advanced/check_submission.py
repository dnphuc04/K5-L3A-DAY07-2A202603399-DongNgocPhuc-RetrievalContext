"""Offline advanced preflight: frozen provenance, complete labels and source coverage."""
from collections import Counter
from .common import BASE,ROOT,read,sha,write
from .run import verify_benchmark

def check():
    errors=[]
    verify_benchmark()
    frozen=read(BASE/'pipeline_freeze.json')
    for name,digest in frozen['files_sha256'].items():
        if sha(ROOT/name)!=digest:errors.append('Changed frozen file: '+name)
    folder=BASE/'results/test_guarded'
    config=read(folder/'run.json')
    if config['config']!=frozen['config']:errors.append('Test config differs from selected pipeline')
    gold=read(BASE/'benchmarks/test.gold.json');inputs=read(BASE/'benchmarks/test.inputs.json')
    if Counter(q['primary_group'] for q in gold)!=Counter(table=6,diagram=5,chart=5,multi_hop=4,text=4,unanswerable=6):
        errors.append('Test group minima/counts differ')
    if [q['id'] for q in gold]!=config['input_ids']:errors.append('Incomplete test input coverage')
    if any(set(q)!={'id','question'} for q in inputs):errors.append('Gold fields in predictor inputs')
    labels=read(folder/'reviews.json')['reviews'];byid={r['id']:r for r in labels}
    if len(labels)!=30 or len(byid)!=30:errors.append('Need all 30 reviews')
    for q in gold:
        path=folder/f"{q['id']}.json";t=read(path);r=byid[q['id']]
        if sha(path)!=r['trace_sha256']:errors.append('Stale label: '+q['id'])
        cs=[c for claim in t['claims'] for c in claim['citations']]
        if len(cs)!=len(r['citations']) or not r['reason']:errors.append('Incomplete citation review: '+q['id'])
        if t['status']=='error' and r['passed']:errors.append('System error marked as pass')
        for c in cs:
            if int(c['source_id'].rsplit('p',1)[1]) not in t['viewed_pages']:errors.append('Unviewed citation: '+q['id'])
    metrics=read(folder/'graded_summary.json')
    if metrics['N']!=30 or metrics['n']!=sum(r['passed'] for r in labels):errors.append('Score denominator mismatch')
    coverage=read(BASE/'coverage_check.json')
    if coverage['rendered_pages']!=297 or coverage['render_errors']:errors.append('Incomplete all-page render check')
    if read(BASE/'source.json')['coverage']['indexed_pages']!=297:errors.append('Incomplete page index')
    receipt=BASE/'evaluation_receipt.json'
    if receipt.exists():
        for name,digest in read(receipt)['files_sha256'].items():
            if sha(ROOT/name)!=digest:errors.append('Receipt mismatch: '+name)
    return {'technical_evidence_checks_passed':not errors,'errors':errors,'test':{'n':metrics['n'],'N':30,'errors':metrics['errors']},
        'numeric_bonus_threshold_met':10*metrics['n']>=9*30,
        'bonus_status':'Not eligible: below 90%; no partial bonus claimed',
        'scope':'Evidence completeness and integrity check; does not award rubric points or certify independent external review.'}

if __name__=='__main__':
    result=check();write(BASE/'submission_check.json',result);print(result)
    if result['errors']:raise SystemExit(1)
