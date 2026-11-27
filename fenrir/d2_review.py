"""Independent D2 review of a pinned, public Ouroboros artifact. Never promotes."""
import hashlib
import json
import os
from pathlib import Path
import zipfile
from urllib.request import urlopen
from fenrir.reviewer import call_qwen, parse_findings, validate_input, validate_report

ARCHIVE_SHA = "10c9873b297f795df130de2f30b6618b5ed081c5f073193aa615d2bf659e0297"
CANDIDATE_SHA = "d6f516b6fea97f30441bf96c9051835a81b5b924d5315a3fba485456000c89ba"
SOURCE = "5c5b4a93be07e7dc39f355c1f6bbf2e978dafd50"
CYCLE = "45913964999-1"
URL = "https://github.com/js775315672-spec/Harness-Ouroboros-MCP/actions/runs/45913964999"
MODEL = "qwen2.5:1.5b"

def digest(b):
    return hashlib.sha256(b).hexdigest()

def strict_json(b):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError("duplicate JSON key")
            d[k] = v
        return d
    return json.loads(b, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))

def load_candidate(path):
    if digest(path.read_bytes()) != ARCHIVE_SHA:
        raise ValueError("wrong archive digest")
    with zipfile.ZipFile(path) as z:
        names = ["candidate/candidate.json", "candidate/ab.json", "candidate/aa.json",
                 "input/public_30_pairs.json"]
        if len(z.infolist()) != len(names) or set(z.namelist()) != set(names) or any(i.file_size > 2_000_000 for i in z.infolist()):
            raise ValueError("unexpected archive members")
        raw = z.read(names[0])
        c = strict_json(raw)
        if digest(raw) != CANDIDATE_SHA or c["cycle_id"] != CYCLE or c["implementation_sha"] != SOURCE:
            raise ValueError("candidate identity mismatch")
        if digest(c["prompt"].encode()) != c["candidate_sha"]:
            raise ValueError("prompt identity mismatch")
        for n in ("ab.json", "aa.json"):
            if digest(z.read("candidate/"+n)) != c["raw_sha256"][n]:
                raise ValueError("raw evidence mismatch")
        if digest(z.read(names[3])) != c["parent_evidence_sha256"]:
            raise ValueError("predecessor mismatch")
        rows = strict_json(z.read(names[1]))["rows"]
    if len(rows) != 30:
        raise ValueError("wrong public group count")
    wrong = []
    for i, row in enumerate(rows):
        a, b = 11+3*i, 2+i%7
        gid = f"public-arithmetic-{i+1:02d}"
        expected = str(a+b)
        if row["group_id"] != gid or row["expected"] != expected or row["question"] != f"What is {a} plus {b}? Answer with only the integer.":
            raise ValueError("public task drift")
        obs = [o for o in row["observations"] if o["variant"] == "compact"]
        if len(obs) != 1 or type(obs[0]["output"]) is not str:
            raise ValueError("missing compact observation")
        if obs[0]["output"].strip() != expected:
            wrong.append({"group_id": gid, "question": row["question"], "expected": expected, "observed": obs[0]["output"]})
    if not wrong:
        raise ValueError("unexpected missing counterexample")
    return validate_input({"cycle_id": CYCLE, "candidate_sha256": CANDIDATE_SHA,
                           "source_commit": SOURCE, "evidence_urls": [URL],
                           "candidate_text": c["prompt"], "public_counterexamples": wrong})

def quality(report, candidate):
    validate_report(report, candidate)
    if not report["findings"]:
        raise ValueError("empty model findings")
    ids = {x["group_id"] for x in candidate["public_counterexamples"]}
    for f in report["findings"]:
        if f["classification"] != "hypothesis":
            raise ValueError("model must not self-certify a causal finding")
        if not any(gid in f["reproduction"] for gid in ids):
            raise ValueError("reproduction must identify a measured counterexample")
        if f["pass_criteria"].strip().casefold() == f["fail_criteria"].strip().casefold():
            raise ValueError("pass and fail criteria must differ")

def main():
    out = Path("out")
    out.mkdir(exist_ok=False)
    candidate = load_candidate(Path("handoff/d2-raw-1.zip"))
    raw = json.dumps(candidate, sort_keys=True, ensure_ascii=False).encode()
    (out/"candidate.json").write_bytes(raw)
    with urlopen("http://127.0.0.1:11434/api/tags", timeout=15) as response:
        models = strict_json(response.read())["models"]
    matches = [m for m in models if m["name"] == MODEL]
    if len(matches) != 1 or len(matches[0]["digest"]) != 64:
        raise ValueError("model digest unavailable")
    prompt = ("Review the supplied public arithmetic prompt and actual wrong answers. "
              "The model cannot prove causation. Return one testable hypothesis, not a confirmed claim. "
              "Use classification hypothesis, severity P2 or P3, all required fields. "
              "In reproduction include an exact public-arithmetic group ID, expected and observed answer. "
              "Propose a concrete attack_test and distinguish pass_criteria from fail_criteria. "
              "Use only the supplied evidence URL. Never approve the candidate. Input: " + raw.decode())
    for attempt in (1, 2):
        answer = call_qwen("http://127.0.0.1:11434", MODEL, prompt)
        (out/f"model-output-{attempt}.json").write_text(answer, encoding="utf-8")
        try:
            report = {
                "cycle_id": CYCLE, "candidate_sha256": CANDIDATE_SHA, "source_commit": SOURCE,
                "archive_sha256": ARCHIVE_SHA, "model": MODEL, "model_digest": matches[0]["digest"],
                "prompt_sha256": digest(prompt.encode()), "input_sha256": digest(raw),
                "run_id": os.environ["GITHUB_RUN_ID"], "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
                "reviewer_commit": os.environ["GITHUB_SHA"], "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "findings": parse_findings(answer), "measured_counterexamples": candidate["public_counterexamples"],
                "status": "UNVERIFIED", "promotion_allowed": False, "protected_grade": "pending"
            }
            quality(report, candidate)
        except (ValueError, KeyError, TypeError) as exc:
            print(f"review attempt {attempt} rejected: {exc}", flush=True)
            prompt += "\nPrevious output was rejected: " + str(exc) + ". Return a corrected JSON object."
            continue
        (out/"FENRIR_REPORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
        print(f"Independent model review contract passed on attempt {attempt}; public only; UNVERIFIED")
        return
    raise SystemExit("model review quality gate failed; no admission")

if __name__ == "__main__":
    main()
