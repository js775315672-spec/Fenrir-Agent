# FENRIR · Independent Critical Reviewer

> **Development status:** DEMO_QWEN_EXECUTED / WAITING_AUTHENTICATED_O_HANDOFF  
> **Trust status:** FENRIR_VERIFIED=false · CERBERUS_GATE=BLOCKED  
> **Scope:** Independent reviewer prototype. This is **not** an approved review of an Ouroboros candidate.

## Development dashboard

| Gate / metric | Current evidence-backed state | Evidence |
|---|---|---|
| Repository / isolation | Dedicated `Fenrir-Agent` repo, Draft PR branch; not merged | [Draft PR #1](https://github.com/js775315672-spec/Fenrir-Agent/pull/1) |
| Contract CI | **PASS** in run #17 | [Run #17](https://github.com/js775315672-spec/Fenrir-Agent/actions/runs/44895880606) |
| Actual Qwen inference | **PASS — public demo only**, model `qwen2.5:0.5b` | [Run #17, qwen-demo-inference](https://github.com/js775315672-spec/Fenrir-Agent/actions/runs/44895880606) |
| FENRIR_REPORT artifact | **Created — demo only**; artifact ID `14704580154` | [Run #17 artifacts](https://github.com/js775315672-spec/Fenrir-Agent/actions/runs/44895880606) |
| GitHub provenance generation | **Step PASS**; independent attestation verification **not done** | [Run #17](https://github.com/js775315672-spec/Fenrir-Agent/actions/runs/44895880606) |
| Actual O candidate SHA-256 | **NOT VERIFIED** | [O ledger #347](https://github.com/js775315672-spec/Harness-Ouroboros-MCP/issues/347) |
| Authenticated independent F report for O | **NOT RECEIVED** | [O ledger #347](https://github.com/js775315672-spec/Harness-Ouroboros-MCP/issues/347) |
| Cerberus protected replay | **BLOCKED — not executed** | [C issue #2](https://github.com/js775315672-spec/Cerberus/issues/2) |
| LoRA / model weight updates | **NOT PERFORMED** | No training evidence |

**Current task key:** `ORIL-OFC-PR346-001:F_REPORT_CONTRACT`  
**Tracked cycle:** `ORIL-OFC-PR346-001`  
**Development branch:** `feat/independent-qwen-review-v0-1`  
**Evidence HEAD for successful demo:** `fd962c4a818e0b8f541daa92f41378725a8fd35c`  
**Candidate note:** the demo candidate's SHA-256 is distinct from O PR #346 and cannot be reused as the O candidate digest.

## Current blocker and next handoff

1. **OUROBOROS:** publish immutable actual candidate bytes and their verified SHA-256, source commit, input/experiment evidence and agreed test contract.
2. **FENRIR:** run the separately controlled Qwen reviewer on that exact candidate; bind the run to its artifact SHA, produce the full report and verify provenance **independently** (including anti-replay).
3. **CERBERUS:** only after a verified F report, conduct isolated tests on a protected holdout; keep its tests and answers unavailable to O and F.
4. Maintain atomic lease/owner and stop on duplicate or conflicting evidence. No automatic merge, protected gate changes or deployment.

**Fail-closed rule:** A green CI check, GitHub provenance generation, a self-declared run ID, or a demo report alone is not `FENRIR_VERIFIED=true`.

## Cycle improvement and speed trend

| Comparable metric (5–12 homogeneous real cycles) | Result |
|---|---|
| Comparable completed cycles / n | **Insufficient data / n=0 verified O→F→C cycles** |
| Median end-to-end time | Not measured |
| Median model time | Not measured across comparable cycles |
| Median independent verification time | Not measured |
| Median follow-up time | Not measured |
| Independently accepted improvements per hour | Not computable |
| Retry / failure / regression / rollback rates | Not computable |
| Protected holdout quality delta | Not measured |
| Cost per verified cycle | Not measured |
| Development acceleration vs previous comparable cycles | **Cannot determine** |

**Single demo run is not a trend.** The workflow's reported duration includes setup and download and must not be labeled pure inference latency. Do not confuse a passing contract test with model intelligence or weight improvement.

## Evidence / chronological checkpoints

| Checkpoint | Result | Interpretation |
|---|---|---|
| [Run #15](https://github.com/js775315672-spec/Fenrir-Agent/actions/runs/44895738082) | Contract PASS, Qwen job skipped | CI green did **not** imply inference |
| [Run #17](https://github.com/js775315672-spec/Fenrir-Agent/actions/runs/44895880606) | Contract PASS, Qwen demo job PASS, artifact uploaded, attestation step PASS | **First confirmed demo inference**, not O candidate review |
| [Artifact #14704580154](https://github.com/js775315672-spec/Fenrir-Agent/actions/runs/44895880606) | Demo ZIP digest `sha256:4e7d475c7f57435c7e8aeba7f919c697d24d07095abbeea7595de1c855e96239` | Digest of uploaded ZIP artifact, **not** O candidate SHA-256 |

Detailed machine-generated logs and artifacts belong in Actions; cross-project handoffs belong in [O issue #347](https://github.com/js775315672-spec/Harness-Ouroboros-MCP/issues/347) and [C issue #2](https://github.com/js775315672-spec/Cerberus/issues/2). The README is a **human-readable snapshot**, not a lock, an authenticated ledger, or an automatically updated status feed. Update this snapshot only from verified evidence; never mark scheduled work as complete merely because time passed.

## Running the prototype

Local Ollama with `qwen2.5:0.5b`:

```bash
python -m unittest discover -s tests -v
python -m fenrir.reviewer --input candidate.json --output out/FENRIR_REPORT.json
```

The input JSON requires `cycle_id`, `source_commit`, actual candidate artifact `candidate_sha256` and real HTTPS `evidence_urls`. Output includes model, input/prompt digests, report findings and a self-declared run ID. Output remains `UNVERIFIED` until trusted external provenance validation.

On the Draft PR branch, GitHub Actions additionally runs a **public demo** on `fixtures/demo_candidate.py`. This workflow does not access protected holdout data, cannot approve Cerberus, and does not use a paid API.

## Project links

- [Ouroboros shared ledger #347](https://github.com/js775315672-spec/Harness-Ouroboros-MCP/issues/347)
- [Fenrir Draft PR #1](https://github.com/js775315672-spec/Fenrir-Agent/pull/1)
- [Cerberus independent gate issue #2](https://github.com/js775315672-spec/Cerberus/issues/2)
