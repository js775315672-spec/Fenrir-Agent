"""D3-C5: verified facts are immutable; Qwen proposes falsifiable public tests."""
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
import zipfile
from fenrir.d2_review import ARCHIVE_SHA,CANDIDATE_SHA,SOURCE,CYCLE,load_candidate,strict_json
from fenrir.d3_compare import api,cpu_proof,proven_cpu,dump,sha,MODELS,PUBLIC

MODES=("digit_instruction","carry_difficulty")
# Predeclared disjoint strata; each proposal must be novel and meet its condition.
TASKS=[{"id":f"{lo}-{kind}","lo":lo,"hi":lo+9,"carry":kind=="carry"}
       for lo in (20,40,60) for kind in ("no_carry","carry")]
OPTIONS={"temperature":0,"seed":42,"num_thread":2,"num_ctx":2048,"num_predict":128,"num_gpu":0}

def check(ok,msg):
    if not ok: raise ValueError(msg)

def facts():
    path=Path("handoff/d2-raw-1.zip")
    c=load_candidate(path)
    with zipfile.ZipFile(path) as z:
        rows=strict_json(z.read("candidate/ab.json"))["rows"]
    out=[]
    for i,row in enumerate(rows):
        a,b=11+3*i,2+i%7
        observed=next(o["output"].strip() for o in row["observations"] if o["variant"]=="compact")
        expected=str(a+b)
        out.append({"id":row["group_id"],"a":a,"b":b,"expected":expected,"observed":observed,"mismatch":observed!=expected})
    check(len(out)==30 and sum(x["mismatch"] for x in out)==10,"source facts drift")
    return {"candidate_sha256":CANDIDATE_SHA,"candidate_text":c["candidate_text"],"rows":out,
            "confirmed_public_mismatches":10,"causal_claim":"not established"}

def schema(task):
    return {"type":"object","additionalProperties":False,"required":["hypothesis","a","b"],
            "properties":{"hypothesis":{"type":"string","enum":list(MODES)},
                          "a":{"type":"integer","minimum":task["lo"],"maximum":task["hi"]},
                          "b":{"type":"integer","minimum":1,"maximum":9}}}

def prompt(task,f):
    condition="a ones digit plus b is at least 10" if task["carry"] else "a ones digit plus b is less than 10"
    known=[list(p) for p in sorted(PUBLIC) if task["lo"]<=max(p)<=task["hi"]]
    return ("You propose an experiment, not a verdict. A public arithmetic model was instructed: "+
            json.dumps(f["candidate_text"])+". Its exact answer is checked by a separate program. "
            "Hypotheses: digit_instruction (compare digit-only versus integer-only wording); "
            "carry_difficulty (compare arithmetic with and without a carry, using integer-only wording). "
            "Choose one hypothesis and a new pair of integers a,b. "
            f"a from {task['lo']} to {task['hi']}; b from 1 to 9; {condition}. "
            "Use carry_difficulty only for a carry pair. Avoid existing unordered pairs "+json.dumps(known)+
            ". Return JSON with hypothesis,a,b only. Do not calculate, classify original answers, or write prose.")

def evaluate(task,raw):
    try:
        x=strict_json(raw)
        check(type(x) is dict and set(x)=={"hypothesis","a","b"},"schema")
        a,b=x["a"],x["b"];h=x["hypothesis"]
        check(type(a) is int and type(b) is int and task["lo"]<=a<=task["hi"] and 1<=b<=9,"operand range")
        check((a%10+b>=10)==task["carry"],"carry stratum")
        check(tuple(sorted((a,b))) not in PUBLIC,"known test")
        check(h in MODES and (h!="carry_difficulty" or task["carry"]),"hypothesis applicability")
        # These are test plans, not inferred facts or executed evidence.
        if h=="digit_instruction":
            arms=[{"instruction":"Reply with only the digit.","a":a,"b":b},
                  {"instruction":"Reply with only the integer.","a":a,"b":b}]
        else:
            arms=[{"instruction":"Reply with only the integer.","a":a,"b":b},
                  {"instruction":"Reply with only the integer.","a":a-a%10,"b":b}]
        for arm in arms: arm["expected"]=str(arm["a"]+arm["b"])
        return {"pass":True,"hypothesis":h,"proposal":[a,b],"arms":arms,
                "classification":"hypothesis","test_executed":False}
    except (ValueError,TypeError,KeyError) as e:
        return {"pass":False,"reason":str(e)}

