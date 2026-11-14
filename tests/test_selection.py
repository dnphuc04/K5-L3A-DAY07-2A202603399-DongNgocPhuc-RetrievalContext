import copy
import unittest
from scripts.select_pipeline import selection_key


class SelectionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {"id": "example", "graded": {
            "grounded_answer": {"mean_out_of_2": 2}, "context_evidence_rate": {"rate": 1},
            "citation_validity": {"rate": 1}, "abstention": {"n": 2}, "median_ms": 100,
            "model_calls": 35}, "retrieval": {"first_original_query_hit3": {"rate": 1}}}

    def test_quality_precedes_latency(self):
        fast = copy.deepcopy(self.candidate)
        fast["graded"]["median_ms"] = 1
        fast["graded"]["grounded_answer"]["mean_out_of_2"] = 1.99
        self.assertGreater(selection_key(self.candidate), selection_key(fast))

    def test_same_cutoff_hit3_precedes_latency(self):
        fast = copy.deepcopy(self.candidate)
        fast["graded"]["median_ms"] = 1
        fast["retrieval"]["first_original_query_hit3"]["rate"] = 14 / 15
        self.assertGreater(selection_key(self.candidate), selection_key(fast))

    def test_na_citation_validity_does_not_win(self):
        other = copy.deepcopy(self.candidate)
        other["graded"]["citation_validity"]["rate"] = None
        self.assertGreater(selection_key(self.candidate), selection_key(other))


if __name__ == "__main__": unittest.main()
