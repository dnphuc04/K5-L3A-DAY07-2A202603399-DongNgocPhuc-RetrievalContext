"""Run real retrieval on dev only. No test queries loaded, no gold passed to tools."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.day6_adapter import Day6VectorReader, convert_chunk
from src.retrieval import BM25Retriever, DenseRetriever, HybridRetriever, pack_context


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text):
    import unicodedata
    return " ".join(unicodedata.normalize("NFC", text).split())


def hit(chunk, gold):
    return any(chunk["source_id"] == g["source_id"] and chunk["page"] == g["page"]
               and norm(g["evidence"]) in norm(chunk["text"]) for g in gold)


def ratio(n, total):
    return {"n": n, "N": total, "rate": n / total if total else None}


def run(day6, output, budget):
    from dotenv import dotenv_values
    import psycopg
    if output.exists():
        raise ValueError("Output already exists; choose a new run directory")
    frozen = load(ROOT / "benchmarks/freeze.json")
    for name, digest in frozen["files_sha256"].items():
        if sha(ROOT / name) != digest:
            raise ValueError("Frozen benchmark changed")
    chunk_path = day6 / "starter/results/chunks/C.jsonl"
    if sha(chunk_path) != frozen["source_sha256"]["chunks_C"]:
        raise ValueError("Frozen corpus changed")
    ingestion = load(day6 / "starter/results/ingestion.json")
    if (ingestion["model"], ingestion["dimensions"], ingestion["query_prefix"]) != ("text-embedding-3-small", 1536, ""):
        raise ValueError("Embedding contract changed")
    chunks = [convert_chunk(json.loads(s)) for s in chunk_path.read_text(encoding="utf-8").splitlines() if s.strip()]
    env = {**dotenv_values(day6 / "starter/.env")}
    import os
    for key in ("DATABASE_URL", "OPENAI_API_KEY"):
        env[key] = os.environ.get(key) or env.get(key)
    # Verify current DB text/metadata/dimensions, not merely a historic receipt.
    with psycopg.connect(env["DATABASE_URL"], connect_timeout=5) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        dbrows = conn.execute("SELECT chunk_id, document_id, source, page, text, metadata, vector_dims(embedding) FROM lab_chunks WHERE strategy=%s", ("C",)).fetchall()
    keys = ("chunk_id", "document_id", "source", "page", "text", "metadata")
    actual = {r[0]: convert_chunk(dict(zip(keys, r[:6]))) for r in dbrows}
    if actual != {c["id"]: c for c in chunks} or any(r[6] != 1536 for r in dbrows):
        raise ValueError("Database and frozen corpus differ")
    spec = importlib.util.spec_from_file_location("day6_embeddings", day6 / "starter/src/embeddings.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cache = ROOT / "data/local/query_cache"
    cache.mkdir(parents=True, exist_ok=True)
    inputs = load(ROOT / "benchmarks/dev.inputs.json")
    # Reuse only the dev query cache entries; never copy test embeddings or write Day 6.
    for q in inputs:
        key = hashlib.sha256(json.dumps(["text-embedding-3-small", 1536, q["question"]], ensure_ascii=False).encode("utf-8")).hexdigest()
        old = day6 / f"starter/.embedding_cache/{key}.json"
        target = cache / f"{key}.json"
        if old.exists() and not target.exists():
            shutil.copyfile(old, target)
    embedder = module.OpenAIEmbedder(env["OPENAI_API_KEY"], cache_dir=cache)
    dense = DenseRetriever(embedder, Day6VectorReader(env["DATABASE_URL"]))
    start = time.perf_counter()
    lexical = BM25Retriever(chunks)
    index_ms = (time.perf_counter() - start) * 1000
    methods = {"dense": dense, "bm25": lexical, "hybrid_rrf": HybridRetriever(dense, lexical)}
    # Retrieve first; labels are loaded only after all query/tool work is finished.
    traces = []
    output.mkdir(parents=True)
    for method, retriever in methods.items():
        for q in inputs:
            start = time.perf_counter()
            before = {k: getattr(embedder, k) for k in ("api_requests", "prompt_tokens", "cache_hits")}
            row = {"query_id": q["id"], "split": "dev", "method": method,
                   "query": q["question"], "filter": q.get("filter"), "filter_origin": "user scope in frozen question; no inferred filters",
                   "query_transformation": "none", "top_k": 3, "budget_chars": budget}
            try:
                rows = retriever.search(q["question"], filters=q.get("filter"), top_k=3)
                context, ids = pack_context(rows, budget)
                row.update(status="ok", results=rows, context=context, context_ids=ids, context_chars=len(context))
            except Exception as exc:
                row.update(status="error", error_type=type(exc).__name__)
            row["elapsed_ms"] = (time.perf_counter() - start) * 1000
            row["embedding_usage"] = {k: getattr(embedder, k) - before[k] for k in before}
            traces.append(row)
            (output / "retrieval.traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    gold = {q["id"]: q for q in load(ROOT / "benchmarks/dev.gold.json")}
    for t in traces:
        q = gold[t["query_id"]]
        if q["answerable"]:
            rows = t.get("results", [])
            t["evaluation"] = {"hit1": bool(rows and hit(rows[0], q["gold"])),
                "hit3": any(hit(c, q["gold"]) for c in rows),
                "context_hit": any(c["id"] in t.get("context_ids", []) and hit(c, q["gold"]) for c in rows)}
        else:
            t["evaluation"] = {"excluded_from_retrieval_metrics": True, "abstention_evaluated": False}
    summary = {"split": "dev", "corpus": {"strategy": "C", "chunks": len(chunks), "sha256": sha(chunk_path)},
        "config": {"top_k": 3, "context_budget_chars": budget, "context_policy": "whole chunks in rank order, dedup, skip blocks exceeding budget",
                   "bm25": {"k1": 1.5, "b": 0.75, "tokenizer": "NFC/casefold/Unicode word tokens; Vietnamese syllables; no stopword removal; unique query terms"},
                   "hybrid": {"candidate_k_per_method": 20, "rrf_k": 60, "weights": [1, 1]}, "embedding_model": "text-embedding-3-small", "dimensions": 1536},
        "timing_note": "Single sequential run; dense before hybrid, shared query cache. Dense may incur fresh API cost; hybrid may reuse it. Latencies are not a fair cold-cache method comparison.",
        "bm25_index_build_ms": index_ms, "methods": {}, "new_embedding_usage_total": {k: getattr(embedder, k) for k in ("api_requests", "prompt_tokens", "cache_hits")},
        "cost_usd": None, "cost_note": "No fabricated pricing. Query embedding usage shared across methods; consult provider billing. BM25 has no model API calls.",
        "code_sha256": {p: sha(ROOT / p) for p in ("src/retrieval.py", "src/day6_adapter.py", "scripts/benchmark_retrieval_dev.py")},
        "embedding_adapter_sha256": sha(day6 / "starter/src/embeddings.py"), "benchmark_freeze_sha256": sha(ROOT / "benchmarks/freeze.json"),
        "evaluation_note": "Strict normalized full-span matching; no semantic/manual ranking review yet. No agent answers, citations or abstention metrics measured."}
    for method in methods:
        rows = [t for t in traces if t["method"] == method]
        answerable = [t for t in rows if gold[t["query_id"]]["answerable"]]
        summary["methods"][method] = {"attempted": len(rows), "errors": sum(t["status"] == "error" for t in rows),
            "success_coverage": ratio(sum(t["status"] == "ok" for t in rows), len(rows)),
            **{metric: ratio(sum(t["evaluation"][metric] for t in answerable), len(answerable)) for metric in ("hit1", "hit3", "context_hit")},
            "median_ms": statistics.median(t["elapsed_ms"] for t in rows),
            "embedding_usage": {k: sum(t["embedding_usage"][k] for t in rows) for k in ("api_requests", "prompt_tokens", "cache_hits")}}
    (output / "evaluated.traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day6-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--budget", type=int, default=4000)
    args = parser.parse_args()
    if args.budget < 1:
        parser.error("budget must be positive")
    run(args.day6_root, args.output, args.budget)
