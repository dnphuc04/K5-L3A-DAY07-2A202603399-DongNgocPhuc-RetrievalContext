"""Aggregate explicitly authored dev reviews; never auto-judge semantic support."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def ratio(n, N):
    return {"n": n, "N": N, "rate": n / N if N else None}


def summarize(run):
    traces = json.loads((run / "traces.json").read_text(encoding="utf-8"))
    reviews = json.loads((run / "reviews.json").read_text(encoding="utf-8"))
    gold = {q["id"]: q for q in json.loads((ROOT / "benchmarks/dev.gold.json").read_text(encoding="utf-8"))}
    by_key = {(r["method"], r["query_id"]): r for r in reviews["reviews"]}
    if len(by_key) != len(reviews["reviews"]) or set(by_key) != {(t["method"], t["query_id"]) for t in traces}:
        raise ValueError("Review coverage mismatch")
    if reviews["traces_sha256"] != hashlib.sha256((run / "traces.json").read_bytes()).hexdigest():
        raise ValueError("Labels do not match trace hash")
    out = {"reviewer": reviews["reviewer"], "independent_human_review": False, "methods": {}}
    for method in sorted({t["method"] for t in traces}):
        rows = [t for t in traces if t["method"] == method]
        grades, contexts, support, abstentions, false_abstentions = [], [], [], [], []
        for t in rows:
            q, r = gold[t["query_id"]], by_key[(method, t["query_id"])]
            if not r["reason"] or len(r["citation_support"]) != len(t["citations"]) or any(type(x) is not bool for x in r["citation_support"]):
                raise ValueError("Incomplete citation/reason review")
            if len(r["citation_reasons"]) != len(t["citations"]):
                raise ValueError("Need a reason for every citation")
            if t["status"] == "error":
                continue
            support.extend(r["citation_support"])
            if q["answerable"]:
                if type(r["answer_grade"]) is not int or r["answer_grade"] not in (0, 1, 2) or r["context_grade"] not in (0, 1, 2):
                    raise ValueError("Invalid answer/context grade")
                if t["status"] == "abstain" and r["answer_grade"] != 0:
                    raise ValueError("False abstention must grade zero")
                grades.append(r["answer_grade"])
                contexts.append(r["context_grade"])
                false_abstentions.append(t["status"] == "abstain")
            else:
                if type(r["abstention_correct"]) is not bool or (r["abstention_correct"] and t["status"] != "abstain"):
                    raise ValueError("Invalid abstention review")
                abstentions.append(r["abstention_correct"])
        out["methods"][method] = {"attempted": len(rows), "errors": sum(t["status"] == "error" for t in rows),
            "grounded_answer": {"distribution": dict(Counter(grades)), "sum": sum(grades), "max": 2 * len(grades),
                                "mean_out_of_2": statistics.mean(grades) if grades else None},
            "context_grades": dict(Counter(contexts)), "context_evidence_rate": ratio(sum(c == 2 for c in contexts), len(contexts)),
            "citation_validity": ratio(sum(support), len(support)), "abstention": ratio(sum(abstentions), len(abstentions)),
            "false_abstention": ratio(sum(false_abstentions), len(false_abstentions)),
            "answer_citation_coverage": ratio(sum(bool(t["citations"]) for t in rows if t["status"] == "answered"), sum(t["status"] == "answered" for t in rows)),
            "tool_use": ratio(sum(t["search_count"] > 0 for t in rows if t["status"] != "error"), sum(t["status"] != "error" for t in rows)),
            "median_ms": statistics.median(t["elapsed_ms"] for t in rows), "model_calls": sum(t["model_call_count"] for t in rows)}
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    result = summarize(args.run)
    (args.run / "graded_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
