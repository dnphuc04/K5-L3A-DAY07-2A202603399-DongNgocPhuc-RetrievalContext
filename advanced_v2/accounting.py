"""Exact decimal per-question estimates from saved usage; never calls a provider."""
from decimal import Decimal
from .common import BASE,read,write,sha

def main():
    estimates=read(BASE/'cost_estimate.json');out={};seen=set()
    for folder in sorted((BASE/'results').glob('*_*')):
        meta=read(folder/'run.json');rates=estimates['rates_usd_per_million']['gpt-5.2' if 'gpt-5.2' in meta['config']['model'] else 'gpt-4.1']
        rows=[];total=Decimal(0)
        for qid in meta['input_ids']:
            path=folder/f'{qid}.json';t=read(path);prompt=cached=completion=reasoning=0
            for c in t['calls']:
                rid=c.get('response_id')
                if rid and rid in seen:raise ValueError('Duplicate recorded response ID; do not double count')
                if rid:seen.add(rid)
                u=c['usage'];prompt+=u.get('prompt_tokens',0);completion+=u.get('completion_tokens',0)
                cached+=u.get('prompt_tokens_details',{}).get('cached_tokens',0)
                reasoning+=u.get('completion_tokens_details',{}).get('reasoning_tokens',0)
            cost=((prompt-cached)*Decimal(str(rates['input']))+cached*Decimal(str(rates['cached_input']))+
                  completion*Decimal(str(rates['output'])))/Decimal(1000000)
            total+=cost
            rows.append({'id':qid,'trace_sha256':sha(path),'status':t['status'],'error':t.get('error'),
                'elapsed_ms':t['elapsed_ms'],'calls':len(t['calls']),'prompt_tokens':prompt,'cached_prompt_tokens':cached,
                'completion_tokens':completion,'reasoning_tokens_in_completion':reasoning,'estimated_usd':float(cost)})
        if abs(total-Decimal(str(estimates['runs'][folder.name]['estimated_usd'])))>Decimal('0.000000001'):
            raise ValueError('Per-question and run estimate differ')
        out[folder.name]={'estimated_usd':float(total),'questions':rows}
    write(BASE/'per_question_costs.json',{'type':'estimate_not_invoice','currency':'USD',
        'price_reference':'cost_estimate.json','method':'Exact decimal token accounting; reasoning included in completion; every saved call counted once, including errors and smoke. No provider call.',
        'runs':out})
    print('Per-question time/cost/error records:',sum(len(r['questions']) for r in out.values()),'; run totals matched.')

if __name__=='__main__':main()
