"""Validate frozen Day 7 benchmark against original PDF and Day 6 snapshot."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(day6):
    from pypdf import PdfReader
    manifest_path = day6 / "data/manifest.json"
    manifest = load(manifest_path)
    pdf = day6 / manifest["source_path_or_url"]
    assert digest(pdf) == manifest["sha256"], "Source PDF hash changed"
    pages = {i + 1: norm(p.extract_text()) for i, p in enumerate(PdfReader(pdf).pages)}
    selected = manifest["selected_pages"]
    chunks_path = day6 / "starter/results/chunks/C.jsonl"
    chunks = [json.loads(s) for s in chunks_path.read_text(encoding="utf-8").splitlines() if s.strip()]
    all_cases, summary, checks = [], {}, []
    for split, minimum in (("dev", (15, 2)), ("test", (5, 2))):
        cases = load(ROOT / f"benchmarks/{split}.gold.json")
        counts = [sum(q["answerable"] is True for q in cases), sum(q["answerable"] is False for q in cases)]
        assert counts[0] >= minimum[0] and counts[1] >= minimum[1], "Insufficient split size"
        summary[split] = {"answerable": counts[0], "unanswerable": counts[1], "total": len(cases)}
        for q in cases:
            assert q["split"] == split and type(q["answerable"]) is bool
            assert q["id"] and q["question"].strip()
            if q["answerable"]:
                assert q["expected_answer"].strip() and q["gold"]
                evidence_checks = []
                for g in q["gold"]:
                    assert g["source_id"] == manifest["source_id"] and g["page"] in selected
                    assert norm(g["evidence"]) in pages[g["page"]], f'{q["id"]}: evidence missing from PDF'
                    matching = [c["chunk_id"] for c in chunks if c["document_id"] == g["source_id"] and c["page"] == g["page"] and norm(g["evidence"]) in norm(c["text"])]
                    assert matching, f'{q["id"]}: evidence split across chunks or absent'
                    if q.get("filter"):
                        assert any(c["chunk_id"] in matching and all(c["metadata"].get(k) == v for k, v in q["filter"].items()) for c in chunks)
                    evidence_checks.append({"page": g["page"], "chunk_ids": matching, "pdf_match": True})
                checks.append({"id": q["id"], "evidence": evidence_checks})
            else:
                assert "gold" not in q and q["absence_reason"].strip()
                assert q["expected_behavior"] == "search_and_abstain"
                check = q["absence_check"]
                checks.append({"id": q["id"], "scope": "all 33 indexed pages", "pages_scanned": len(selected),
                    "term_hits": {term: [p for p in selected if norm(term).casefold() in pages[p].casefold()] for term in check["terms"]},
                    "semantic_absence_review": "AI-assisted review of all selected page text; keyword hits alone do not prove absence", "missing_fact": check["missing_fact"]})
        inputs = [{k: q[k] for k in ("id", "question", "filter") if k in q and q[k] is not None} for q in cases]
        assert load(ROOT / f"benchmarks/{split}.inputs.json") == inputs, "Agent inputs differ or contain labels"
        all_cases.extend(cases)
    assert len({q["id"] for q in all_cases}) == len(all_cases), "Duplicate IDs"
    assert len({norm(q["question"]).casefold() for q in all_cases}) == len(all_cases), "Duplicate questions"
    old = [json.loads(s) for s in (day6 / "benchmark/test.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
    old_questions = {norm(q["question"]).casefold() for q in old}
    assert not any(norm(q["question"]).casefold() in old_questions for q in all_cases if q["split"] == "test")
    files = {f"benchmarks/{split}.{suffix}.json": digest(ROOT / f"benchmarks/{split}.{suffix}.json") for split in ("dev", "test") for suffix in ("gold", "inputs")}
    files["benchmarks/dev_absence.json"] = digest(ROOT / "benchmarks/dev_absence.json")
    files["benchmarks/README.md"] = digest(ROOT / "benchmarks/README.md")
    sources = {"pdf": digest(pdf), "manifest": digest(manifest_path), "chunks_C": digest(chunks_path)}
    return {"status": "passed", "counts": summary, "files_sha256": files, "source_sha256": sources, "checks": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day6-root", type=Path, required=True)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    report = validate(args.day6_root)
    frozen = ROOT / "benchmarks/freeze.json"
    if args.freeze:
        if frozen.exists():
            raise SystemExit("Freeze already exists; do not overwrite the held-out benchmark")
        frozen.write_text(json.dumps({"frozen_at": datetime.now(timezone.utc).isoformat(),
            "stage": "Before Day 7 Dense/BM25/Hybrid implementation or benchmark runs",
            "files_sha256": report["files_sha256"], "source_sha256": report["source_sha256"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif frozen.exists():
        prior = load(frozen)
        assert prior["files_sha256"] == report["files_sha256"] and prior["source_sha256"] == report["source_sha256"], "Frozen benchmark/corpus changed"
    (ROOT / "artifacts/benchmark_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "counts": report["counts"], "frozen": frozen.exists()}))
