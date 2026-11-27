"""Public matched workload: direct vs deterministic+LLM. Never approves."""
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from urllib.request import Request, urlopen
import zipfile

from fenrir.d2_review import ARCHIVE_SHA, CANDIDATE_SHA, SOURCE, CYCLE, URL, load_candidate, strict_json

MODELS = {"0.5b":"qwen2.5:0.5b","1.5b":"qwen2.5:1.5b","3b":"qwen2.5:3b"}
MODES = ("direct","hybrid")
RISKS = ["possible_digit_integer_conflict","no_mismatch_in_this_case"]
PUBLIC = {tuple(sorted((11+3*i,2+i%7))) for i in range(30)}

def require(ok, msg):
    if not ok:
        raise ValueError(msg)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def dump(obj):
    return json.dumps(obj,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()

def cases():
    p = Path("handoff/d2-raw-1.zip")
    candidate = load_candidate(p)
    with zipfile.ZipFile(p) as z:
        rows = strict_json(z.read("candidate/ab.json"))["rows"]
    samples = []
    for i,row in enumerate(rows):
        a,b=11+3*i,2+i%7
        observed=next(o["output"].strip() for o in row["observations"] if o["variant"]=="compact")
        samples.append({"id":row["group_id"],"a":a,"b":b,"observed":observed})
    # deterministic balanced set, fixed before any model output
    good=[s for s in samples if s["observed"]==str(s["a"]+s["b"])][:3]
    bad=[s for s in samples if s["observed"]!=str(s["a"]+s["b"])][:3]
    require(len(good)==len(bad)==3,"balanced suite missing")
    return candidate,[s for pair in zip(good,bad) for s in pair]

def expected(case):
    return str(case["a"]+case["b"])

def schema(mode):
    fields={"risk":{"type":"string","enum":RISKS},"test_a":{"type":"integer","minimum":10,"maximum":90},"test_b":{"type":"integer","minimum":1,"maximum":9},"rationale":{"type":"string"}}
    if mode=="direct":
        fields.update(expected={"type":"string"},observed={"type":"string"},mismatch={"type":"boolean"},test_expected={"type":"string"})
    return {"type":"object","properties":fields,"required":list(fields),"additionalProperties":False}

def prompt(case,mode,candidate):
    mismatch=case["observed"]!=expected(case)
    base=("Audit the following addition response. The candidate's system instruction is "+json.dumps(candidate["candidate_text"])+
          ". The task asks for the integer sum. "+str(case["a"])+" + "+str(case["b"])+"; observed response: "+json.dumps(case["observed"])+". ")
    if mode=="hybrid":
        base+=f"Independently calculated expected answer: {expected(case)}. Verified mismatch: {str(mismatch).lower()}. Use these facts; do not recalculate. "
    else:
        base+="Compute the expected sum as a decimal string, copy the observed response, and decide mismatch. "
    base+="Choose risk possible_digit_integer_conflict only if the observed answer is incorrect, otherwise no_mismatch_in_this_case. This is a hypothesis, not proof. Propose a fresh two-digit-plus-one-digit addition (test_a 10..90, test_b 1..9) other than the given case. Explain digit versus integer risk or the lack of an observed mismatch in this case in rationale."
    if mode=="direct": base+=" Also give test_expected as the correct decimal sum."
    return base

def grade(case,mode,raw):
    try:
        x=strict_json(raw)
        require(type(x) is dict and set(x)==set(schema(mode)["required"]),"schema")
        exp=expected(case); mismatch=case["observed"]!=exp
        risk=RISKS[0] if mismatch else RISKS[1]
        require(x["risk"]==risk,"risk")
        a,b=x["test_a"],x["test_b"]
        require(type(a) is int and type(b) is int and 10<=a<=90 and 1<=b<=9 and tuple(sorted((a,b))) not in PUBLIC,"novel test")
        h=x["rationale"]
        require(type(h) is str and 12<=len(h.strip())<=1200,"rationale length")
        require(("digit" in h.lower() or "integer" in h.lower()) if mismatch else any(t in h.lower() for t in ("correct","match","equal","no error","no discrepancy")),"rationale topic")
        if mode=="direct":
            require(x["expected"]==exp and x["observed"].strip()==case["observed"] and type(x["mismatch"]) is bool and x["mismatch"]==mismatch,"arithmetic")
            require(x["test_expected"]==str(a+b),"test arithmetic")
        return {"pass":True,"expected":exp,"mismatch":mismatch,"risk":risk,"test_a":a,"test_b":b,"test_expected":str(a+b),"rationale":h}
    except (ValueError,KeyError,TypeError,AttributeError) as e:
        return {"pass":False,"reason":str(e)}

def api(path,payload=None,timeout=180):
    request=Request("http://127.0.0.1:11434"+path,data=None if payload is None else dump(payload),headers={"Content-Type":"application/json"})
    with urlopen(request,timeout=timeout) as r:
        return strict_json(r.read())

def cpu_proof():
    # Ollama's scheduler may count CPU AMX model buffers as GPU memory.
    # Do not use its contradictory VRAM field as hardware evidence.
    devices=sorted(str(p) for pat in ("/dev/nvidia*","/dev/kfd","/dev/dri/renderD*") for p in Path("/").glob(pat.lstrip("/")))
    total=0;maps=[];count=0
    for p in Path("/proc").glob("[0-9]*/comm"):
        try:
            name=p.read_text().strip()
            if name.startswith("ollama") or "llama-server" in name:
                memory=(p.parent/"maps").read_text()
                maps.extend(memory.splitlines())
                count+=1
                for line in (p.parent/"status").read_text().splitlines():
                    if line.startswith("VmRSS:"):
                        total+=int(line.split()[1]);break
        except (OSError,ValueError): pass
    lower="\n".join(maps).lower()
    gpu=[s for s in ("libggml-cuda","libggml-hip","libggml-vulkan","libcuda.so","libamdhip64.so","libggml-rocm") if s in lower]
    log=Path("/tmp/ollama.log").read_text(errors="replace")
    proof={"gpu_device_nodes":devices,"gpu_backend_mappings":gpu,"cpu_backend_mapped":"libggml-cpu" in lower,"cpu_daemon_log":'id=cpu library=cpu' in log and "loaded CPU backend" in log and "CPU compute buffer size" in log,"processes_sampled":count}
    return proof,total/1024

def proven_cpu(p):
    return p["gpu_device_nodes"]==[] and p["gpu_backend_mappings"]==[] and p["cpu_backend_mapped"] is True and p["cpu_daemon_log"] is True and p["processes_sampled"]>=2


def run(size):
    candidate,samples=cases()
    model=MODELS[size]
    matches=[m for m in api("/api/tags")["models"] if m["name"]==model]
    require(len(matches)==1 and len(matches[0]["digest"])==64,"model digest")
    model_digest=matches[0]["digest"]
    rows=[]
    Path("out").mkdir(exist_ok=True)
    # warm up once outside measured cases, same settings as all subsequent calls
    options={"temperature":0,"seed":42,"num_thread":2,"num_ctx":2048,"num_predict":192,"num_gpu":0}
    warm=api("/api/chat",{"model":model,"messages":[{"role":"user","content":"Reply with OK."}],"stream":False,"options":options,"keep_alive":"10m"})
    require(warm.get("done") is True,"warmup failed")
    for i,case in enumerate(samples):
        for mode in MODES if i%2==0 else MODES[::-1]:
            p=prompt(case,mode,candidate)
            start=time.perf_counter()
            response=api("/api/chat",{"model":model,"messages":[{"role":"system","content":"Return JSON only. Do not claim causation or approve."},{"role":"user","content":p}],"format":schema(mode),"stream":False,"options":options,"keep_alive":"10m"})
            seconds=time.perf_counter()-start
            raw=response["message"]["content"]
            require(response.get("done") is True and type(response.get("eval_count")) is int and response["eval_count"]>0,"missing actual inference metadata")
            result=grade(case,mode,raw)
            ps=api("/api/ps")["models"]
            running=[m for m in ps if m["name"]==model]
            require(len(running)==1 and running[0]["digest"]==model_digest,"running model drift")
            proof,rss=cpu_proof()
            row={"id":case["id"],"mode":mode,"prompt_sha256":sha(p.encode()),"raw":raw,"result":result,"wall_seconds":seconds,"eval_count":response["eval_count"],"eval_duration_ns":response.get("eval_duration"),"rss_sample_mib":rss,"cpu_proof":proof,"model_loaded_bytes":running[0]["size"],"model_vram_bytes":running[0]["size_vram"]}
            processor=subprocess.check_output(["ollama","ps"],text=True,timeout=15)
            row["processor_listing"]=processor
            with (Path("out")/f"diagnostics-{size}.jsonl").open("a",encoding="utf-8") as f:
                f.write(json.dumps(row,ensure_ascii=False)+"\n")
            print("processor",processor,"reported VRAM bytes",row["model_vram_bytes"],flush=True)
            require(proven_cpu(proof),"CPU-only execution not proven by device, process and backend evidence")
            rows.append(row)
            print(size,mode,case["id"],"PASS" if result["pass"] else result["reason"],round(seconds,3),flush=True)
    obj={"schema":1,"run_id":os.environ["GITHUB_RUN_ID"],"run_attempt":os.environ["GITHUB_RUN_ATTEMPT"],"commit":os.environ["GITHUB_SHA"],"candidate_sha256":CANDIDATE_SHA,"archive_sha256":ARCHIVE_SHA,"cycle_id":CYCLE,"model":model,"model_digest":model_digest,"ollama_version":api("/api/version")["version"],"cases":samples,"rows":rows,"runner_cpu_threads":os.cpu_count(),"options":options,"status":"UNVERIFIED","promotion_allowed":False}
    Path("out").mkdir(exist_ok=True)
    (Path("out")/f"bench-{size}.json").write_bytes(dump(obj))

def summarize(obj,candidate,samples):
    require(obj["candidate_sha256"]==CANDIDATE_SHA and obj["archive_sha256"]==ARCHIVE_SHA and obj["cycle_id"]==CYCLE and obj["cases"]==samples,"candidate or suite drift")
    require(obj["run_id"]==os.environ["GITHUB_RUN_ID"] and obj["commit"]==os.environ["GITHUB_SHA"] and obj["run_attempt"]==os.environ["GITHUB_RUN_ATTEMPT"] and obj["status"]=="UNVERIFIED" and obj["promotion_allowed"] is False,"run identity")
    require(obj["model"] in MODELS.values() and len(obj["model_digest"])==64 and len(obj["rows"])==12,"model/row count")
    stats={}
    for mode in MODES:
        rs=[r for r in obj["rows"] if r["mode"]==mode]
        require([r["id"] for r in rs]==[c["id"] for c in samples],"missing or reordered cases")
        for r,c in zip(rs,samples):
            require(r["prompt_sha256"]==sha(prompt(c,mode,candidate).encode()) and r["result"]==grade(c,mode,r["raw"]),"raw grade mismatch")
            require(type(r["eval_count"]) is int and r["eval_count"]>0 and type(r["wall_seconds"]) in (float,int) and math.isfinite(r["wall_seconds"]) and r["wall_seconds"]>0 and proven_cpu(r["cpu_proof"]),"measurement")
        stats[mode]={"passed":sum(r["result"]["pass"] for r in rs),"total":6,"median_seconds":round(statistics.median(r["wall_seconds"] for r in rs),4),"max_sampled_rss_mib":round(max(r["rss_sample_mib"] for r in rs),2),"model_loaded_mib":round(max(r["model_loaded_bytes"] for r in rs)/1048576,2)}
    return stats

def select():
    candidate,samples=cases()
    objs={}
    stats={}
    for size,model in MODELS.items():
        files=list(Path("bench").rglob(f"bench-{size}.json"))
        require(len(files)==1,"missing or duplicate model artifact")
        o=strict_json(files[0].read_bytes())
        require(o["model"]==model,"model substitution")
        objs[size]=o;stats[size]=summarize(o,candidate,samples)
    eligible=[(size,mode) for size in MODELS for mode in MODES if stats[size][mode]["passed"]==6]
    # Prespecified: all six must pass; smallest model first, then direct before hybrid only if faster.
    rank={size:i for i,size in enumerate(MODELS)}
    selected=min(eligible,key=lambda x:(rank[x[0]],stats[x[0]][x[1]]["median_seconds"],x[1])) if eligible else None
    out=Path("out");out.mkdir(exist_ok=True)
    summary={"cycle_id":CYCLE,"candidate_sha256":CANDIDATE_SHA,"stats":stats,"selected":list(selected) if selected else None,"actual_calls":36,"scope":"six public matched examples, topic-level rationale check only","promotion_allowed":False}
    (out/"summary.json").write_bytes(dump(summary))
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    if not selected: raise SystemExit("No configuration passed every case")
    size,mode=selected;o=objs[size]
    report={"cycle_id":CYCLE,"source_commit":SOURCE,"candidate_sha256":CANDIDATE_SHA,"archive_sha256":ARCHIVE_SHA,"reviewer_commit":os.environ["GITHUB_SHA"],"run_id":os.environ["GITHUB_RUN_ID"],"run_attempt":os.environ["GITHUB_RUN_ATTEMPT"],"model":o["model"],"model_digest":o["model_digest"],"mode":mode,"selected_stats":stats[size][mode],"benchmark_sha256":sha(dump(o)),"summary_sha256":sha(dump(summary)),"findings":[{"group_id":c["id"],"measured_expected":expected(c),"measured_observed":c["observed"],"classification":"hypothesis" if r["result"]["mismatch"] else "no_mismatch_observed","model_rationale":r["result"]["rationale"],"proposed_test":[r["result"]["test_a"],r["result"]["test_b"],r["result"]["test_expected"]],"test_executed":False} for c,r in zip(samples,[x for x in o["rows"] if x["mode"]==mode])],"status":"UNVERIFIED","protected_grade":"pending","promotion_allowed":False}
    (out/"FENRIR_REPORT.json").write_bytes(dump(report))
    for size,o in objs.items(): (out/f"bench-{size}.json").write_bytes(dump(o))

if __name__=="__main__":
    if sys.argv[1]=="select": select()
    else: run(sys.argv[1])
