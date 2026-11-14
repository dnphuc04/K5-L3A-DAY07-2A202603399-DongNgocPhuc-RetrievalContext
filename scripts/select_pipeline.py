"""Compare fully reviewed dev runs and freeze a pipeline before any test run."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from grade_dev import summarize


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selection_key(candidate):
    m = candidate["graded"]
    # Monetary cost is unknown for every run, so cannot break a tie.
    return (m["grounded_answer"]["mean_out_of_2"], m["context_evidence_rate"]["rate"],
            m["citation_validity"]["rate"] if m["citation_validity"]["rate"] is not None else -1,
            m["abstention"]["n"], candidate["retrieval"]["first_original_query_hit3"]["rate"],
            -m["median_ms"], -m["model_calls"], candidate["id"] == "baseline_dense")


def main():
    target = ROOT / "configs/selected_pipeline.json"
    freeze_path = ROOT / "configs/pipeline_freeze.json"
    if target.exists() or freeze_path.exists():
        raise SystemExit("Pipeline freeze exists; do not silently change selected configuration")
    frozen = load(ROOT / "benchmarks/freeze.json")
    for name, expected in frozen["files_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("Benchmark freeze changed")
    candidates = []
    evidence_hashes = {}
    for run_name, method, cid in (("agent_dev_v1", "dense", "baseline_dense"),
                                  ("agent_dev_v1", "bm25", "bm25"),
                                  ("agent_dev_v1", "hybrid_rrf", "hybrid_rrf"),
                                  ("agent_dev_dense_wide", "dense", "dense_wide"),
                                  ("agent_dev_dense_wide_quotes", "dense", "dense_wide_quotes")):
        run = ROOT / "results" / run_name
        cfg = load(run / "config.json")
        graded = summarize(run)["methods"][method]
        rows = [t for t in load(run / "traces.json") if t["method"] == method]
        if len(rows) != 17 or {t["query_id"] for t in rows} != {q["id"] for q in load(ROOT / "benchmarks/dev.inputs.json")}:
            raise ValueError("All candidates must cover the same full dev set")
        if graded["errors"]:
            raise ValueError("Resolve/explain candidate system errors before freezing")
        if cfg["model"] != "gpt-4.1-mini-2025-04-14" or cfg["source_sha256"] != frozen["source_sha256"]:
            raise ValueError("Comparison model/corpus mismatch")
        candidate = {"id": cid, "run": str(run.relative_to(ROOT)), "method": method,
                     "config": cfg, "graded": graded, "retrieval": load(run / "context_checks.json")[method],
                     "operational": load(run / "summary.json")["methods"][method]}
        candidates.append(candidate)
        for name in ("traces.json", "config.json", "reviews.json", "graded_summary.json", "context_checks.json", "summary.json"):
            path = run / name
            evidence_hashes[str(path.relative_to(ROOT))] = digest(path)
    ordered = sorted(candidates, key=selection_key, reverse=True)
    winner = ordered[0]
    report = {"split": "dev", "policy_source": "benchmarks/README.md", "candidates": candidates,
              "ranked_ids": [c["id"] for c in ordered], "selected": winner["id"],
              "review_limit": "Every query/citation compared against the original source with a written reason. No test evaluated.",
              "cost_limit": "Monetary cost unverified; token usage recorded. Single-run latency tie-break is noisy, not a statistical superiority claim."}
    cfg = winner["config"]
    selected = {"id": winner["id"], "model": cfg["model"], "method": winner["method"],
        "top_k": cfg["top_k"], "context_budget_chars": cfg["context_budget_chars"],
        "max_searches": cfg["max_searches"], "require_quotes": cfg.get("require_quotes", False),
        "max_completion_tokens": cfg.get("max_completion_tokens", 1200), "temperature": 0,
        "bm25": {"k1": 1.5, "b": 0.75, "tokenizer": "NFC/casefold/Unicode word tokens, no stopwords, unique query terms"},
        "context_policy": cfg["context_policy"], "embedding_model": "text-embedding-3-small", "dimensions": 1536,
        "strategy": "C", "source_sha256": frozen["source_sha256"], "selected_on": "dev only",
        "baseline_for_future_test": {"method": "dense", "top_k": 3, "context_budget_chars": 4000,
                                     "max_searches": 2, "require_quotes": False, "model": cfg["model"]}}
    def write(path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write(ROOT / "results/dev_comparison.json", report)
    write(target, selected)
    for name in ("configs/selected_pipeline.json", "configs/dev_experiments.json", "results/dev_comparison.json", "benchmarks/freeze.json"):
        evidence_hashes[name] = digest(ROOT / name)
    for name in ("src/model.py", "src/agent.py", "src/retrieval.py", "src/runtime.py", "src/day6_adapter.py", "scripts/run_agent_dev.py", "scripts/inspect_agent_dev.py", "scripts/grade_dev.py", "scripts/select_pipeline.py"):
        evidence_hashes[name] = digest(ROOT / name)
    write(freeze_path, {"frozen_at": datetime.now(timezone.utc).isoformat(), "stage": "Selected after full dev reviews and two improvement experiments; before any Day 7 test evaluation",
                        "selected_id": winner["id"], "sha256": evidence_hashes})
    print(json.dumps({"selected": winner["id"], "ranked": report["ranked_ids"]}))


if __name__ == "__main__": main()
