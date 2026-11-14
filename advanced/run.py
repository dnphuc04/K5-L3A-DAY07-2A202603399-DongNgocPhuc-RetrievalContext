"""Run only frozen input questions; no gold import, no automatic retry of test."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import os
from pathlib import Path
from dotenv import dotenv_values
from .common import BASE, ROOT, read, sha, write
from .pipeline import PageStore, run

CODE = ["advanced/pipeline.py", "advanced/ingest.py", "advanced/common.py", "advanced/run.py", "src/retrieval.py"]

def verify_benchmark():
    frozen = read(BASE / "benchmarks/freeze.json")
    for name, digest in frozen["files_sha256"].items():
        if sha(BASE / name) != digest:
            raise ValueError("Frozen advanced benchmark changed")
    return sha(BASE / "benchmarks/freeze.json")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["dev", "test"], required=True)
    parser.add_argument("--config", choices=["compact", "wide", "locator", "precise", "checked", "guarded"])
    parser.add_argument("--env-file", type=Path, help="Read API key locally; never record path/content in evidence")
    parser.add_argument("--workers", type=int, choices=[1,2], default=2)
    parser.add_argument("--output-root",type=Path,help="Optional fresh local replay root under data/local/advanced; reported results are never overwritten")
    args = parser.parse_args()
    benchmark_sha = verify_benchmark()
    if args.split == "test":
        lock = read(BASE / "pipeline_freeze.json")
        for name,digest in lock["files_sha256"].items():
            if sha(ROOT / name) != digest:
                raise ValueError("Frozen advanced pipeline/dev evidence changed")
        if args.config and args.config != lock["config"]["name"]:
            raise ValueError("Test must use selected config")
        config = lock["config"]
    else:
        if not args.config:
            parser.error("Dev requires --config")
        config = read(BASE / f"configs/{args.config}.json")
    output_root=BASE/'results'
    if args.output_root:
        output_root=args.output_root.resolve()
        if not output_root.is_relative_to((ROOT/'data/local/advanced').resolve()):
            raise ValueError('Replay output must stay under data/local/advanced')
    output = output_root / f"{args.split}_{config['name']}"
    if output.exists():
        raise ValueError("Output already exists; do not overwrite/retry benchmark")
    inputs = read(BASE / f"benchmarks/{args.split}.inputs.json")
    if any(set(q) != {"id","question"} for q in inputs):
        raise ValueError("Only id/question allowed in agent inputs")
    env = dotenv_values(args.env_file) if args.env_file else {}
    key = os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAI_API_KEY")
    store = PageStore()
    output.mkdir(parents=True)
    write(output / "code_snapshot.json", {n:(ROOT/n).read_text(encoding='utf-8') for n in CODE})
    write(output / "run.json", {"split":args.split,"config":config,
        "started_at":datetime.now(timezone.utc).isoformat(), "benchmark_sha256":benchmark_sha,
        "source_manifest_sha256":sha(BASE / "source.json"), "workers":args.workers,
        "code_sha256":{n:sha(ROOT/n) for n in CODE},
        "input_ids":[q["id"] for q in inputs], "privacy":"Public NASA questions, text, requested original page images only; no gold or credentials in payload/traces",
        "endpoint":"https://api.openai.com/v1/chat/completions", "retries":0})
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(run,q["question"],key,store,config):q["id"] for q in inputs}
        for job in as_completed(jobs):
            result = {"id":jobs[job],"split":args.split,**job.result()}
            write(output / f"{result['id']}.json",result)
            print(result["id"],result["status"],result.get("error",{}),flush=True)
    traces = [read(output / f"{q['id']}.json") for q in inputs]
    write(output / "operational_summary.json", {"N":len(traces),
        "finished_at":datetime.now(timezone.utc).isoformat(),
        "statuses":{s:sum(t["status"]==s for t in traces) for s in ("answered","abstain","error")},
        "elapsed_ms_sum":sum(t["elapsed_ms"] for t in traces),
        "usage":{k:sum(c["usage"].get(k,0) for t in traces for c in t["calls"])
                 for k in ("prompt_tokens","completion_tokens","total_tokens")},
        "quality":"Not scored; requires per-question source/citation review, errors remain in denominator"})

if __name__ == "__main__":
    main()
