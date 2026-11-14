"""Validate an extracted private handoff and restore vectors into a NEW empty DB.

Reads credentials from DAY7_RESTORE_DATABASE_URL only. Never deletes/replaces data.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path


def validate_handoff(root):
    manifest = json.loads((root / "handoff_manifest.json").read_text(encoding="utf-8"))
    resolved_root = root.resolve()
    for name, expected in manifest["files_sha256"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(resolved_root) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Handoff path/hash mismatch")
    rows = json.loads((root / "vectors_C.json").read_text(encoding="utf-8"))
    if len(rows) != manifest["rows"] or len({r["chunk_id"] for r in rows}) != len(rows):
        raise ValueError("Invalid vector row count/IDs")
    chunks = [json.loads(s) for s in (root / "day6/starter/results/chunks/C.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
    fields = ("chunk_id", "document_id", "source", "page", "text", "metadata")
    if {r["chunk_id"]: {k:r[k] for k in fields} for r in rows} != {r["chunk_id"]: {k:r[k] for k in fields} for r in chunks}:
        raise ValueError("Vector and chunk snapshots differ")
    if manifest["strategy"] != "C" or manifest["dimensions"] != 1536:
        raise ValueError("Unexpected embedding contract")
    for row in rows:
        vector = row["embedding"]
        if (len(vector) != 1536 or not any(vector) or
                any(type(v) not in (int, float) or not math.isfinite(v) for v in vector)):
            raise ValueError("Invalid vector")
    return rows


def restore(root):
    import psycopg
    from psycopg.types.json import Jsonb
    rows = validate_handoff(root)
    url = os.environ.get("DAY7_RESTORE_DATABASE_URL")
    if not url:
        raise ValueError("Set DAY7_RESTORE_DATABASE_URL to a NEW database")
    with psycopg.connect(url, connect_timeout=5) as conn:
        if conn.execute("SELECT to_regclass('public.lab_chunks')").fetchone()[0] is not None:
            raise ValueError("Refusing to modify a database with existing lab_chunks")
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute("""CREATE TABLE lab_chunks (
            strategy text NOT NULL, chunk_id text NOT NULL, document_id text NOT NULL,
            source text NOT NULL, page integer NOT NULL, text text NOT NULL,
            metadata jsonb NOT NULL, embedding vector(1536) NOT NULL,
            PRIMARY KEY (strategy, chunk_id))""")
        with conn.cursor() as cursor:
            cursor.executemany("INSERT INTO lab_chunks VALUES (%s,%s,%s,%s,%s,%s,%s,%s::vector)",
                [("C", r["chunk_id"], r["document_id"], r["source"], r["page"], r["text"], Jsonb(r["metadata"]),
                  "[" + ",".join(str(v) for v in r["embedding"]) + "]") for r in rows])
        count = conn.execute("SELECT count(*) FROM lab_chunks WHERE strategy='C'").fetchone()[0]
        if count != len(rows):
            raise ValueError("Restored count differs")
    return {"status": "restored", "rows": count, "dimensions": 1536}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(restore(args.handoff_root)))
