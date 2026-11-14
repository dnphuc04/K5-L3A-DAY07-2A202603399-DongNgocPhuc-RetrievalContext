"""Run real tool-calling agent on dev only; never load gold into the runner."""
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


def write(path, obj):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day6-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="gpt-4.1-mini-2025-04-14")
    parser.add_argument("--methods", nargs="+", choices=["dense", "bm25", "hybrid_rrf"], default=["dense", "bm25", "hybrid_rrf"])
    parser.add_argument("--ids", nargs="+", help="Optional dev smoke subset; cannot select test IDs")
    parser.add_argument("--max-searches", type=int, default=2)
    parser.add_argument("--budget", type=int, default=4000)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--require-quotes", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("Choose an unused output directory")
    if args.max_searches < 1 or args.budget < 1 or args.top_k < 1:
        parser.error("Limits must be positive")
    inputs = json.loads((ROOT / "benchmarks/dev.inputs.json").read_text(encoding="utf-8"))
    if args.ids:
        if set(args.ids) - {q["id"] for q in inputs}:
            parser.error("Only existing dev IDs allowed")
        inputs = [q for q in inputs if q["id"] in args.ids]
    if any(set(q) - {"id", "question", "filter"} for q in inputs):
        raise ValueError("Unexpected input fields")
    key, embedder, retrievers = load_runtime(args.day6_root, ROOT)
    model = OpenAIChatModel(key, model=args.model, require_quotes=args.require_quotes)
    output.mkdir(parents=True)
    config = {"started_at": datetime.now(timezone.utc).isoformat(), "split": "dev", "model": args.model,
        "methods": args.methods, "query_ids": [q["id"] for q in inputs], "top_k": args.top_k,
        "require_quotes": args.require_quotes, "max_completion_tokens": model.max_completion_tokens,
        "max_searches": args.max_searches, "context_budget_chars": args.budget,
        "context_policy": "cumulative first-seen whole chunks; source headers included; dedup; skip oversized blocks",
        "first_search_query": "original question enforced", "later_queries": "model chosen, logged separately",
        "source_sha256": json.loads((ROOT / "benchmarks/freeze.json").read_text(encoding="utf-8"))["source_sha256"],
        "code_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (
            "src/agent.py", "src/model.py", "src/runtime.py", "src/retrieval.py", "src/day6_adapter.py", "scripts/run_agent_dev.py")}}
    write(output / "config.json", config)
    traces = []
    for method in args.methods:
        for q in inputs:
            before = {k: getattr(embedder, k) for k in ("api_requests", "prompt_tokens", "cache_hits")}
            trace = {"query_id": q["id"], "split": "dev", "method": method, "question": q["question"], "filter": q.get("filter"),
                **run_agent(q["question"], model, retrievers[method], filters=q.get("filter"),
                            max_searches=args.max_searches, budget=args.budget, top_k=args.top_k, require_quotes=args.require_quotes)}
            trace["embedding_usage"] = {k: getattr(embedder, k) - before[k] for k in before}
            traces.append(trace)
            write(output / "traces.json", traces)
            print(json.dumps({"method": method, "id": q["id"], "status": trace["status"], "searches": trace["search_count"]}), flush=True)
            # Fail fast for provider connection/auth/model errors to avoid 51 identical failures.
            if trace["status"] == "error" and trace["events"][-2].get("error_type") == "ModelError":
                print(json.dumps(trace["events"][-2]), flush=True)
                raise SystemExit("Provider failure recorded; resolve before continuing, no mock fallback")
    summary = {"split": "dev", "queries_per_method": len(inputs), "methods": {},
        "cost_usd": None, "cost_note": "Actual token usage reported; monetary cost not yet verified against billing.",
        "quality_note": "Operational summary only; semantic answer/citation/abstention labels require separate review."}
    for method in args.methods:
        rows = [t for t in traces if t["method"] == method]
        calls = [c for t in rows for c in t["model_calls"]]
        summary["methods"][method] = {"attempted": len(rows), "statuses": dict(Counter(t["status"] for t in rows)),
            "tool_use": {"n": sum(t["search_count"] > 0 for t in rows if t["status"] != "error"), "N": sum(t["status"] != "error" for t in rows)},
            "search_count_distribution": dict(Counter(t["search_count"] for t in rows)), "model_calls": len(calls),
            "median_ms": statistics.median(t["elapsed_ms"] for t in rows),
            "usage": {k: sum(c["usage"].get(k, 0) for c in calls) for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
            "embedding_usage": {k: sum(t["embedding_usage"][k] for t in rows) for k in ("api_requests", "prompt_tokens", "cache_hits")},
            "answers_with_citation": sum(t["status"] == "answered" and bool(t["citations"]) for t in rows)}
    write(output / "summary.json", summary)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__": main()
