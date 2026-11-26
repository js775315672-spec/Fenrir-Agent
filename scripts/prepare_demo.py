"""Create an explicit public DEMO input, never impersonate an O artifact."""
import hashlib
import json
from pathlib import Path

sample = Path("fixtures/demo_candidate.py")
raw = sample.read_bytes()
data = {
    "cycle_id": "FENRIR-DEMO-NOT-ORIL-OFC-PR346-001",
    "candidate_sha256": hashlib.sha256(raw).hexdigest(),
    "source_commit": "DEMO-NOT-OUROBOROS",
    "evidence_urls": ["https://github.com/js775315672-spec/Fenrir-Agent/pull/1"],
    "candidate_text": raw.decode("utf-8"),
    "demo_only": True,
}
Path("out").mkdir(exist_ok=True)
Path("out/candidate.json").write_text(json.dumps(data, indent=2) + "\n")
