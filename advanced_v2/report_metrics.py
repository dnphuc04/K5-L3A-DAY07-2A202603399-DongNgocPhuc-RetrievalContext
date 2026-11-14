"""Offline accounting and page-coverage checks, separate from predictor and labels."""
import statistics
from .common import BASE,ROOT,read,write,sha

def main():
    costs={};contexts={}
    for folder in sorted((BASE/'results').glob('*_*')):
        meta=read(folder/'run.json');rows=[read(folder/f'{qid}.json') for qid in meta['input_ids']]
        calls=[c for t in rows for c in t['calls']]
        prompt=sum(c['usage'].get('prompt_tokens',0) for c in calls)
        cached=sum(c['usage'].get('prompt_tokens_details',{}).get('cached_tokens',0) for c in calls)
        output=sum(c['usage'].get('completion_tokens',0) for c in calls)
        reasoning=sum(c['usage'].get('completion_tokens_details',{}).get('reasoning_tokens',0) for c in calls)
        rate=(1.75,.175,14) if 'gpt-5.2' in meta['config']['model'] else (2,.5,8)
        costs[folder.name]={'model':meta['config']['model'],'cases':len(rows),'calls':len(calls),
            'prompt_tokens':prompt,'cached_prompt_tokens':cached,'completion_tokens':output,'reasoning_tokens_in_completion':reasoning,
            'estimated_usd':round(((prompt-cached)*rate[0]+cached*rate[1]+output*rate[2])/1e6,9),
            'median_query_ms':statistics.median(t['elapsed_ms'] for t in rows),
            'latency_ms_sum':sum(t['elapsed_ms'] for t in rows),
            'wall_seconds':read(folder/'operational_summary.json')['wall_seconds'],
            'format_repairs':sum(e['tool']=='format_repair' for t in rows for e in t['events']),
            'zoom_calls':sum(e['tool']=='view_region' for t in rows for e in t['events'])}
        gold={q['id']:q for q in read(BASE/f"benchmarks/{meta['split']}.gold.json")};checks=[]
        for t in rows:
            q=gold[t['id']];expected={e['page'] for e in q['evidence'] if 'page' in e}
            retrieved={r['page'] for e in t['events'] if e['tool']=='search' for r in e['results']}
            checks.append({'id':t['id'],'trace_sha256':sha(folder/f"{t['id']}.json"),
                'expected_pages':sorted(expected),'retrieved_pages':sorted(retrieved),'viewed_pages':t['viewed_pages'],
                'gold_pages_retrieved':expected<=retrieved if q['answerable'] else None,
                'gold_original_pages_viewed':expected<=set(t['viewed_pages']) if q['answerable'] else None,
                'note':'Page-coverage proxy only, not semantic context/citation correctness. Read reviews for completeness and entailment; absence uses separate full-corpus review.'})
        contexts[folder.name]=checks
    write(BASE/'cost_estimate.json',{'type':'estimate_not_invoice','checked_on':'2026-11-14',
        'rates_usd_per_million':{'gpt-4.1':{'input':2,'cached_input':.5,'output':8},'gpt-5.2':{'input':1.75,'cached_input':.175,'output':14}},
        'sources':['https://developers.openai.com/api/docs/models/gpt-4.1','https://developers.openai.com/api/docs/models/gpt-5.2'],
        'assumptions':'Standard synchronous rates; image input and reasoning output included in reported token usage. Malformed successful responses and smoke included. No invoice/tax/compute/storage reconciliation. Historical v1 baseline reused without new calls, not charged again.',
        'runs':costs,'total_estimated_usd':round(sum(c['estimated_usd'] for c in costs.values()),9)})
    write(BASE/'context_checks.json',contexts)
    print('Total estimate USD',round(sum(c['estimated_usd'] for c in costs.values()),6))
    print('Test:',costs['test_reasoned'])
    print('Expected answerable source pages viewed:',sum(r['gold_original_pages_viewed'] is True for r in contexts['test_reasoned']),'/24')

if __name__=='__main__':main()
