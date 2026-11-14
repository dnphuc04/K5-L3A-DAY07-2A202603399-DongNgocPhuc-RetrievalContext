"""Build a standalone basic demo from saved Day 6/7 evidence; no API calls."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads(path.read_text(encoding="utf-8"))
def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]
def build(day6):
    source = day6 / "starter/results"
    chunks = {s: [{k: r[k] for k in ("chunk_id", "page", "text", "metadata")} for r in lines(source / f"chunks/{s}.jsonl")] for s in "ABC"}
    chunk_runs = [{k: r[k] for k in ("question_id", "question", "strategy", "hits", "expected_answer", "evidence_quote", "gold_page", "applied_filter", "strict_hit1", "strict_hit3")} for r in lines(source / "dev/traces.jsonl")]
    with (day6 / "artifacts/experiment_log.csv").open(encoding="utf-8-sig", newline="") as stream:
        experiments = list(csv.DictReader(stream))
    retrieval = load(ROOT / "results/retrieval_dev_v3/evaluated.traces.json")
    agents = []
    for split in ("dev", "test"):
        for r in load(ROOT / f"results/agent_{split}_v1/traces.json"):
            agents.append({k: r[k] for k in ("query_id", "split", "method", "question", "status", "answer", "citations", "elapsed_ms")} | {"searches": [{k: e.get(k) for k in ("query", "results")} for e in r["events"] if e["event"] == "search"]})
    data = {"chunks": chunks, "chunk_runs": chunk_runs, "experiments": experiments, "retrieval": retrieval, "summary": load(ROOT / "results/retrieval_dev_v3/summary.json"), "gold": load(ROOT / "benchmarks/dev.gold.json"), "agents": agents, "agent_test": load(ROOT / "results/agent_test_v1/graded_summary.json")}
    assert len(chunks["A"]) == 112 and len(chunks["C"]) == 65
    assert len(chunk_runs) == 45 and len(retrieval) == 51
    template = (ROOT / "assets/demo-basic.template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    out = ROOT / "demo.html"
    out.write_text(template.replace("__DATA__", payload), encoding="utf-8")
    print(f"Built basic demo: {out.stat().st_size} bytes; 45 chunking traces; 51 retrieval traces; {len(agents)} agent traces")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day6-root", type=Path, default=ROOT.parent / "K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering")
    build(parser.parse_args().day6_root)
