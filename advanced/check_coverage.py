"""Verify render access for every indexed page, independent of benchmark pages."""
from .common import BASE, LOCAL, PDF, read, sha, write
from .ingest import render

def main():
    rows=[];errors=[]
    for page in range(1,read(BASE/'source.json')['pdf_pages']+1):
        try:
            path=render(page,1800)
            rows.append({'page':page,'path':str(path.relative_to(BASE.parent)).replace('\\','/'),'sha256':sha(path),'bytes':path.stat().st_size})
        except Exception as exc:
            errors.append({'page':page,'error_type':type(exc).__name__})
        if page%25==0:print('Render verified through page',page,flush=True)
    write(LOCAL/'coverage_replay.json',{'source_sha256':sha(PDF),'indexed_pages':297,
        'rendered_pages':len(rows),'render_errors':errors,'pages':rows,
        'scope':'All pages, including pages outside benchmark. Rendering success proves image availability, not semantic extraction accuracy; native warnings remain in source.json.'})
    print('Rendered',len(rows),'pages; errors',len(errors),flush=True)

if __name__=='__main__':main()
