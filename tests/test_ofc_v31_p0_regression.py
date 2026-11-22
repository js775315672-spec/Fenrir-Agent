import unittest
from agent import cycle_registry as r
SOURCE = "f" * 40

class FenrirAdversarialRegression(unittest.TestCase):
    def base(self):
        return dict(schema=1, agent=r.AGENT, cycle="cycle-f", source=SOURCE,
                    phase="open", owner="owner-1", generation=7, expires=0,
                    checkpoint="before", pending=None, results={"old": "receipt"})

    def test_f01_two_acquires_from_same_snapshot_need_remote_cas(self):
        # Both local transitions succeed. This proves a remote atomic CAS is mandatory,
        # NOT that the real remote is race-safe.
        first, _ = r.transition(self.base(), "acquire", "writer-a", 0, SOURCE, "", 100, 60)
        second, _ = r.transition(self.base(), "acquire", "writer-b", 0, SOURCE, "", 100, 60)
        self.assertEqual(first["generation"], second["generation"])
        self.assertNotEqual(first["owner"], second["owner"])
        self.assertEqual(first["results"], {"old": "receipt"})

    def test_f02_stale_owner_fenced(self):
        new, _ = r.transition(self.base(), "acquire", "writer-a", 0, SOURCE, "", 100, 60)
        with self.assertRaises(r.Blocked):
            r.transition(new, "record", "owner-1", 7, SOURCE, "old=forged", 101, 60)

    def test_f03_source_drift_blocks(self):
        with self.assertRaises(r.Blocked):
            r.transition(self.base(), "acquire", "writer-a", 0, "0"*40, "", 100, 60)

    def test_f04_pending_survives_expiry(self):
        state = self.base()
        state["pending"] = "unknown-side-effect"
        with self.assertRaises(r.Blocked):
            r.transition(state, "acquire", "writer-a", 0, SOURCE, "", 100, 60)
        self.assertEqual(state["pending"], "unknown-side-effect")

    def test_f05_untrusted_identity_rejected(self):
        state = self.base()
        state["agent"] = "other-agent"
        with self.assertRaises(r.Blocked):
            r.transition(state, "acquire", "writer-a", 0, SOURCE, "", 100, 60)
if __name__ == "__main__":
    unittest.main()
