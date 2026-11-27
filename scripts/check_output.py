"""Fail closed on missing output, digest mismatch, or false approval."""
import hashlib
import json
from pathlib import Path
from fenrir.reviewer import validate_report

candidate = json.loads(Path("out/candidate.json").read_text())
expected = hashlib.sha256(Path("fixtures/demo_candidate.py").read_bytes()).hexdigest()
if candidate["candidate_sha256"] != expected or candidate.get("demo_only") is not True:
    raise SystemExit("invalid demo candidate digest or marker")
report = json.loads(Path("out/FENRIR_REPORT.json").read_text())
validate_report(report, candidate)
if report["status"] != "UNVERIFIED" or report["cycle_id"].startswith("ORIL-OFC"):
    raise SystemExit("false promotion of demo result")
print("Report schema OK; UNVERIFIED demo only; NOT a Cerberus admission")
