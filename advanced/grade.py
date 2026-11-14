"""Aggregate explicit source-based labels. No LLM judge, no answer keyword scoring."""
import argparse
from collections import Counter
from .common import BASE, read, sha, write

def summarize(run_name):
    folder=BASE/'results'/run_name
    split=run_name.split('_',1)[0]
    gold=read(BASE/f'benchmarks/{split}.gold.json')
    reviews=read(folder/'reviews.json')
    labels={r['id']:r for r in reviews['reviews']}
    if len(labels)!=len(gold) or set(labels)!={q['id'] for q in gold}:
        raise ValueError('Every frozen question requires one explicit review')
    groups={};traces=[]
    for q in gold:
        path=folder/f"{q['id']}.json";t=read(path);r=labels[q['id']];traces.append(t)
        if r['trace_sha256']!=sha(path) or not r['reason']:
            raise ValueError('Missing/stale review')
        if t['status']=='error' and r['passed']:
            raise ValueError('System errors must fail')
        citations=[c for claim in t['claims'] for c in claim['citations']]
        if len(r['citations'])!=len(citations):raise ValueError('Review every citation')
        if any(not c['reason'] for c in r['citations']):raise ValueError('Citation reason missing')
        if q['answerable'] and r['passed'] and (not r['answer_correct_complete'] or not citations or not all(c['supported'] for c in r['citations'])):
            raise ValueError('Passing answer needs all citation and answer checks')
        g=groups.setdefault(q['primary_group'],{'n':0,'N':0})
        g['N']+=1;g['n']+=int(r['passed'])
    n=sum(r['passed'] for r in labels.values());N=len(gold)
    usage={k:sum(c['usage'].get(k,0) for t in traces for c in t['calls']) for k in ('prompt_tokens','completion_tokens','total_tokens')}
    out={'split':split,'run':run_name,'n':n,'N':N,'rate':n/N,'groups':groups,
         'errors':sum(t['status']=='error' for t in traces),'elapsed_ms_sum':sum(t['elapsed_ms'] for t in traces),
         'usage':usage,'meets_numeric_90_percent':10*n>=9*N,
         'cost_usd':None,'cost_note':'Usage recorded, billed USD not verified. See cost estimate separately.',
         'review_method':reviews['method'],'reviews_sha256':sha(folder/'reviews.json')}
    write(folder/'graded_summary.json',out)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');args=p.parse_args();print(summarize(args.run))
