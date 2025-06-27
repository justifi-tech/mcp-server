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
1. Add AI evaluation dependencies to `requirements.txt`:
   - `langchain` (for AI evaluation utilities)
   - `openai` (for AI agent testing)
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

Each JSONL row represents a **developer assistance scenario**:
```json
{
  "user_query": "Check the status of payment py_5A30RmJ3vLiYxqenOojQVW",
  "expected_tool": "retrieve_payment",
  "expected_params": { "payment_id": "py_5A30RmJ3vLiYxqenOojQVW" },
  "success_criteria": [
    "AI chooses retrieve_payment tool",
    "AI extracts payment ID correctly", 
    "AI explains payment status clearly",
    "AI provides helpful context about the payment"
  ],
  "meta": { "scenario": "Developer checking payment status", "complexity": "simple" }
}
```

**Key Design Decisions**:
- **Developer-Centric**: Real questions developers ask when integrating JustiFi
- **AI Behavior Testing**: Focus on tool selection, parameter extraction, communication quality
- **Real API Integration**: Uses actual JustiFi payment IDs for realistic AI responses
- **Regression Detection**: Stable scenarios that catch AI performance degradation

**WHY?** – Data-first approach lets reviewers validate AI evaluation criteria before implementation.

---

## 3. AI Agent Evaluation Harness (⚙️) — _PR #3_
Add `scripts/run-evals.py` that evaluates **real AI agent performance** for developer assistance:

### **Architecture: AI Agent + MCP Tools Integration**
```python
# Real AI agent evaluation using OpenAI function calling
import openai
from langsmith.wrappers import wrap_openai
from langsmith import traceable

client = wrap_openai(openai.Client())

@traceable
def evaluate_developer_assistant(user_query: str, expected_outcome: dict):
    """Test AI agent's ability to help developers with JustiFi integration."""
    
    # Define MCP tools as OpenAI functions
    tools = [
        {
            "type": "function",
            "function": {
                "name": "retrieve_payment",
                "description": "Get payment details by ID",
                "parameters": {
                    "type": "object",
                    "properties": {"payment_id": {"type": "string"}},
                    "required": ["payment_id"]
                }
            }
        },
        # ... other MCP tools
    ]
    
    system_prompt = """
    You are a JustiFi API expert helping developers integrate payments.
    Use the available tools to help developers understand, debug, and implement JustiFi payments.
    Always explain what you're doing and provide helpful context.
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        tools=tools,
        tool_choice="auto"
    )
    
    # When AI calls a tool, execute it via our MCP server
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            # Execute the actual MCP tool
            tool_result = await handle_call_tool(
                tool_call.function.name, 
                json.loads(tool_call.function.arguments)
            )
            # Continue conversation with tool results...
    
    return evaluate_ai_response(response, expected_outcome)
```

### **What This Architecture Tests**
1. **Tool Selection**: Does AI choose the right JustiFi operation for developer needs?
2. **Parameter Extraction**: Does AI correctly parse payment IDs, amounts, etc. from natural language?
3. **Developer Communication**: Does AI explain results clearly and provide helpful context?
4. **Error Handling**: How does AI help developers debug payment issues?
5. **Learning Support**: Does AI teach developers JustiFi best practices?

### **Integration Points**
- **Real MCP Tools**: AI calls actual `handle_call_tool()` functions
- **Real JustiFi API**: Tools make live API calls for realistic responses
- **LangSmith Tracing**: Full conversation and tool usage tracking
- **Developer Scenarios**: Test cases based on real developer workflows

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