import unittest
from pathlib import Path
from fenrir.d2_review import load_candidate, quality

class D2Tests(unittest.TestCase):
    def test_pinned_real_candidate(self):
        c = load_candidate(Path("handoff/d2-raw-1.zip"))
        self.assertEqual(len(c["public_counterexamples"]), 10)
        self.assertEqual(c["public_counterexamples"][0]["group_id"], "public-arithmetic-09")
        self.assertEqual(c["public_counterexamples"][0]["expected"], "38")

    def test_unverified_review_gate(self):
        c = load_candidate(Path("handoff/d2-raw-1.zip"))
        report = {k:c[k] for k in ("cycle_id","candidate_sha256","source_commit")}
        report.update(model="test",prompt_sha256="x",input_sha256="x",run_id="test",created_at="test",status="UNVERIFIED")
        f = dict(finding_id="F1",severity="P2",classification="hypothesis",summary="test",
                 reproduction="public-arithmetic-09",attack_test="compare",pass_criteria="matches",
                 fail_criteria="differs",evidence_urls=c["evidence_urls"])
        report["findings"] = [f]
        quality(report,c)
        for changed in (dict(classification="confirmed"),dict(reproduction="unrelated"),dict(fail_criteria="matches")):
            report["findings"] = [dict(f,**changed)]
            with self.assertRaises(ValueError):
                quality(report,c)
