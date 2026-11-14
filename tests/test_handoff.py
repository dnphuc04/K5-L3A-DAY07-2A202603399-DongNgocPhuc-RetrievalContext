import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.restore_day6_handoff import validate_handoff


class HandoffTests(unittest.TestCase):
    def build(self, root, dimensions=1536):
        row = dict(chunk_id="c", document_id="d", source="doc.pdf", page=1, text="evidence", metadata={})
        chunks = root / "day6/starter/results/chunks/C.jsonl"
        chunks.parent.mkdir(parents=True)
        chunks.write_text(json.dumps(row) + "\n", encoding="utf-8")
        vectors = root / "vectors_C.json"
        vectors.write_text(json.dumps([{**row, "embedding": [1.] * dimensions}]), encoding="utf-8")
        manifest = {"rows": 1, "dimensions": 1536, "strategy": "C", "files_sha256": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (chunks, vectors)}}
        (root / "handoff_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_complete_snapshot_roundtrip_and_hash_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.build(root)
            self.assertEqual(validate_handoff(root)[0]["chunk_id"], "c")
            (root / "vectors_C.json").write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                validate_handoff(root)

    def test_wrong_embedding_dimension_rejected_before_database(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.build(root, dimensions=384)
            with self.assertRaisesRegex(ValueError, "Invalid vector"):
                validate_handoff(root)

    def test_manifest_cannot_read_outside_handoff(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "handoff_manifest.json").write_text(json.dumps({"files_sha256": {"../outside": "hash"}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "path/hash mismatch"):
                validate_handoff(root)


if __name__ == "__main__": unittest.main()
