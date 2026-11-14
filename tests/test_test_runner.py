import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.run_agent_test import verify_freezes


class TestRunnerIntegrityTests(unittest.TestCase):
    def test_refuses_modified_frozen_artifact_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            (root / "benchmarks").mkdir()
            artifact = root / "frozen.txt"
            artifact.write_text("original", encoding="utf-8")
            expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
            (root / "configs/pipeline_freeze.json").write_text(json.dumps({"sha256": {"frozen.txt": expected}}), encoding="utf-8")
            (root / "benchmarks/freeze.json").write_text(json.dumps({"files_sha256": {"frozen.txt": expected}}), encoding="utf-8")
            self.assertEqual(verify_freezes(root)["status"], "passed")
            artifact.write_text("modified", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Frozen file changed"):
                verify_freezes(root)


if __name__ == "__main__": unittest.main()
