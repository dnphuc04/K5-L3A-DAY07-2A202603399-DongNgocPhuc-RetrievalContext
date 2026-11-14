"""Prepare a test review packet or aggregate explicit semantic reviews offline."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "starter"))
sys.path.insert(0, str(ROOT / "scripts"))
from agent_metrics import aggregate
from benchmark_retrieval_dev import hit, ratio


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare(run):
    rows = load(run / "traces.json")
    gold = {q["id"]: q for q in load(ROOT / "benchmarks/test.gold.json")}
    packet = []
    for t in rows:
        chunks = {c["id"]: c for e in t["events"] if e["event"] == "search" for c in e["results"]}
        packet.append({"method": t["method"], "query_id": t["query_id"], "status": t["status"],
            "question": t["question"], "answer": t["answer"], "citations": t["citations"],
            "cited_chunks": [chunks[c] for c in t["citations"]], "context": t["context"], "gold": gold[t["query_id"]],
            "review": {"answer_grade": None, "context_grade": None, "citation_support": [None] * len(t["citations"]),
                       "citation_reasons": [], "abstention_correct": None, "reason": None}})
    return packet


def summarize(run):
    rows = load(run / "traces.json")
    reviews = load(run / "reviews.json")
    cases = load(ROOT / "benchmarks/test.gold.json")
    by_id = {q["id"]: q for q in cases}
    if hashlib.sha256((run / "traces.json").read_bytes()).hexdigest() != reviews["traces_sha256"]:
        raise ValueError("Reviews do not match test trace hash")
    labels = {(r["method"], r["query_id"]): r for r in reviews["reviews"]}
    if len(rows) != 14 or len(labels) != 14 or len(reviews["reviews"]) != 14 or set(labels) != {(r["method"], r["query_id"]) for r in rows}:
        raise ValueError("Need all fourteen test results/reviews")
    out = {"split": "test", "reviewer": reviews["reviewer"], "independent_human_review": False, "methods": {}}
    for method in ("dense", "bm25"):
        selected = [t for t in rows if t["method"] == method]
        if len(selected) != 7 or {t["query_id"] for t in selected} != set(by_id):
            raise ValueError("Incomplete test coverage")
        method_reviews = [labels[(method, t["query_id"])] for t in selected]
        contexts, strict_contexts, hit1, hit3 = [], 0, 0, 0
        for t, r in zip(selected, method_reviews):
            if not r["reason"] or len(r["citation_reasons"]) != len(t["citations"]):
                raise ValueError("Every query/citation needs a written review reason")
            q = by_id[t["query_id"]]
            if q["answerable"]:
                if type(r["context_grade"]) is not int or r["context_grade"] not in (0, 1, 2):
                    raise ValueError("Need context grade for all five answerable test queries")
                contexts.append(r["context_grade"])
                events = [e for e in t["events"] if e["event"] == "search"]
                first = events[0]["results"] if events else []
                hit1 += bool(first and hit(first[0], q["gold"]))
                hit3 += any(hit(c, q["gold"]) for c in first[:3])
                chunks = {c["id"]: c for e in events for c in e["results"]}
                strict_contexts += any(c in chunks and hit(chunks[c], q["gold"]) for c in t["context_ids"])
        metrics = aggregate(cases, selected, method_reviews)
        out["methods"][method] = {**metrics, "hit1_strict_original_query": ratio(hit1, 5),
            "hit3_strict_original_query": ratio(hit3, 5), "context_evidence_rate_strict": ratio(strict_contexts, 5),
            "context_evidence_rate_reviewed": ratio(sum(c == 2 for c in contexts), 5),
            "context_grade_distribution": dict(Counter(contexts)), "median_ms": statistics.median(t["elapsed_ms"] for t in selected),
            "search_count_distribution": dict(Counter(t["search_count"] for t in selected)),
            "note": "Quality metrics exclude provider errors as in starter; all attempted/error counts are shown. Strict metrics retain all five answerable queries."}
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        path, data = args.run / "review_packet.json", prepare(args.run)
    else:
        path, data = args.run / "graded_summary.json", summarize(args.run)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(path), "review_rows": len(data) if isinstance(data, list) else None}))
