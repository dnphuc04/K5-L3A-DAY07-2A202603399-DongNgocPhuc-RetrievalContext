"""V2 runner: frozen question-only inputs, immutable historical evidence, no test overrides."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import os
from pathlib import Path
from dotenv import dotenv_values
from .common import BASE,ROOT,read,write,sha,verify_benchmark
from .pipeline import PageStore,run

CODE=['advanced_v2/pipeline.py','advanced_v2/common.py','advanced_v2/run.py',
      'advanced/pipeline.py','advanced/common.py','advanced/ingest.py','src/retrieval.py']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--split',choices=['dev','test'],required=True)
    p.add_argument('--config',choices=['extractive','reasoned'])
    p.add_argument('--env-file',type=Path)
    p.add_argument('--ids',nargs='+',help='Dev smoke subset only')
    p.add_argument('--workers',type=int,choices=[1,2],default=2)
    p.add_argument('--output-root',type=Path,help='Optional fresh replay folder under data/local/advanced_v2')
    a=p.parse_args();verify_benchmark()
    if a.split=='test':
        if a.ids or a.config:p.error('Test forbids subset/config overrides')
        lock=read(BASE/'pipeline_freeze.json')
        for n,h in lock['files_sha256'].items():
            if sha(ROOT/n)!=h:raise ValueError('Changed frozen file: '+n)
        config=lock['config']
    else:
        if not a.config:p.error('Dev needs config')
        config=read(BASE/f'configs/{a.config}.json')
    inputs=read(BASE/f'benchmarks/{a.split}.inputs.json')
    if any(set(q)!={'id','question'} for q in inputs):raise ValueError('Input fields must be id/question only')
    if a.ids:
        if set(a.ids)-{q['id'] for q in inputs}:raise ValueError('Unknown dev IDs')
        inputs=[q for q in inputs if q['id'] in a.ids]
    output_root=BASE/'results'
    if a.output_root:
        output_root=a.output_root.resolve()
        if not output_root.is_relative_to((ROOT/'data/local/advanced_v2').resolve()):raise ValueError('Replay must remain local')
    output=output_root/f"{a.split}_{config['name']}{'_smoke' if a.ids else ''}"
    if output.exists():raise ValueError('Never overwrite a reported run; use a fresh local replay root')
    env=dotenv_values(a.env_file) if a.env_file else {}
    key=os.environ.get('OPENAI_API_KEY') or env.get('OPENAI_API_KEY')
    if not key:raise ValueError('OPENAI_API_KEY missing')
    store=PageStore();output.mkdir(parents=True)
    start=datetime.now(timezone.utc)
    write(output/'run.json',{'split':a.split,'config':config,'started_at':start.isoformat(),
        'workers':a.workers,'input_ids':[q['id'] for q in inputs],'benchmark_freeze_sha256':sha(BASE/'benchmarks/freeze.json'),
        'pipeline_freeze_sha256':sha(BASE/'pipeline_freeze.json') if a.split=='test' else None,
        'code_sha256':{n:sha(ROOT/n) for n in CODE},'gold_sent':False,
        'protocol_policy':'No HTTP retries. At most one agent format repair plus at most one verifier format repair per verification; raw responses and all usage recorded.',
        'endpoint':'https://api.openai.com/v1/chat/completions'})
    write(output/'code_snapshot.json',{n:(ROOT/n).read_text(encoding='utf8') for n in CODE})
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        jobs={pool.submit(run,q['question'],key,store,config):q['id'] for q in inputs}
        for job in as_completed(jobs):
            result={'id':jobs[job],'split':a.split,**job.result()};write(output/f"{result['id']}.json",result)
            print(result['id'],result['status'],result.get('error',''),flush=True)
    rows=[read(output/f"{q['id']}.json") for q in inputs]
    end=datetime.now(timezone.utc)
    write(output/'operational_summary.json',{'N':len(rows),'finished_at':end.isoformat(),'wall_seconds':(end-start).total_seconds(),
        'latency_ms_sum':sum(t['elapsed_ms'] for t in rows),
        'statuses':{s:sum(t['status']==s for t in rows) for s in ['answered','abstain','error']},
        'usage':{k:sum(c['usage'].get(k,0) for t in rows for c in t['calls']) for k in ['prompt_tokens','completion_tokens','total_tokens']}})
    verify_benchmark()

if __name__=='__main__':main()
