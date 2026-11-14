"""Rebuild local NASA assets without rewriting historical manifests or freezes."""
import argparse
import hashlib
import subprocess
import sys
from .common import ROOT,LOCAL,PDF,read,sha,check_pdf,verify_legacy

def main():
    p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');a=p.parse_args();verify_legacy()
    index=LOCAL/'index.json';expected=read(ROOT/'advanced/source.json')['index_sha256']
    if PDF.exists() and index.exists() and sha(index)==expected:
        check_pdf();print('Exact source and index already verified; no files changed.');return
    cmd=[sys.executable,'-m','advanced.ingest']+(['--download'] if a.download else [])
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=240)
    check_pdf()
    if not index.exists():raise ValueError('No index produced; pin dependencies and check local NASA download')
    if sha(index)!=expected:
        # The recorded index was written on Windows. Accept newline conversion
        # ONLY if the resulting exact bytes match the original recorded hash.
        candidate=index.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
        if hashlib.sha256(candidate).hexdigest()!=expected:
            raise ValueError('Extraction differs semantically or in serialization; do not rebaseline. Use pinned dependencies in a fresh venv without fontTools.')
        temp=index.with_suffix('.json.tmp');temp.write_bytes(candidate);temp.replace(index)
    verify_legacy()
    print('Original PDF and rebuilt local index match exact historical hashes; manifests unchanged.')

if __name__=='__main__':main()
