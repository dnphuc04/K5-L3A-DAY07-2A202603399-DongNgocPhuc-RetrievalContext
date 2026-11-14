import math
import unittest
from src.retrieval import BM25Retriever, DenseRetriever, HybridRetriever, pack_context


def chunk(cid, text, chapter="chapter_1"):
    return dict(id=cid, text=text, source_id="doc", source="doc.pdf", page=1, metadata={"chapter": chapter})


class RetrievalTests(unittest.TestCase):
    def test_bm25_known_score_and_filter(self):
        bm = BM25Retriever([chunk("a", "rare common"), chunk("b", "common other", "chapter_2")])
        hits = bm.search("rare")
        self.assertEqual([r["id"] for r in hits], ["a"])
        self.assertAlmostEqual(hits[0]["score"], math.log(2))
        self.assertEqual(bm.search("rare", filters={"chapter": "chapter_2"}), [])
        self.assertEqual(bm.search("nonexistent"), [])

    def test_unicode_and_deterministic_ties(self):
        bm = BM25Retriever([chunk("b", "Tiếng Việt"), chunk("a", "Tiếng Việt")])
        self.assertEqual([r["id"] for r in bm.search("TIẾNG")], ["a", "b"])

    def test_rrf_uses_ranks_not_incompatible_scores(self):
        class Fixed:
            def __init__(self, rows): self.rows = rows
            def search(self, query, **kwargs): return self.rows
        a, b, c = [chunk(x, x) for x in "abc"]
        dense = Fixed([{**a, "score": 0.9}, {**b, "score": 0.8}])
        lexical = Fixed([{**c, "score": 10000}, {**b, "score": 1}])
        rows = HybridRetriever(dense, lexical).search("q")
        self.assertEqual(rows[0]["id"], "b")
        self.assertAlmostEqual(rows[0]["score"], 2 / 62)
        self.assertEqual(len({r["id"] for r in rows}), len(rows))

    def test_dense_forwards_query_scope_and_propagates_error(self):
        class Embed:
            def embed_query(self, query):
                self.query = query
                return [1]
        class Store:
            def search(self, vector, **kwargs):
                self.args = (vector, kwargs)
                return [{**chunk("a", "text"), "score": 1}]
        embed, store = Embed(), Store()
        dense = DenseRetriever(embed, store)
        self.assertEqual(dense.search("q", filters={"chapter": "chapter_1"}, top_k=2)[0]["rank"], 1)
        self.assertEqual(store.args, ([1], {"filters": {"chapter": "chapter_1"}, "top_k": 2}))
        with self.assertRaises(ValueError): dense.search("q", filters={"gold_page": 1})
        class Broken:
            def embed_query(self, query): raise RuntimeError("provider failed")
        with self.assertRaises(RuntimeError): DenseRetriever(Broken(), store).search("q")

    def test_context_budget_includes_headers_and_dedups(self):
        a = chunk("a", "abc")
        context, ids = pack_context([a, a], budget=100)
        self.assertEqual(ids, ["a"])
        self.assertIn("doc.pdf", context)
        self.assertEqual(pack_context([a], budget=1), ("", []))


if __name__ == "__main__": unittest.main()
