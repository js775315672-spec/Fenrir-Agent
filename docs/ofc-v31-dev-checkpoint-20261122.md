# Fenrir independent red-team DEV dashboard — OFC v3.1

Scope: DEV only. Base main SHA: `b1454fc9bab573b7018103cce35e9a443b68dfd4`. Fenrir is an independent adversarial research and falsification agent, not a persona within Ouroboros or Cerberus. Its own experiments, registry, memory, metrics and verdicts remain separate.

## Falsifiable hypothesis
A recovery mechanism may report success after two simultaneous writers race for the same generation, creating duplicate success receipts. Test a real remote Git CAS race; a local mock is insufficient.

## Red-team cases (planned, not run)
- F-01: two concurrent acquisitions from the same source and generation; no double success.
- F-02: stale owner attempts record/checkpoint after fenced recovery; reject.
- F-03: source drift between read and write; reject without destroying existing results.
- F-04: truncated, replayed, or forged execution artifact; fail provenance validation.
- F-05: Windows CRLF tree path; avoid false conflict and record exact reproduction.

## Dashboard
| Metric | Current evidence |
| --- | --- |
| Verified independent attack runs | UNKNOWN |
| Confirmed reproducible findings | UNKNOWN |
| False-positive rate | null — no comparable labeled cases |
| Unique ledger cycles | UNKNOWN — full ledger not audited |
| Median runtime, last 5–12 comparable runs | null — insufficient samples |
| Qwen/model calls | NOT_RUN in this checkpoint |
| Independent evaluation PASS | NOT_RUN in this checkpoint |
| OPS lease | NOT_ACQUIRED in this checkpoint |

Review target: https://github.com/js775315672-spec/Fenrir-Agent/pull/8

Every F-ID requires exact target SHA, runner URL, reproduction commands, expected/observed results, severity, and artifact digest. Do not mark a hypothetical failure as confirmed. Next single action: implement and execute F-01 remote CAS competition on #8 exact HEAD. No main/OPS changes.
