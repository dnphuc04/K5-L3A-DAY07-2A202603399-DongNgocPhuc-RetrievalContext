import unittest
from src.day6_adapter import convert_chunk, convert_question, Day6VectorReader


class Day6AdapterTests(unittest.TestCase):
    def test_preserves_identity_source_and_score(self):
        row = dict(chunk_id="c1", document_id="d1", source="original.pdf", page=12,
                   text="Evidence", metadata={"chapter": "chapter_1"}, score=0.9)
        converted = convert_chunk(row)
        self.assertEqual((converted["id"], converted["source_id"], converted["page"]), ("c1", "d1", 12))
        self.assertEqual(converted["metadata"], row["metadata"])
        self.assertEqual(converted["score"], 0.9)

    def test_unanswerable_has_no_fabricated_gold(self):
        q = convert_question(dict(id="u1", split="dev", question="Unknown?",
                                  answerable=False, absence_reason="Checked corpus"))
        self.assertNotIn("gold", q)
        self.assertEqual(q["expected_behavior"], "search_and_abstain")

    def test_rejects_invalid_vector_before_connecting(self):
        with self.assertRaises(ValueError):
            Day6VectorReader("unused").search([0.0] * 1536)
        with self.assertRaises(ValueError):
            Day6VectorReader("unused").search([float("nan")] * 1536)


if __name__ == "__main__":
    unittest.main()
