import unittest
from fenrir.reviewer import validate_input, validate_report

SHA = "a" * 64
INPUT = {"cycle_id": "ORIL-OFC-PR346-001", "candidate_sha256": SHA,
         "source_commit": "083eb00e9efb", "evidence_urls": ["https://github.com/example/repo"]}
REPORT = {"cycle_id": INPUT["cycle_id"], "candidate_sha256": SHA,
          "source_commit": INPUT["source_commit"], "model": "qwen2.5:0.5b",
          "prompt_sha256": SHA, "input_sha256": SHA, "run_id": "local-unattested",
          "created_at": "2026-11-21T00:00:00Z", "findings": [], "status": "UNVERIFIED"}

class ContractTests(unittest.TestCase):
    def test_input(self):
        self.assertEqual(validate_input(INPUT)["candidate_sha256"], SHA)

    def test_missing_sha(self):
        with self.assertRaises(ValueError):
            validate_input({**INPUT, "candidate_sha256": ""})

    def test_mismatched_sha(self):
        with self.assertRaises(ValueError):
            validate_report({**REPORT, "candidate_sha256": "b" * 64}, INPUT)

    def test_cannot_self_approve(self):
        with self.assertRaises(ValueError):
            validate_report({**REPORT, "status": "PASS"}, INPUT)

    def test_empty_findings_not_a_pass(self):
        self.assertEqual(validate_report(REPORT, INPUT)["status"], "UNVERIFIED")

    def test_incomplete_finding_rejected(self):
        with self.assertRaises(ValueError):
            validate_report({**REPORT, "findings": [{"finding_id": "F-1"}]}, INPUT)

if __name__ == "__main__":
    unittest.main()
