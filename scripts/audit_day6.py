"""Read-only Day 6 inventory. Never prints credentials or calls model APIs."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit(root):
    manifest = read_json(root / "data/manifest.json")
    ingestion = read_json(root / "starter/results/ingestion.json")
    chunks = read_jsonl(root / "starter/results/chunks/C.jsonl")
    selected = set(manifest["selected_pages"])
    pdf = root / manifest["source_path_or_url"]
    normalize = lambda text: " ".join(text.split())
    dev = read_jsonl(root / "benchmark/dev.jsonl")
    # Read only test counts/schema: do not expose test questions or gold in output.
    test = read_jsonl(root / "benchmark/test.jsonl")
    result = {
        "day6_root": str(root.resolve()),
        "source": {
            "pdf_exists": pdf.is_file(),
            "sha256_matches": pdf.is_file() and hashlib.sha256(pdf.read_bytes()).hexdigest() == manifest["sha256"],
            "physical_pages_recorded": manifest["physical_page_count"],
            "selected_pages": len(selected),
            "permission": manifest["license_or_permission"],
        },
        "chunks": {
            "strategy": "C", "count": len(chunks),
            "unique_ids": len({c["chunk_id"] for c in chunks}) == len(chunks),
            "nonempty_text": all(c["text"].strip() for c in chunks),
            "pages_match_manifest": {c["page"] for c in chunks} == selected,
            "required_fields_present": all(set(("chunk_id", "document_id", "source", "page", "text", "metadata")) <= c.keys() for c in chunks),
        },
        "embedding": {k: ingestion.get(k) for k in ("provider", "model", "dimensions", "document_prefix", "query_prefix", "metric", "search", "table")},
        "benchmark": {
            "dev_count": len(dev), "test_count": len(test),
            "dev_unanswerable": sum(q.get("answerable") is False for q in dev),
            "test_unanswerable": sum(q.get("answerable") is False for q in test),
            "dev_evidence_in_selected_chunks": sum(any(c["document_id"] == q["gold_source_id"] and c["page"] == q["gold_page"] and normalize(q["evidence_quote"]) in normalize(c["text"]) for c in chunks) for q in dev),
            "old_test_results_exist": (root / "starter/results/test/traces.jsonl").is_file(),
        },
    }
    try:
        from dotenv import dotenv_values
        import psycopg
        env = dotenv_values(root / "starter/.env")
        for key in ("DATABASE_URL", "OPENAI_API_KEY"):
            env[key] = os.environ.get(key) or env.get(key)
        result["configuration"] = {"database_url_present": bool(env.get("DATABASE_URL")), "openai_key_present": bool(env.get("OPENAI_API_KEY"))}
        with psycopg.connect(env["DATABASE_URL"], connect_timeout=5) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            rows = conn.execute("SELECT chunk_id, document_id, source, page, text, metadata, vector_dims(embedding) FROM lab_chunks WHERE strategy=%s", ("C",)).fetchall()
            expected = {c["chunk_id"]: (c["document_id"], c["source"], c["page"], c["text"], c["metadata"]) for c in chunks}
            result["database"] = {"status": "connected_read_only", "strategy": "C", "rows": len(rows), "dimensions": sorted({r[6] for r in rows}), "matches_chunk_snapshot": len(rows) == len(expected) and all(expected.get(r[0]) == tuple(r[1:6]) for r in rows)}
            vectors = conn.execute("SELECT chunk_id, embedding::text FROM lab_chunks WHERE strategy=%s ORDER BY chunk_id", ("C",)).fetchall()
            parsed = [(cid, json.loads(raw)) for cid, raw in vectors]
            result["database"]["finite_nonzero_vectors"] = bool(parsed) and all(len(v) == 1536 and all(math.isfinite(x) for x in v) and any(v) for _, v in parsed)
            if parsed:
                # Exercise the Day 7 adapter with an existing document vector: no API call.
                import sys
                sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
                from src.day6_adapter import Day6VectorReader
                reader = Day6VectorReader(env["DATABASE_URL"])
                hits = reader.search(parsed[0][1], top_k=3)
                result["database"]["adapter_self_query"] = {"hits": len(hits), "top1_matches": bool(hits) and hits[0]["id"] == parsed[0][0], "top1_score": hits[0]["score"] if hits else None}
    except Exception as exc:
        # Raw exceptions can contain connection strings/passwords.
        result["database"] = {"status": "unverified", "error_type": type(exc).__name__}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day6-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.day6_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
