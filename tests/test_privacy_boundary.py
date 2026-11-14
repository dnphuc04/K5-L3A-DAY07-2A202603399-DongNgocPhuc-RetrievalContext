import unittest
from scripts.audit_submission_privacy import allowed_for_submission, private_path, secret_types


class PrivacyBoundaryTests(unittest.TestCase):
    def test_authorized_evidence_never_opens_credential_or_scratch_paths(self):
        for name in ("results/run/traces.json", "benchmarks/test.gold.json", "configs/pipeline_freeze.json",
                     "data/submission/day6_handoff.zip"):
            self.assertTrue(allowed_for_submission(name, True), name)
        for name in (".env", "docs/.env", "data/local/handoff.zip", "docs/key.pem", ".git/config"):
            self.assertFalse(allowed_for_submission(name, True), name)

    def test_known_credential_and_provider_patterns_without_printing_values(self):
        synthetic = b"sk-" + b"x" * 32
        self.assertIn("openai_key_pattern", secret_types(synthetic, []))
        known = b"custom-credential-" + b"y" * 20
        result = secret_types(b"prefix " + known, [known])
        self.assertEqual(result, ["known_local_credential_exact_match"])
        self.assertNotIn(known.decode(), str(result))

    def test_placeholder_url_is_allowed_but_credentialed_url_is_not(self):
        prefix = b"postgresql" + b"://"
        self.assertEqual(secret_types(prefix + b"USER:PASSWORD@host/db", []), [])
        self.assertIn("credentialed_database_url", secret_types(prefix + b"student:actual-pass@host/db", []))

    def test_private_payloads_excluded_but_code_templates_allowed(self):
        for name in ("results/run/traces.json", "benchmarks/test.gold.json", "configs/pipeline_freeze.json",
                     "docs/TEST_RESULTS.md", "data/local/handoff.zip", ".env", "key.pem"):
            self.assertTrue(private_path(name), name)
        for name in ("src/agent.py", ".env.example", "docs/PRIVACY_REVIEW.md", "artifacts/privacy_review.json"):
            self.assertFalse(private_path(name), name)


if __name__ == "__main__": unittest.main()
