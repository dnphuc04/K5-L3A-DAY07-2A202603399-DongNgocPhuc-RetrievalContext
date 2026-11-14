"""Offline cost, latency and context checks; no model calls or pipeline changes."""
from datetime import datetime
import statistics
from .common import BASE,read,sha,write

def main():
    costs={};contexts={}
    for folder in sorted((BASE/'results').glob('*_*')):
        run=read(folder/'run.json');split=run['split']
        rows=[read(folder/f"{qid}.json") for qid in run['input_ids']]
        prompt=cached=completion=0
        for t in rows:
            for c in t['calls']:
                u=c['usage'];prompt+=u.get('prompt_tokens',0);completion+=u.get('completion_tokens',0)
                cached+=u.get('prompt_tokens_details',{}).get('cached_tokens',0)
        rates=(.4,.1,1.6) if 'mini' in run['config']['model'] else (2,.5,8)
        operational=read(folder/'operational_summary.json')
        costs[folder.name]={'model':run['config']['model'],'prompt_tokens':prompt,'cached_prompt_tokens':cached,
            'completion_tokens':completion,'model_calls':sum(len(t['calls']) for t in rows),
            'estimated_usd':round(((prompt-cached)*rates[0]+cached*rates[1]+completion*rates[2])/1e6,9),
            'latency_ms_sum':sum(t['elapsed_ms'] for t in rows),'median_query_ms':statistics.median(t['elapsed_ms'] for t in rows),
            'wall_seconds':(datetime.fromisoformat(operational['finished_at'])-datetime.fromisoformat(run['started_at'])).total_seconds() if operational.get('finished_at') else None}
        gold=read(BASE/f'benchmarks/{split}.gold.json')
        checks=[]
        for q,t in zip(gold,rows):
            retrieved={r['page'] for e in t['events'] if e['tool']=='search' for r in e['results']}
            viewed=set(t['viewed_pages']);expected={e['page'] for e in q['evidence'] if 'page' in e}
            checks.append({'id':q['id'],'trace_sha256':sha(folder/f"{q['id']}.json"),
                'expected_pages':sorted(expected),'retrieved_pages':sorted(retrieved),'viewed_pages':sorted(viewed),
                'expected_pages_retrieved':expected<=retrieved if q['answerable'] else None,
                'expected_original_pages_viewed':expected<=viewed if q['answerable'] else None,
                'reason':('Original-page availability is a page-level coverage check, not a semantic answer/citation label; see reviews.json.' if q['answerable'] else
                          'Related context is insufficient to establish the requested universal mandate; full-corpus absence review is separate. No absence conclusion inferred from page hit alone.')})
        contexts[folder.name]=checks
    write(BASE/'cost_estimate.json',{'type':'estimate_not_invoice','checked_on':'2026-11-14',
        'rates_usd_per_million':{'gpt-4.1-mini':{'input':.4,'cached_input':.1,'output':1.6},'gpt-4.1':{'input':2,'cached_input':.5,'output':8}},
        'sources':['https://developers.openai.com/api/docs/models/gpt-4.1-mini','https://developers.openai.com/api/docs/models/gpt-4.1'],
        'assumptions':'Standard synchronous token rates; image tokens included in recorded prompt usage. Successful response usage includes malformed outputs. No tax, discounts, compute/storage/download costs or invoice reconciliation.',
        'runs':costs,'total_estimated_usd':round(sum(r['estimated_usd'] for r in costs.values()),9)})
    write(BASE/'context_checks.json',contexts)
    print('Estimated total USD',round(sum(r['estimated_usd'] for r in costs.values()),6))
    print('Test:',costs['test_guarded'])

if __name__=='__main__':main()
