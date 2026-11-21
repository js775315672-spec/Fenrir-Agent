# Fenrir-Agent

Independent Qwen critic prototype for Ouroboros → Fenrir → Cerberus.

**Status: CONTRACT PROTOTYPE / WAITING_AUTHENTICATED_FENRIR.** Separate repository and GitHub CI do not prove independent agent identity.

## Local use
Install Ollama locally, pull `qwen2.5:0.5b`, and start the local server. Then run:

```sh
python -m unittest discover -s tests -v
python -m fenrir.reviewer --input candidate.json --output out/FENRIR_REPORT.json
```

Candidate JSON must contain `cycle_id`, `source_commit`, actual candidate artifact `candidate_sha256` (64 lowercase hex characters), and real HTTPS `evidence_urls`. A Git commit SHA is **not** an artifact SHA-256.

The runner calls the local Ollama Qwen chat API and writes a structured report with finding ID, severity, confirmed/hypothesis, reproduction, attack test, pass/fail criteria and evidence URLs. Output status is always `UNVERIFIED`. The run ID is self-declared and **not** an authenticated identity proof. CI only executes Python contract tests; it does not run Qwen.

## Outstanding gates
- Immutable O artifact digest, input provenance and reproducible model run
- Independently verified GitHub Actions attestation or equivalent trusted identity
- Signed artifact verification, nonce/replay defense and independent report validation
- Protected Cerberus replay only after F provenance and report contract PASS

No secrets, private holdout, paid API, automatic merging, or deployment. This is a public repository.

Shared cycle `ORIL-OFC-PR346-001`; task `ORIL-OFC-PR346-001:F_REPORT_CONTRACT`.

Ledger: https://github.com/js775315672-spec/Harness-Ouroboros-MCP/issues/347

Cerberus gate: https://github.com/js775315672-spec/Cerberus/issues/2

## GitHub-hosted Qwen demo (Draft PR branch only)

A branch **push** starts `qwen-demo-inference` on a separate GitHub-hosted Ubuntu runner. It installs local Ollama, downloads `qwen2.5:0.5b`, executes actual model inference against a **public demonstration file** (`fixtures/demo_candidate.py`), validates the output and uploads `FENRIR_REPORT.json` and its SHA-256. If the job succeeds, `actions/attest-build-provenance@v2` attempts to issue a GitHub provenance attestation for the report file. The workflow has no write permission to repository contents and never merges or deploys.

**Important limitations:** This is *not* a review of the actual Ouroboros PR #346. The demo cycle ID is deliberately distinct. The GitHub attestation identifies the GitHub workflow/run that generated the bytes; it does not prove model independence, reviewer quality, or that a candidate was supplied through a trusted channel. Attestation verification, authenticated O artifact ingestion, replay prevention, and Cerberus protected holdout remain blocked. The report is always `UNVERIFIED`.

Review the Actions run and artifact before interpreting any status; installing Ollama or downloading model weights can fail on hosted runners. No protected evaluation data is sent to this public workflow.
