"""Evaluate the frozen Dense baseline and selected pipeline on all test inputs.

No gold is loaded. No model/retrieval/config override is offered for test tuning.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.agent import run_agent
from src.model import OpenAIChatModel
from src.runtime import load_runtime
from scripts.run_agent_dev import write


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freezes(root=ROOT):
    pipeline = load(root / "configs/pipeline_freeze.json")
    benchmark = load(root / "benchmarks/freeze.json")
    for records in (pipeline["sha256"], benchmark["files_sha256"]):
        for name, expected in records.items():
            if sha(root / name) != expected:
                raise ValueError("Frozen file changed: " + name)
    return {"pipeline_freeze_sha256": sha(root / "configs/pipeline_freeze.json"),
            "benchmark_freeze_sha256": sha(root / "benchmarks/freeze.json"), "status": "passed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day6-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("Choose an unused output directory; never overwrite test results")
    integrity = verify_freezes()
    selected = load(ROOT / "configs/selected_pipeline.json")
    baseline = selected["baseline_for_future_test"]
    inputs = load(ROOT / "benchmarks/test.inputs.json")
    if len(inputs) != 7 or len({q["id"] for q in inputs}) != 7 or any(set(q) - {"id", "question", "filter"} for q in inputs):
        raise ValueError("Invalid frozen test inputs")
    key, embedder, retrievers = load_runtime(args.day6_root, ROOT)
    configs = {baseline["method"]: {**baseline, "role": "baseline"}, selected["method"]: {**selected, "role": "selected"}}
    output.mkdir(parents=True)
    write(output / "config.json", {"started_at": datetime.now(timezone.utc).isoformat(), "split": "test",
        "freeze_verification_before": integrity, "configs": configs, "query_ids": [q["id"] for q in inputs],
        "runner_sha256": sha(Path(__file__)), "test_inputs_sha256": sha(ROOT / "benchmarks/test.inputs.json"),
        "policy": "All seven test inputs, fixed Dense/BM25 configurations, no tuning or cherry-picking; errors retained."})
    traces = []
    for method, cfg in configs.items():
        model = OpenAIChatModel(key, model=cfg["model"], require_quotes=cfg["require_quotes"])
        for q in inputs:
            before = {k: getattr(embedder, k) for k in ("api_requests", "prompt_tokens", "cache_hits")}
            trace = {"query_id": q["id"], "split": "test", "method": method, "role": cfg["role"],
                "question": q["question"], "filter": q.get("filter"),
                **run_agent(q["question"], model, retrievers[method], filters=q.get("filter"),
                    max_searches=cfg["max_searches"], top_k=cfg["top_k"],
                    budget=cfg["context_budget_chars"], require_quotes=cfg["require_quotes"])}
            trace["embedding_usage"] = {k: getattr(embedder, k) - before[k] for k in before}
            traces.append(trace)
            write(output / "traces.json", traces)
            print(json.dumps({"method": method, "id": q["id"], "status": trace["status"], "searches": trace["search_count"]}), flush=True)
    summary = {"split": "test", "methods": {}, "freeze_verification_after": verify_freezes(),
               "cost_usd": None, "cost_note": "Actual API token usage recorded; monetary cost unverified.",
               "quality_note": "Operational only; semantic answer/context/citation/abstention reviews are separate."}
    for method in configs:
        rows = [t for t in traces if t["method"] == method]
        calls = [c for t in rows for c in t["model_calls"]]
        summary["methods"][method] = {"attempted": len(rows), "statuses": dict(Counter(t["status"] for t in rows)),
            "model_calls": len(calls), "median_ms": statistics.median(t["elapsed_ms"] for t in rows),
            "search_count_distribution": dict(Counter(t["search_count"] for t in rows)),
            "usage": {k: sum(c["usage"].get(k, 0) for c in calls) for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
            "embedding_usage": {k: sum(t["embedding_usage"][k] for t in rows) for k in ("api_requests", "prompt_tokens", "cache_hits")}}
    write(output / "summary.json", summary)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__": main()
