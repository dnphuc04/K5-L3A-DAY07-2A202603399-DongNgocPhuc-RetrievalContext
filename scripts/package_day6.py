"""Create a local, private handoff of the exact Day 6 snapshot; no secrets/API calls."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_agent_test import verify_freezes
from src.day6_adapter import convert_chunk


def package(day6, output):
    from dotenv import dotenv_values
    import psycopg
    if output.exists():
        raise ValueError("Output already exists")
    verify_freezes()
    files = ["data/manifest.json", "starter/data/bao_cao_thuc_tap.pdf",
             "starter/results/chunks/C.jsonl", "starter/results/ingestion.json",
             "starter/src/embeddings.py", "benchmark/dev.jsonl", "benchmark/test.jsonl"]
    payloads = {"day6/" + name: (day6 / name).read_bytes() for name in files}
    frozen = json.loads((ROOT / "benchmarks/freeze.json").read_text(encoding="utf-8"))["source_sha256"]
    for name, key in (("starter/data/bao_cao_thuc_tap.pdf", "pdf"), ("data/manifest.json", "manifest"), ("starter/results/chunks/C.jsonl", "chunks_C")):
        if hashlib.sha256(payloads["day6/" + name]).hexdigest() != frozen[key]:
            raise ValueError("Source changed since benchmark freeze")
    env = dotenv_values(day6 / "starter/.env")
    with psycopg.connect(os.environ.get("DATABASE_URL") or env.get("DATABASE_URL"), connect_timeout=5) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        rows = conn.execute("SELECT chunk_id, document_id, source, page, text, metadata, embedding::text FROM lab_chunks WHERE strategy=%s ORDER BY chunk_id", ("C",)).fetchall()
    keys = ("chunk_id", "document_id", "source", "page", "text", "metadata")
    vectors = [{**dict(zip(keys, row[:6])), "embedding": json.loads(row[6])} for row in rows]
    expected = [json.loads(s) for s in payloads["day6/starter/results/chunks/C.jsonl"].decode("utf-8").splitlines() if s.strip()]
    if ({r["chunk_id"]: convert_chunk(r) for r in vectors} != {r["chunk_id"]: convert_chunk(r) for r in expected}
            or len(vectors) != len(expected)):
        raise ValueError("Database differs from frozen chunks")
    for row in vectors:
        if len(row["embedding"]) != 1536 or not any(row["embedding"]) or not all(math.isfinite(x) for x in row["embedding"]):
            raise ValueError("Invalid stored vector")
    payloads["vectors_C.json"] = (json.dumps(vectors, ensure_ascii=False) + "\n").encode("utf-8")
    cache = ROOT / "data/local/query_cache"
    for path in sorted(cache.glob("*.json")):
        payloads["query_cache/" + path.name] = path.read_bytes()
    manifest = {"scope": "Private grading/reproduction only; no credentials included",
                "strategy": "C", "rows": len(vectors), "dimensions": 1536, "source_sha256": frozen,
                "files_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}}
    payloads["handoff_manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in payloads.items():
            archive.writestr(name, data)
    return {"path": str(output), "rows": len(vectors), "files": len(payloads),
            "bytes": output.stat().st_size, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day6-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(package(args.day6_root, args.output)))
