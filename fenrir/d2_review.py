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
    samples = []
    for i, row in enumerate(rows):
        a, b = 11+3*i, 2+i%7
        gid = f"public-arithmetic-{i+1:02d}"
        expected = str(a+b)
        if row["group_id"] != gid or row["expected"] != expected or row["question"] != f"What is {a} plus {b}? Answer with only the integer.":
            raise ValueError("public task drift")
        obs = [o for o in row["observations"] if o["variant"] == "compact"]
        if len(obs) != 1 or type(obs[0]["output"]) is not str:
            raise ValueError("missing compact observation")
        sample = {"group_id": gid, "question": row["question"], "expected": expected, "observed": obs[0]["output"], "a": a, "b": b}
        samples.append(sample)
        if obs[0]["output"].strip() != expected:
            wrong.append(sample)
    if not wrong:
        raise ValueError("unexpected missing counterexample")
    return validate_input({"cycle_id": CYCLE, "candidate_sha256": CANDIDATE_SHA,
                           "source_commit": SOURCE, "evidence_urls": [URL],
                           "candidate_text": c["prompt"], "public_counterexamples": wrong,
                           "review_samples": [samples[0], wrong[0]]})

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

def narrow_schema(candidate):
    fields = {"group_id":{"type":"string","enum":[x["group_id"] for x in candidate["review_samples"]]},
              "expected":{"type":"string"}, "observed":{"type":"string"}, "hypothesis":{"type":"string"},
              "test_a":{"type":"integer","minimum":10,"maximum":99},
              "test_b":{"type":"integer","minimum":1,"maximum":99},
              "test_expected":{"type":"string"}}
    return {"type":"object","required":list(fields),"additionalProperties":False,"properties":fields}

def adapt_review(answer, candidate):
    x = strict_json(answer)
    actual = next((s for s in candidate["review_samples"] if s["group_id"] == x.get("group_id")), None)
    if actual is None or actual["expected"] == actual["observed"].strip():
        raise ValueError("model did not select an actual erroneous example")
    if x.get("expected") != actual["expected"] or x.get("observed") != actual["observed"]:
        raise ValueError("model did not identify exact correct and observed answers")
    a,b = x.get("test_a"),x.get("test_b")
    if type(a) is not int or type(b) is not int or not 10<=a<=99 or not 1<=b<=99 or not 10<=a+b<=99 or x.get("test_expected")!=str(a+b):
        raise ValueError("model did not propose valid two-digit addition test")
    # It must be new to the known 30-group public suite, including reversed operands.
    if any(sorted((a,b))==sorted((11+3*i,2+i%7)) for i in range(30)):
        raise ValueError("model repeated an existing public question")
    h=x.get("hypothesis")
    if not isinstance(h,str) or "digit" not in h.lower() or len(h.strip())<12:
        raise ValueError("model did not explain digit-related risk")
    return [{"finding_id":actual["group_id"],"severity":"P2","classification":"hypothesis",
             "summary":h,"reproduction":f'{actual["group_id"]}: expected {x["expected"]}; observed {x["observed"]}',
             "attack_test":f"Proposed, not executed: compare digit vs integer instruction on {a} + {b}.",
             "pass_criteria":f"Exact answer {a+b}","fail_criteria":f"Any answer other than {a+b}",
             "evidence_urls":candidate["evidence_urls"]}]

def review_prompt(candidate):
    samples = "\n".join(f'{s["group_id"]}: {s["a"]} + {s["b"]}; observed answer: {s["observed"]}' for s in candidate["review_samples"])
    return ("Audit the arithmetic outputs. System prompt under test: "+candidate["candidate_text"]+
            "\nThe task asks for an integer, not necessarily one digit. Select an incorrect row and calculate its correct answer. "
            "Return its exact group_id, expected answer, observed answer, and a hypothesis about the word digit. "
            "Also propose a new two-digit addition test: test_a, test_b, test_expected. Do not reuse the examples or claim causation.\n"+samples)

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
    prompt = review_prompt(candidate)
    for attempt in (1, 2):
        answer = call_qwen("http://127.0.0.1:11434", MODEL, prompt, schema=narrow_schema(candidate))
        (out/f"model-output-{attempt}.json").write_text(answer, encoding="utf-8")
        try:
            report = {
                "cycle_id": CYCLE, "candidate_sha256": CANDIDATE_SHA, "source_commit": SOURCE,
                "archive_sha256": ARCHIVE_SHA, "model": MODEL, "model_digest": matches[0]["digest"],
                "prompt_sha256": digest(prompt.encode()), "input_sha256": digest(raw),
                "run_id": os.environ["GITHUB_RUN_ID"], "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
                "reviewer_commit": os.environ["GITHUB_SHA"], "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "findings": adapt_review(answer, candidate), "measured_counterexamples": candidate["public_counterexamples"],
                "model_raw_output_sha256": digest(answer.encode()), "finding_metadata_origin": "deterministic adapter; model selects example, computes answers, provides hypothesis and test",
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
