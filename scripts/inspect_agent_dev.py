"""Offline evidence checks and review packet. Never calls models or opens test gold."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_retrieval_dev import hit, ratio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    rows = json.loads((args.run / "traces.json").read_text(encoding="utf-8"))
    gold = {q["id"]: q for q in json.loads((ROOT / "benchmarks/dev.gold.json").read_text(encoding="utf-8"))}
    summary, packet = {}, []
    for method in sorted({t["method"] for t in rows}):
        selected = [t for t in rows if t["method"] == method]
        answerable = [t for t in selected if gold[t["query_id"]]["answerable"]]
        context_hits, hit1, hit3 = 0, 0, 0
        for t in selected:
            q = gold[t["query_id"]]
            searches = [e for e in t["events"] if e["event"] == "search"]
            first = searches[0]["results"] if searches else []
            chunks = {c["id"]: c for e in searches for c in e["results"]}
            if q["answerable"]:
                hit1 += bool(first and hit(first[0], q["gold"]))
                hit3 += any(hit(c, q["gold"]) for c in first[:3])
                context_hits += any(cid in chunks and hit(chunks[cid], q["gold"]) for cid in t["context_ids"])
            packet.append({"method": method, "query_id": t["query_id"], "question": t["question"],
                "status": t["status"], "answer": t["answer"], "citations": t["citations"],
                "cited_chunks": [chunks[c] for c in t["citations"] if c in chunks],
                "gold": q, "context": t["context"], "review": {
                    "reviewer": None, "answer_grade": None, "context_grade": None,
                    "citation_support": [None for _ in t["citations"]], "abstention_correct": None, "reason": None}})
        summary[method] = {"first_original_query_hit1": ratio(hit1, len(answerable)),
            "first_original_query_hit3": ratio(hit3, len(answerable)),
            "final_context_evidence_rate_strict": ratio(context_hits, len(answerable)),
            "note": "Strict span check only; answer/citation support and abstention require semantic review. Errors remain in denominator."}
    for name, value in (("context_checks.json", summary), ("review_packet.json", packet)):
        (args.run / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
