"""Independent Qwen critic. This runner never approves Ouroboros or Cerberus."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

REQUIRED = ("cycle_id", "candidate_sha256", "source_commit", "evidence_urls")
FIELDS = ("finding_id", "severity", "classification", "summary", "reproduction",
          "attack_test", "pass_criteria", "fail_criteria", "evidence_urls")

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def validate_input(data):
    for key in REQUIRED:
        if not data.get(key):
            raise ValueError("missing input: " + key)
    digest = data["candidate_sha256"]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("candidate_sha256 must be lowercase SHA-256")
    if not isinstance(data["evidence_urls"], list) or not all(
        isinstance(x, str) and x.startswith("https://") for x in data["evidence_urls"]
    ):
        raise ValueError("evidence_urls must be HTTPS links")
    return data

def validate_report(report, expected):
    for key in ("cycle_id", "candidate_sha256", "source_commit", "model", "prompt_sha256",
                "input_sha256", "run_id", "created_at", "findings", "status"):
        if not report.get(key):
            raise ValueError("missing report: " + key)
    for key in ("cycle_id", "candidate_sha256", "source_commit"):
        if report[key] != expected[key]:
            raise ValueError("mismatched " + key)
    if report["status"] != "UNVERIFIED":
        raise ValueError("runner may not claim independent authentication or PASS")
    if not isinstance(report["findings"], list):
        raise ValueError("findings must be a list")
    for finding in report["findings"]:
        for field in FIELDS:
            if not finding.get(field):
                raise ValueError("finding missing " + field)
        if finding["severity"] not in ("P0", "P1", "P2", "P3"):
            raise ValueError("invalid severity")
        if finding["classification"] not in ("confirmed", "hypothesis"):
            raise ValueError("invalid classification")
        urls = finding["evidence_urls"]
        if not isinstance(urls, list) or not urls or not all(
            isinstance(url, str) and url.startswith("https://") for url in urls
        ):
            raise ValueError("invalid finding evidence")
    return report

def call_qwen(endpoint, model, prompt):
    if not endpoint.startswith("http://127.0.0.1:") and not endpoint.startswith("http://localhost:"):
        raise ValueError("only local Qwen endpoint permitted")
    payload = json.dumps({"model": model, "messages": [
        {"role": "system", "content": "You are an independent skeptical code reviewer. Return JSON only. Never invent evidence URLs. Mark untested risks as hypothesis."},
        {"role": "user", "content": prompt}
    ], "stream": False, "format": "json"}).encode()
    request = Request(endpoint.rstrip("/") + "/api/chat", payload,
                      {"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=180) as response:
        answer = json.load(response)
    return answer["message"]["content"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="qwen2.5:0.5b")
    args = parser.parse_args()
    raw = Path(args.input).read_bytes()
    candidate = validate_input(json.loads(raw))
    prompt = ("Review this candidate critically. Output JSON object with 'findings' list. "
              "Each finding must include finding_id, severity P0-P3, classification "
              "confirmed or hypothesis, summary, reproduction, attack_test, "
              "pass_criteria, fail_criteria, evidence_urls. Use only supplied evidence; "
              "do not invent execution or test results. Candidate:\n" +
              json.dumps(candidate, ensure_ascii=False, sort_keys=True))
    response = json.loads(call_qwen(args.endpoint, args.model, prompt))
    report = {
        "cycle_id": candidate["cycle_id"],
        "candidate_sha256": candidate["candidate_sha256"],
        "source_commit": candidate["source_commit"],
        "model": args.model,
        "prompt_sha256": sha256_bytes(prompt.encode()),
        "input_sha256": sha256_bytes(raw),
        "run_id": os.environ.get("GITHUB_RUN_ID", "local-unattested"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "findings": response.get("findings", []),
        "status": "UNVERIFIED",
        "provenance": "Requires independent GitHub attestation and verifier; self-declared metadata is not authentication",
    }
    validate_report(report, candidate)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

if __name__ == "__main__":
    main()
