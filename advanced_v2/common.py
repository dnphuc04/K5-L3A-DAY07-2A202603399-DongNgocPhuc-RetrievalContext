from pathlib import Path
from advanced.common import ROOT, LOCAL, PDF, SOURCE_SHA, read, write, sha, check_pdf
BASE=Path(__file__).resolve().parent

def verify_legacy():
    frozen=read(BASE/'legacy_snapshot.json')
    for name,digest in frozen['files_sha256'].items():
        if sha(ROOT/name)!=digest:
            raise ValueError('Historical advanced evidence changed: '+name)

def verify_benchmark():
    verify_legacy()
    for name,digest in read(BASE/'benchmarks/freeze.json')['files_sha256'].items():
        if sha(BASE/name)!=digest:raise ValueError('V2 benchmark changed: '+name)
