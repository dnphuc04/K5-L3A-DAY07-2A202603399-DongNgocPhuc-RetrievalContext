"""Guard held-out benchmark integrity and model-input isolation, without tuning."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkContractTests(unittest.TestCase):
    def test_frozen_files_unchanged(self):
        frozen = json.loads((ROOT / "benchmarks/freeze.json").read_text(encoding="utf-8"))
        for name, expected in frozen["files_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)

    def test_inputs_have_only_allowed_fields(self):
        for split, expected_count in (("dev", 17), ("test", 7)):
            cases = json.loads((ROOT / f"benchmarks/{split}.inputs.json").read_text(encoding="utf-8"))
            self.assertEqual(len(cases), expected_count)
            for case in cases:
                self.assertLessEqual(set(case), {"id", "question", "filter"})
                self.assertTrue(case["id"] and case["question"])


if __name__ == "__main__":
    unittest.main()
