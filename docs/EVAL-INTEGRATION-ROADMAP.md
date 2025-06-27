# JustiFi MCP – Eval Framework Roadmap  
_v1.0 • Pilot tool: `retrieve_payment`_

This document breaks the evaluation initiative into discrete, reviewable checkpoints.  
After each step you can pause, review, and approve before the next PR lands.

---

## 0. Prep  (📄 You are here)
* Commit this roadmap file.  
* **No code changes yet.**

**WHY?** – Establishes a shared plan & review gates before touching code.

---

## 1. Dependencies & Environment (🔧) — _PR #1_
1. Add `langchain-evaluate` to `requirements.txt`.
2. Extend **Makefile**:
   ```make
   eval: env-check
   	docker-compose run --rm dev python scripts/run-evals.py
   ```
3. Document that `LANGCHAIN_API_KEY` is *required* for evals.

**WHY?** – `langchain-evaluate` supplies ready-made evaluators and plugs into existing LangSmith tracing.

---

## 2. Datasets & Schemas (📁) — _PR #2_
```
eval/
  retrieve_payment.jsonl               # 10 canonical cases
schemas/
  retrieve_payment_response.schema.json
```
Each JSONL row:
```json
{
  "arguments": { "payment_id": "py_demo_123" },
  "expected":  { "id": "py_demo_123", "status": "succeeded", "amount": 1050 }
}
```

**WHY?** – Data-first lets reviewers validate business expectations before wiring code.

---

## 3. Eval Harness (⚙️) — _PR #3_
Add `scripts/run-evals.py`:
1. Launch MCP server (stdio) inside the dev container.
2. For each dataset row:
   * `call_tool("retrieve_payment", arguments)` via small `MCPClient` wrapper.
   * Measure latency.
   * Score with `JSONSchemaEvaluator(schema)`.
3. Aggregate metrics: `accuracy`, `p95_latency_ms`.
4. Log run to LangSmith (`project="JustiFi-MCP-Eval"`).
5. Exit non-zero if accuracy < 1 or latency SLO fails.

**WHY?** – Keeps evaluations outside pytest so unit tests stay fast and deterministic.

---

## 4. CI Workflow (🛠️) — _PR #4_
`.github/workflows/eval.yml`
```yaml
on:
  schedule:
    - cron: "0 4 * * *"   # nightly
  pull_request:
    paths:
      - "tools/**"
      - "main.py"
      - "eval/**"
      - "schemas/**"
      - "scripts/run-evals.py"

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: make eval
```
Workflow fails (and blocks merge) if `make eval` exits non-zero.

**WHY?** – Separate job gives clear status badge and avoids slowing unit-test job.

---

## 5. Dashboards & Docs (📊) — _PR #5_
1. Create LangSmith project **"JustiFi-MCP-Eval"**.
2. Add `docs/EVALS.md` explaining:
   * Viewing runs & filters.
   * Adding new datasets.
   * Tuning latency SLO.

**WHY?** – Provides long-term visibility for product & engineering.

---

## 6. Extend to More Tools (🚀) — _future PRs_
Repeat pattern:
1. Add `<tool>.jsonl` + schema.
2. Register evaluator in `run-evals.py`.
3. Update docs.

---

### Change-Control Checklist (for each PR)
* [ ] Code compiles (CI green)
* [ ] `make test` passes
* [ ] `make eval` passes (≥ step 3)
* [ ] Documentation updated

---

## Acceptance Criteria
1. `make eval` returns exit-code 0 with 100 % accuracy.
2. GitHub Action "Eval" job blocks merge on failure.
3. LangSmith dashboard shows nightly runs with trend lines.
4. Adding an intentionally failing dataset row breaks CI.

---

## Future Enhancements
* GPT-4 semantic evaluators for error-message quality.
* Synthetic dataset generation via `langchain_experimental`.
* Cost tracking when LLM evaluators are introduced.
* Auto-bisect Git commit that degrades eval metrics.

---

*End of roadmap – ready for PR #1 once this doc is merged.* 