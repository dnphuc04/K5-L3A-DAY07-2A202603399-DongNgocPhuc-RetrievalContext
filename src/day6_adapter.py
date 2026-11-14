"""Validated Day 6 exports and read-only pgvector access; no gold in retrieval."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def convert_chunk(row):
    result = {"id": row["chunk_id"], "source_id": row["document_id"],
              **{key: row[key] for key in ("text", "source", "page", "metadata")}}
    if any(not isinstance(result[k], str) or not result[k].strip()
           for k in ("id", "source_id", "text", "source")):
        raise ValueError("Invalid chunk identity/text/source")
    if type(result["page"]) is not int or result["page"] < 1 or not isinstance(result["metadata"], dict):
        raise ValueError("Invalid physical page or metadata")
    if "score" in row:
        result["score"] = row["score"]
    return result


def convert_question(row):
    result = {key: row[key] for key in ("id", "split", "question")}
    if result["split"] not in ("dev", "test"):
        raise ValueError("Invalid benchmark split")
    result["answerable"] = row.get("answerable", True)
    if type(result["answerable"]) is not bool:
        raise ValueError("answerable must be boolean")
    if result["answerable"]:
        result.update(expected_answer=row["expected_answer"], gold=[{
            "source_id": row["gold_source_id"], "page": row["gold_page"],
            "evidence": row["evidence_quote"]}])
    else:
        result.update(expected_behavior="search_and_abstain", absence_reason=row["absence_reason"])
    if "filter" in row:
        result["filter"] = row["filter"]
    return result


class Day6VectorReader:
    """Read existing strategy C; schema creation and ingestion are not exposed."""
    def __init__(self, database_url, dimensions=1536):
        if dimensions != 1536:
            raise ValueError("Day 6 snapshot requires 1536 dimensions")
        self._database_url = database_url
        self.dimensions = dimensions

    def search(self, query_vector, *, filters=None, top_k=3):
        import psycopg
        from psycopg.types.json import Jsonb
        if (len(query_vector) != self.dimensions or
                any(type(v) not in (int, float) or not math.isfinite(v) for v in query_vector)
                or not any(query_vector)):
            raise ValueError("Invalid query vector")
        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        filters = filters or {}
        if not isinstance(filters, dict) or set(filters) - {"chapter"}:
            raise ValueError("Only chapter filters are supported")
        vector = "[" + ",".join(str(float(v)) for v in query_vector) + "]"
        with psycopg.connect(self._database_url, connect_timeout=5) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            rows = conn.execute("""SELECT chunk_id, document_id, source, page, text,
                metadata, 1-(embedding <=> %s::vector) AS score
                FROM lab_chunks WHERE strategy=%s AND metadata @> %s
                ORDER BY embedding <=> %s::vector, chunk_id LIMIT %s""",
                (vector, "C", Jsonb(filters), vector, top_k)).fetchall()
        keys = ("chunk_id", "document_id", "source", "page", "text", "metadata", "score")
        return [convert_chunk(dict(zip(keys, row))) for row in rows]


def export(root, output):
    chunk_path = root / "starter/results/chunks/C.jsonl"
    dev_path = root / "benchmark/dev.jsonl"
    read = lambda p: [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]
    chunks = [convert_chunk(c) for c in read(chunk_path)]
    questions = [convert_question(q) for q in read(dev_path)]
    if len({c["id"] for c in chunks}) != len(chunks):
        raise ValueError("Duplicate chunk IDs")
    if any(q["split"] != "dev" for q in questions):
        raise ValueError("Dev input contains another split")
    # Agent inputs are constructed by allowlist, never by removing selected gold fields.
    inputs = [{k: q[k] for k in ("id", "question", "filter") if k in q} for q in questions]
    output.mkdir(parents=True, exist_ok=True)
    for name, value in (("chunks.json", chunks), ("dev.gold.json", questions),
                        ("dev.inputs.json", inputs), ("provenance.json", {
                            "strategy": "C", "page_numbering": "physical PDF, 1-based",
                            "source_resolution": "Resolve chunk.source relative to the Day 6 repository root",
                            "input_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                             for p in (chunk_path, dev_path)}})):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"chunks": len(chunks), "dev_questions": len(questions), "test_exported": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day6-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.day6_root, args.output)))
