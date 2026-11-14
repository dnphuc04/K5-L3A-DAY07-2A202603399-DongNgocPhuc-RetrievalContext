"""Select solely from fully reviewed dev results and freeze before test."""
from datetime import datetime, timezone
from .common import BASE, ROOT, read, sha, write
from .run import CODE, verify_benchmark

def main():
    target=BASE/'pipeline_freeze.json'
    if target.exists() or any((BASE/'results').glob('test_*')):
        raise ValueError('Already frozen or test exists; selection cannot be rewritten')
    verify_benchmark()
    names=['compact','wide','locator','precise','checked','guarded']
    candidates=[read(BASE/f'results/dev_{n}/graded_summary.json') for n in names]
    # Fixed priority: full binary quality, fewer errors, lower total observed latency.
    winner=max(candidates,key=lambda c:(c['rate'],-c['errors'],-c['elapsed_ms_sum']))
    name=winner['run'].split('_',1)[1]
    config=read(BASE/f'configs/{name}.json')
    files=CODE+['advanced/source.json','advanced/benchmarks/freeze.json',f'advanced/configs/{name}.json',
                'advanced/select.py','advanced/grade.py']
    for n in names:
        folder=BASE/f'results/dev_{n}'
        files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in folder.glob('*.json'))
    write(BASE/'dev_comparison.json',{'split':'dev','candidates':candidates,'selected':name,
        'policy':'Highest binary pass rate, then fewer system errors, then lower observed latency. Integration failures retained. Test not run or used for selection.'})
    files.append('advanced/dev_comparison.json')
    write(target,{'frozen_at':datetime.now(timezone.utc).isoformat(),'stage':'Before any advanced test run',
        'config':config,'selected_dev_result':winner['run'],'files_sha256':{n:sha(ROOT/n) for n in files}})
    print('Selected and frozen:',name)

if __name__=='__main__':main()
