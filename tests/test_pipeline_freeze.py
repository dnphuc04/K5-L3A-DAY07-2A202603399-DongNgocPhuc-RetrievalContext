import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PipelineFreezeTests(unittest.TestCase):
    def test_selected_pipeline_evidence_and_code_unchanged(self):
        frozen = json.loads((ROOT / "configs/pipeline_freeze.json").read_text(encoding="utf-8"))
        for name, expected in frozen["sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)

    def test_all_five_candidates_fully_reviewed_dev_only(self):
        comparison = json.loads((ROOT / "results/dev_comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(len(comparison["candidates"]), 5)
        self.assertEqual(comparison["split"], "dev")
        for candidate in comparison["candidates"]:
            self.assertEqual(candidate["graded"]["attempted"], 17)
            self.assertEqual(candidate["graded"]["errors"], 0)
            self.assertEqual(candidate["graded"]["grounded_answer"]["max"], 30)


if __name__ == "__main__": unittest.main()
