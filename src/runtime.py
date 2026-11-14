"""Load verified Day 6 corpus and real retrievers without benchmark labels."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from .day6_adapter import Day6VectorReader, convert_chunk
from .retrieval import DenseRetriever, BM25Retriever, HybridRetriever


def load_runtime(day6, root):
    from dotenv import dotenv_values
    import psycopg
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    frozen = load(root / "benchmarks/freeze.json")
    # Test files are hashed, never parsed or run.
    for name, value in frozen["files_sha256"].items():
        if sha(root / name) != value:
            raise ValueError("Frozen benchmark changed")
    path = day6 / "starter/results/chunks/C.jsonl"
    if sha(path) != frozen["source_sha256"]["chunks_C"]:
        raise ValueError("Frozen corpus changed")
    ingestion = load(day6 / "starter/results/ingestion.json")
    if (ingestion["model"], ingestion["dimensions"], ingestion["query_prefix"]) != ("text-embedding-3-small", 1536, ""):
        raise ValueError("Embedding model contract changed")
    chunks = [convert_chunk(json.loads(s)) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]
    env = dotenv_values(day6 / "starter/.env")
    key = os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    url = os.environ.get("DATABASE_URL") or env.get("DATABASE_URL")
    with psycopg.connect(url, connect_timeout=5) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        rows = conn.execute("SELECT chunk_id, document_id, source, page, text, metadata, vector_dims(embedding) FROM lab_chunks WHERE strategy=%s", ("C",)).fetchall()
    fields = ("chunk_id", "document_id", "source", "page", "text", "metadata")
    actual = {r[0]: convert_chunk(dict(zip(fields, r[:6]))) for r in rows}
    if actual != {c["id"]: c for c in chunks} or len(rows) != len(chunks) or any(r[6] != 1536 for r in rows):
        raise ValueError("Database differs from frozen snapshot")
    spec = importlib.util.spec_from_file_location("day6_real_embeddings", day6 / "starter/src/embeddings.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    embedder = module.OpenAIEmbedder(key, cache_dir=root / "data/local/query_cache")
    dense = DenseRetriever(embedder, Day6VectorReader(url))
    bm25 = BM25Retriever(chunks)
    return key, embedder, {"dense": dense, "bm25": bm25, "hybrid_rrf": HybridRetriever(dense, bm25)}
