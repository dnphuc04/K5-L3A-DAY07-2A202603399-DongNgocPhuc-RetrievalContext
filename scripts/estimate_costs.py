"""Offline price estimate from recorded usage; never substitutes for billing."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def estimate():
    runs = ["agent_dev_v1", "agent_dev_dense_wide", "agent_dev_dense_wide_quotes", "agent_test_v1",
            "agent_smoke_v1", "agent_smoke_v2", "agent_smoke_v3", "agent_smoke_v4"]
    result = {"type": "estimate_not_invoice", "price_checked_on": "2026-11-14",
        "usd_per_million_tokens": {"chat_input": 0.40, "chat_cached_input": 0.10, "chat_output": 1.60, "embedding_input": 0.02},
        "sources": ["https://developers.openai.com/api/docs/models/gpt-4.1-mini", "https://developers.openai.com/api/docs/models/text-embedding-3-small"],
        "assumptions": "Standard synchronous API prices, no tax/credits/discounts. Only recorded successful usage; excludes Day 6 document embedding and previous cached vectors, compute/storage/network costs. Failed calls without usage have unknown billing.",
        "runs": {}, "source_sha256": {}}
    response_ids = set()
    for name in runs:
        path = ROOT / "results" / name / "traces.json"
        rows = json.loads(path.read_text(encoding="utf-8"))
        result["source_sha256"][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        methods = {}
        for method in sorted({r["method"] for r in rows}):
            selected = [r for r in rows if r["method"] == method]
            calls = [c for r in selected for c in r["model_calls"]]
            for call in calls:
                rid = call.get("response_id")
                if rid and rid in response_ids:
                    raise ValueError("Duplicate recorded response; review cost attribution")
                if rid: response_ids.add(rid)
            prompt = sum(c["usage"].get("prompt_tokens", 0) for c in calls)
            cached = sum(c["usage"].get("prompt_tokens_details", {}).get("cached_tokens", 0) for c in calls)
            output = sum(c["usage"].get("completion_tokens", 0) for c in calls)
            emb = sum(r["embedding_usage"]["prompt_tokens"] for r in selected)
            usd = ((prompt - cached) * .40 + cached * .10 + output * 1.60 + emb * .02) / 1_000_000
            methods[method] = {"calls": len(calls), "prompt_tokens": prompt, "cached_prompt_tokens": cached,
                               "completion_tokens": output, "new_embedding_tokens": emb, "estimated_usd": round(usd, 9)}
        result["runs"][name] = methods
    # This incomplete retrieval run paid for the two new dev embeddings; do not lose it.
    partial = ROOT / "results/retrieval_dev_v2/retrieval.traces.json"
    rows = json.loads(partial.read_text(encoding="utf-8"))
    emb = sum(r["embedding_usage"]["prompt_tokens"] for r in rows)
    result["retrieval_preparation"] = {"run": "retrieval_dev_v2", "new_embedding_tokens": emb,
                                        "estimated_usd": round(emb * .02 / 1_000_000, 9), "status": "partial_run_usage_recorded"}
    result["source_sha256"][str(partial.relative_to(ROOT))] = hashlib.sha256(partial.read_bytes()).hexdigest()
    result["total_estimated_usd"] = round(sum(m["estimated_usd"] for run in result["runs"].values() for m in run.values()) + result["retrieval_preparation"]["estimated_usd"], 9)
    return result


if __name__ == "__main__":
    result = estimate()
    (ROOT / "artifacts/cost_estimate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total_estimated_usd": result["total_estimated_usd"], "main_runs": {k:v for k,v in result["runs"].items() if "smoke" not in k}}))
