# JustiFi MCP – AI Agent Evaluation Framework Roadmap  
_v1.1 • Focus: AI Performance & Decision-Making • Pilot tool: `retrieve_payment`_

## 🎯 **What We're Evaluating**

**This is NOT code testing** – we already have comprehensive unit tests for that.

**This IS AI agent evaluation** – ensuring the AI makes good decisions when using our MCP tools:
- ✅ **Tool Selection**: Does the AI choose the right MCP tool for user requests?
- ✅ **Parameter Extraction**: Does it correctly extract payment IDs, amounts, etc. from natural language?
- ✅ **Response Quality**: Does it present results clearly and helpfully to users?
- ✅ **Error Handling**: How gracefully does it handle API failures or edge cases?
- ✅ **Regression Detection**: Are we maintaining AI performance as we make changes?

**Why This Matters**: The MCP server code is small and stable. The real value (and risk) is in how AI agents use these tools in conversation with users.

---

This document breaks the AI evaluation initiative into discrete, reviewable checkpoints.  
After each step you can pause, review, and approve before the next PR lands.

---

## 0. Prep  (📄 You are here)
* Commit this roadmap file.  
* **No code changes yet.**

**WHY?** – Establishes a shared plan & review gates before touching code.

---

## 1. Dependencies & Environment (🔧) — _PR #1_
1. Add `langchain` to `requirements.txt` (for AI evaluation utilities).
2. Extend **Makefile**:
   ```make
   eval: env-check build-dev
   	@echo "📈 Running AI evaluation suite in dev container..."
   	docker-compose run --rm dev python scripts/run-evals.py
   ```
3. Document that `LANGCHAIN_API_KEY` is *optional* for LangSmith tracing.

**WHY?** – LangChain provides AI-focused evaluation tools and integrates with LangSmith for observability.

---

## 2. AI Evaluation Datasets & Schemas (📁) — _PR #2_
```
eval/
  retrieve_payment.jsonl               # Real user scenarios & expectations
schemas/
  retrieve_payment_response.schema.json # Expected AI response structure
```

Each JSONL row represents a **user interaction scenario**:
```json
{
  "arguments": { "payment_id": "py_5A30RmJ3vLiYxqenOojQVW" },
  "expected": { "id": "py_5A30RmJ3vLiYxqenOojQVW", "status": "succeeded", "amount": 4299, "currency": "usd" },
  "meta": { "description": "Real payment from JustiFi API - $42.99" }
}
```

**Key Design Decisions**:
- **Real API Data**: Uses actual JustiFi payment IDs so AI sees realistic response structures
- **User-Centric**: Focuses on what users care about (payment status, amounts, etc.)
- **Regression-Focused**: Stable test cases that detect AI performance degradation

**WHY?** – Data-first approach lets reviewers validate AI evaluation criteria before implementation.

---

## 3. AI Evaluation Harness (⚙️) — _PR #3_
Add `scripts/run-evals.py` that evaluates **AI agent performance**:

1. **Direct MCP Tool Testing**: Call `handle_call_tool()` directly (simulates AI agent calls)
2. **Real API Integration**: Uses live JustiFi API for realistic evaluation conditions
3. **AI-Focused Metrics**:
   * **Response Structure**: JSON schema validation of tool outputs
   * **Performance**: Latency measurements (affects user experience)
   * **Reliability**: Success rate across different scenarios
4. **Observability**: Optional LangSmith integration for debugging AI decisions
5. **CI Integration**: Exits non-zero if AI performance degrades

**What This Catches**:
- API response format changes that break AI understanding
- Performance regressions that hurt user experience  
- Edge cases where AI tools fail unexpectedly

**WHY?** – Separate from unit tests because AI evaluation requires real API data and different success criteria.

---

## 4. CI Workflow for AI Performance (🛠️) — _PR #4_
`.github/workflows/eval.yml` - **AI Performance Gate**
```yaml
name: "AI Agent Evaluation"
on:
  schedule:
    - cron: "0 4 * * *"   # nightly AI performance check
  pull_request:
    paths:
      - "tools/**"        # MCP tool changes
      - "main.py"         # Core server changes
      - "eval/**"         # Evaluation criteria updates
      - "schemas/**"      # Expected response changes

jobs:
  ai-eval:
    name: "Evaluate AI Agent Performance"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make eval
```

**Blocks merges if**:
- AI agent can't successfully use updated MCP tools
- Response latency degrades beyond acceptable thresholds
- API changes break AI understanding of responses

**WHY?** – Prevents shipping changes that degrade AI agent performance in production.

---

## 5. AI Performance Dashboards & Docs (📊) — _PR #5_
1. **LangSmith Project**: "JustiFi-MCP-AI-Eval" for tracking AI performance trends
2. Add `docs/AI-EVALUATION.md` explaining:
   * How to interpret AI performance metrics
   * Adding new user scenarios to evaluation datasets
   * Debugging AI decision-making issues
   * Understanding AI performance trends over time

**WHY?** – Provides visibility into AI agent performance for product & engineering teams.

---

## 6. Expand AI Evaluation Coverage (🚀) — _future PRs_
Extend to more MCP tools and user scenarios:
1. Add `create_payment.jsonl` - test AI parameter extraction from natural language
2. Add `refund_payment.jsonl` - test AI handling of complex refund scenarios  
3. Add conversation-level evaluations - test multi-turn AI interactions
4. Add error scenario datasets - test AI graceful failure handling

---

### Change-Control Checklist (for each PR)
* [ ] Code compiles (CI green)
* [ ] `make test` passes (unit tests still work)
* [ ] `make eval` passes (AI performance maintained)
* [ ] AI evaluation documentation updated

---

## Success Criteria - AI Agent Performance
1. **Baseline Performance**: `make eval` achieves 100% success rate on current scenarios
2. **Regression Prevention**: GitHub Action blocks merges that degrade AI performance
3. **Observability**: LangSmith dashboard shows AI performance trends over time
4. **Validation**: Intentionally breaking AI scenarios fails CI as expected

---

## Future AI Evaluation Enhancements
* **Conversation-Level Evaluation**: Multi-turn AI interactions with context
* **Natural Language Input Testing**: "Refund $25 from last Tuesday's payment"
* **AI Error Message Quality**: Semantic evaluation of how AI explains failures
* **Prompt Engineering Validation**: A/B testing different AI instructions
* **Cost & Performance Optimization**: Track AI decision-making efficiency

---

*End of roadmap – This focuses on AI agent performance, not MCP server code quality.* 
*Ready for PR #1 once this doc is merged.* 