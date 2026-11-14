"""Offline review packets and aggregation of explicit source-based binary labels."""
from collections import Counter
import argparse
from .common import BASE,read,write,sha

def packet(name):
    folder=BASE/'results'/name;config=read(folder/'run.json');split=config['split']
    gold={q['id']:q for q in read(BASE/f'benchmarks/{split}.gold.json')}
    rows=[]
    for qid in config['input_ids']:
        path=folder/f'{qid}.json';t=read(path)
        rows.append({'id':qid,'trace_sha256':sha(path),'question':t['question'],'status':t['status'],
            'claims':t['claims'],'error':t.get('error'),'gold':gold[qid],
            'viewed_pages':t['viewed_pages'],'source_events':[e for e in t['events'] if e['tool'] in ('view_pages','view_region','source_verification')]})
    write(folder/'review_packet.json',rows)

def summarize(name):
    folder=BASE/'results'/name;run=read(folder/'run.json');split=run['split']
    gold={q['id']:q for q in read(BASE/f'benchmarks/{split}.gold.json')}
    reviews=read(folder/'reviews.json');labels={r['id']:r for r in reviews['reviews']}
    if set(labels)!=set(run['input_ids']) or len(labels)!=len(reviews['reviews']):raise ValueError('Complete unique review set required')
    if len(run['input_ids'])!=30:raise ValueError('Reported evaluation requires all 30 cases')
    groups={};rows=[]
    for qid in run['input_ids']:
        path=folder/f'{qid}.json';t=read(path);r=labels[qid];q=gold[qid];rows.append(t)
        cs=[c for claim in t['claims'] for c in claim['citations']]
        if sha(path)!=r['trace_sha256'] or not r['reason'] or len(cs)!=len(r['citations']):raise ValueError('Stale/incomplete source review')
        if t['status']=='error' and r['passed']:raise ValueError('System error cannot pass')
        if q['answerable'] and r['passed'] and (not r['answer_correct_complete'] or not cs or not all(c['supported'] for c in r['citations'])):
            raise ValueError('Pass requires complete answer and all supporting citations')
        if any(not c['reason'] for c in r['citations']):raise ValueError('Citation reason missing')
        g=groups.setdefault(q['primary_group'],{'n':0,'N':0});g['N']+=1;g['n']+=int(r['passed'])
    n=sum(r['passed'] for r in labels.values());N=len(rows)
    result={'run':name,'split':split,'n':n,'N':N,'rate':n/N,'groups':groups,'errors':sum(t['status']=='error' for t in rows),
        'model_calls':sum(len(t['calls']) for t in rows),'latency_ms_sum':sum(t['elapsed_ms'] for t in rows),
        'meets_90_percent':10*n>=9*N,'reviews_sha256':sha(folder/'reviews.json'),
        'method':reviews['method'],'operational_summary':read(folder/'operational_summary.json')}
    write(folder/'graded_summary.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--prepare',action='store_true');a=p.parse_args()
    if a.prepare:packet(a.name)
    else:print(summarize(a.name))
