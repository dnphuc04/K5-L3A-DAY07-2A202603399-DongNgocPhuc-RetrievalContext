"""Dense, BM25 and rank-based hybrid retrieval over the same Day 6 snapshot."""
from collections import Counter
import math
import re
import unicodedata


def tokenize(text):
    """NFC + casefold + Unicode word tokens; Vietnamese syllables, no segmentation."""
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


def validate_search(query, filters, top_k):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be nonempty")
    if type(top_k) is not int or top_k < 1:
        raise ValueError("top_k must be positive")
    if filters is not None and (not isinstance(filters, dict) or set(filters) - {"chapter"}
                                or any(not isinstance(v, str) or not v for v in filters.values())):
        raise ValueError("Only explicit chapter string filters are supported")


class DenseRetriever:
    def __init__(self, embedder, store):
        self.embedder, self.store = embedder, store

    def search(self, query, *, filters=None, top_k=3):
        validate_search(query, filters, top_k)
        rows = self.store.search(self.embedder.embed_query(query), filters=filters, top_k=top_k)
        return [{**r, "rank": i, "strategy": "dense"} for i, r in enumerate(rows, 1)]


class BM25Retriever:
    def __init__(self, chunks, k1=1.5, b=0.75):
        if not chunks or len({c["id"] for c in chunks}) != len(chunks):
            raise ValueError("Require nonempty corpus with unique IDs")
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("Invalid BM25 parameters")
        self.chunks, self.k1, self.b = chunks, k1, b
        self.counts = [Counter(tokenize(c["text"])) for c in chunks]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.avgdl = sum(self.lengths) / len(chunks)
        if not self.avgdl:
            raise ValueError("Corpus has no tokens")
        df = Counter(term for counts in self.counts for term in counts)
        self.idf = {term: math.log(1 + (len(chunks) - n + 0.5) / (n + 0.5)) for term, n in df.items()}

    def search(self, query, *, filters=None, top_k=3):
        validate_search(query, filters, top_k)
        terms = set(tokenize(query))
        results = []
        for c, counts, length in zip(self.chunks, self.counts, self.lengths):
            if any(c["metadata"].get(k) != v for k, v in (filters or {}).items()):
                continue
            score = sum(self.idf[t] * counts[t] * (self.k1 + 1) /
                        (counts[t] + self.k1 * (1 - self.b + self.b * length / self.avgdl))
                        for t in terms if counts[t])
            if score > 0:
                results.append({**c, "score": score, "strategy": "bm25"})
        results.sort(key=lambda c: (-c["score"], c["id"]))
        return [{**c, "rank": i} for i, c in enumerate(results[:top_k], 1)]


class HybridRetriever:
    def __init__(self, dense, lexical, candidate_k=20, rrf_k=60):
        if type(candidate_k) is not int or candidate_k < 1 or rrf_k <= 0:
            raise ValueError("Invalid RRF parameters")
        self.dense, self.lexical = dense, lexical
        self.candidate_k, self.rrf_k = candidate_k, rrf_k

    def search(self, query, *, filters=None, top_k=3):
        validate_search(query, filters, top_k)
        depth = max(top_k, self.candidate_k)
        rankings = {"dense": self.dense.search(query, filters=filters, top_k=depth),
                    "bm25": self.lexical.search(query, filters=filters, top_k=depth)}
        combined = {}
        for method, rows in rankings.items():
            seen = set()
            for rank, row in enumerate(rows, 1):
                if row["id"] in seen:
                    raise ValueError("Duplicate ID in component ranking")
                seen.add(row["id"])
                item = combined.setdefault(row["id"], {**row, "score": 0.0, "strategy": "hybrid_rrf", "components": {}})
                item["score"] += 1 / (self.rrf_k + rank)
                item["components"][method] = {"rank": rank, "score": row["score"]}
        rows = sorted(combined.values(), key=lambda r: (-r["score"], r["id"]))[:top_k]
        return [{**row, "rank": rank} for rank, row in enumerate(rows, 1)]


def pack_context(results, budget=4000):
    """Whole chunks, ranking order, source headers included in character budget."""
    blocks, ids, seen = [], [], set()
    for c in results:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        block = f'[{c["id"]} | {c["source"]} | page {c["page"]}]\n{c["text"]}'
        if len("\n\n".join(blocks + [block])) <= budget:
            blocks.append(block)
            ids.append(c["id"])
    return "\n\n".join(blocks), ids