def run(size):
    f=facts(); model=MODELS[size]
    tags=[x for x in api("/api/tags")["models"] if x["name"]==model]
    check(len(tags)==1 and len(tags[0]["digest"])==64,"model identity")
    digest=tags[0]["digest"]; rows=[]
    out=Path("out");out.mkdir(exist_ok=True)
    warm=api("/api/chat",{"model":model,"messages":[{"role":"user","content":"Reply OK."}],"stream":False,"options":OPTIONS,"keep_alive":"10m"})
    check(warm.get("done") is True,"warmup")
    for task in TASKS:
        p=prompt(task,f); start=time.perf_counter()
        response=api("/api/chat",{"model":model,"messages":[{"role":"system","content":"Return only the requested JSON."},{"role":"user","content":p}],"stream":False,"format":schema(task),"options":OPTIONS,"keep_alive":"10m"})
        elapsed=time.perf_counter()-start
        check(response.get("done") is True and type(response.get("eval_count")) is int and response["eval_count"]>0,"inference metadata")
        active=[x for x in api("/api/ps")["models"] if x["name"]==model]
        check(len(active)==1 and active[0]["digest"]==digest,"model drift")
        proof,rss=cpu_proof()
        row={"id":task["id"],"prompt_sha256":sha(p.encode()),"raw":response["message"]["content"],"wall_seconds":elapsed,
             "eval_count":response["eval_count"],"cpu_proof":proof,"rss_sample_mib":rss}
        row["result"]=evaluate(task,row["raw"])
        with (out/f"diagnostics-{size}.jsonl").open("a",encoding="utf-8") as stream: stream.write(json.dumps(row,ensure_ascii=False)+"\n")
        check(proven_cpu(proof),"CPU hardware evidence missing")
        rows.append(row);print(size,task["id"],row["result"],round(elapsed,3),flush=True)
    obj={"schema":1,"cycle_id":CYCLE,"source_commit":SOURCE,"candidate_sha256":CANDIDATE_SHA,
         "archive_sha256":ARCHIVE_SHA,"run_id":os.environ["GITHUB_RUN_ID"],"run_attempt":os.environ["GITHUB_RUN_ATTEMPT"],
         "commit":os.environ["GITHUB_SHA"],"model":model,"model_digest":digest,"options":OPTIONS,
         "facts_sha256":sha(dump(f)),"tasks":TASKS,"rows":rows,"status":"UNVERIFIED","promotion_allowed":False}
    (out/f"proposal-{size}.json").write_bytes(dump(obj))

def verify(obj,size,f):
    for k,v in {"cycle_id":CYCLE,"source_commit":SOURCE,"candidate_sha256":CANDIDATE_SHA,"archive_sha256":ARCHIVE_SHA,
                "run_id":os.environ["GITHUB_RUN_ID"],"run_attempt":os.environ["GITHUB_RUN_ATTEMPT"],"commit":os.environ["GITHUB_SHA"],
                "model":MODELS[size],"options":OPTIONS,"facts_sha256":sha(dump(f)),"tasks":TASKS,"status":"UNVERIFIED","promotion_allowed":False}.items():
        check(obj[k]==v,"identity "+k)
    check(len(obj["model_digest"])==64 and all(c in "0123456789abcdef" for c in obj["model_digest"]),"digest")
    rows=obj["rows"];check([r["id"] for r in rows]==[t["id"] for t in TASKS],"tasks")
    accepted=[]
    for t,r in zip(TASKS,rows):
        check(r["prompt_sha256"]==sha(prompt(t,f).encode()) and r["result"]==evaluate(t,r["raw"]),"raw grade")
        check(proven_cpu(r["cpu_proof"]) and type(r["eval_count"]) is int and r["eval_count"]>0 and math.isfinite(r["wall_seconds"]) and r["wall_seconds"]>0,"execution proof")
        if r["result"]["pass"]: accepted.append(r["result"])
    check(len({tuple(x["proposal"]) for x in accepted})==len(accepted),"duplicate proposals")
    return {"passed":len(accepted),"total":len(TASKS),"median_seconds":round(statistics.median(r["wall_seconds"] for r in rows),4),
            "max_rss_mib":round(max(r["rss_sample_mib"] for r in rows),2)}

def select():
    f=facts();out=Path("out");out.mkdir(exist_ok=True); stats={}; objects={}
    for size in MODELS:
        files=list(Path("bench").rglob(f"proposal-{size}.json"));check(len(files)==1,"missing artifact")
        o=strict_json(files[0].read_bytes());stats[size]=verify(o,size,f);objects[size]=o
        (out/f"proposal-{size}.json").write_bytes(dump(o))
    eligible=[s for s in MODELS if stats[s]["passed"]==len(TASKS)]
    selected=eligible[0] if eligible else None
    summary={"actual_calls":18,"stats":stats,"selected":selected,"scope":"public constrained test proposal contract only",
             "promotion_allowed":False,"candidate_sha256":CANDIDATE_SHA,"cycle_id":CYCLE}
    (out/"summary.json").write_bytes(dump(summary));(out/"facts.json").write_bytes(dump(f))
    print(json.dumps(summary),flush=True)
    if selected is None: raise SystemExit("No eligible proposal configuration")
    o=objects[selected]
    report={"cycle_id":CYCLE,"source_commit":SOURCE,"candidate_sha256":CANDIDATE_SHA,"archive_sha256":ARCHIVE_SHA,
            "run_id":o["run_id"],"run_attempt":o["run_attempt"],"reviewer_commit":o["commit"],"model":o["model"],"model_digest":o["model_digest"],
            "facts_sha256":sha(dump(f)),"summary_sha256":sha(dump(summary)),"proposal_sha256":sha(dump(o)),
            "hypotheses":[r["result"] for r in o["rows"]],"status":"UNVERIFIED","protected_grade":"pending","promotion_allowed":False,
            "test_execution":"not performed; independent Cerberus evaluation required"}
    (out/"FENRIR_PROPOSALS.json").write_bytes(dump(report))

if __name__=="__main__":
    if sys.argv[1]=="select": select()
    else: run(sys.argv[1])
