# Fenrir-Agent

## OFC DEV 12-cycle expansion (unverified)

- Scope: isolated DEV branch only; no OPS registry, main merge, holdout or protected edits.
- Runner: `agent/dev_cycle_12.py` (maximum 12 sequential candidate/verifier command pairs, wall-clock budget, atomic local checkpoint, stable operation keys).
- Safety: ambiguous pending blocks replay; failure stops the track; independent command exit 0 is **not** evidence of model intelligence improvement.
- Tests: `tests/test_dev_cycle_12.py`; Windows/Linux workflow `.github/workflows/ofc-dev-12-cycle.yml`.
- Evidence: this Draft PR and its head SHA / Actions checks. Current CI outcome: UNKNOWN until completed. Real Qwen runs: NOT_RUN. Protected independent evaluation: NOT_RUN. OPS cycle IDs: UNKNOWN.
- Limitations: no actual Qwen orchestration or artifact-backed independent evaluation; monetary cost cannot be enforced by this runner, so use only approved zero-cost commands. The runner must not be used for external side effects until operation reconciliation and source provenance gates are verified.
- Next single action: validate Windows/Linux regression and independently audit pending/restart behavior before enabling any real candidate commands.


## OFC D-plan: adaptive 120-cycle DEV planner (verification pending)

- A gate: 12-cycle Linux/Windows safety CI passed on the pre-expansion PR head. This is **not** proof of independent model improvement.
- B DEV files: `agent/adaptive_dev_120.py`, `tests/test_adaptive_dev_120.py`, `.github/workflows/ofc-dev-120-cycle.yml`. Maximum 10 batches × 12 cycles, stable keys, fail-closed pending, bounded budget counters, and independent-evaluation receipt fields.
- Status: planner committed to this independent Draft PR; new 120-cycle Windows/Linux CI must pass before promotion. The code is a **planner/receipt ledger**, not an external model executor or trusted evaluator. It does not automatically enforce third-party spending or cryptographically authenticate evaluator evidence.
- C gate: real approved free Qwen calls NOT_RUN; model hash, candidate SHA, evaluator SHA, actual run ID, artifact digest and independent holdout evaluation remain UNKNOWN/NOT_RUN. No OPS lease acquired; no main/protected/registry writes.
- Next single action: verify 120-cycle CI and harden evidence authentication and real-cost metering before any Qwen execution.


## OFC A-gate 120-cycle CI evidence — 2026-11-23

- Verification target before this documentation commit: `dcc723b7da0ca3a65cf5b644c684cf3995237d99` (Draft PR, DEV-only).
- Workflow: `OFC DEV 120-cycle planner safety`; run: https://github.com/js775315672-spec/Fenrir-Agent/actions/runs/45047641693.
- Linux: **QUEUED**; Windows: **QUEUED** at inspection time. Do not treat queued as passed or failed.
- A-gate: **BLOCKED pending both operating systems**.
- Evidence limitations: test suite checks deterministic planner bounds, pending replay block, independent-agent ledger separation, fail-closed receipts and budget counters. It does not prove real Qwen inference, authenticated evaluation artifacts, real spend enforcement, or intelligence gains.
- New README commit changes PR head: verify the new head separately before final gate promotion.
- OPS registry / PROTECTED / main: unchanged. No automatic merge.

### OFC C-gate read-only artifact verification (2026-11-23)
- DEV-only: `agent/github_artifact_evidence.py` fetches GitHub run and artifact metadata using a separately provided read-only token; verifies repository, exact head SHA, successful completed run, artifact binding, expiry and SHA-256 of downloaded ZIP (50 MB limit).
- Windows/Linux test: `tests/test_github_artifact_evidence.py` (mock transport). The workflow executes both planner and provenance tests. A mocked PASS is **not** a live authenticated artifact verification.
- **BLOCKED** until the newest CI for this exact README head passes on both OSes, a real artifact is available and independently authenticated, lease and zero-cost provider are verified. No real Qwen calls, independent improvements, or operational cycles are claimed.


### OFC P0 live audit snapshot (2026-11-23)
- Inspected pre-documentation DEV head: `a964b0b7a4654eec537f6f906cd67e3e4f9581a0`; P0 Actions run: https://github.com/js775315672-spec/Fenrir-Agent/actions/runs/45048554933.
- Observed at audit: Windows regression and Ubuntu CAS running; other jobs queued; no artifact.
- Final `verify-live-artifacts` job: NOT_PASSED / not yet executed. P0 overall BLOCKED; no new Qwen invocation, independent improvement, or verified operational cycle.
- Snapshot only: this README commit changes the DEV head and requires fresh head-bound CI; do not promote previous-run evidence as current-head PASS. main, OPS, PROTECTED and automations unchanged.
