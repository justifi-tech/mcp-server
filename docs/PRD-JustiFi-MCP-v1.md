# Product Requirements Document (PRD)
JustiFi MCP Integration – v1.0  
Prepared by: AI Assistant | Date: 2025-01-15  

---

## 1. Purpose & Vision
Give Cursor & VS Code engineers instant, secure access to the **JustiFi** payments platform through our LangChain-powered MCP server.  
The assistant can create, list, retrieve, and refund payments by calling MCP tools that wrap the JustiFi REST API, eliminating context-switching and speeding up integration work.

---

## 2. Goals & Non-Goals
### 2.1 Goals (v1)
1. Expose **four core payment tools** (`create_payment`, `retrieve_payment`, `list_payments`, `refund_payment`).
2. Support **OAuth2 Client-Credentials** auth flow, with in-memory token caching.
3. Conform to project rules: async/await, `@traceable`, Docker-only, env-driven secrets.
4. Provide unit tests (mocked HTTP), README documentation, and example Cursor prompts.
5. Ship within one sprint (≤ 1 week).

### 2.2 Non-Goals (deferred)
• Auto-generate the entire API surface from OpenAPI.  
• Support advanced resources (sub-accounts, payouts, reports, webhooks).  
• Provide SSE/WebSocket streaming for long-running operations.  
• Production hosting / multi-tenant auth.

---

## 3. Background / References
• JustiFi OpenAPI spec: <https://docs.justifi.tech/redocusaurus/plugin-redoc-0.yaml>  
• OAuth Client-Credentials flow & idempotency requirements are documented in the spec ("Authenticate With JustiFi" and "Idempotent Requests").

---

## 4. User Stories
| As a … | I want to … | So that … |
| ---- | ------------ | ---------- |
| Backend engineer in Cursor | "Create a $10 test payment" via chat prompt | I can prototype billing flows without switching to Postman |
| QA engineer | Quickly refund a failed test charge from the IDE | I can reset state between tests |
| Engineering lead | List last 25 payments & statuses | I can see real-time progress during load testing |

---

## 5. Functional Requirements
### 5.1 MCP Tools
| Tool | Method / Endpoint | Required Args | Optional Args | Description |
| ---- | ---------------- | ------------- | ------------- | ----------- |
| `create_payment` | POST `/payments` | `amount_cents`, `currency`, `idempotency_key` | Any extra body fields allowed by API | Creates a charge. |
| `retrieve_payment` | GET `/payments/{payment_id}` | `payment_id` | – | Fetches payment object. |
| `list_payments` | GET `/payments` | – | `limit`, `after_cursor`, `before_cursor` | Paginates payments. |
| `refund_payment` | POST `/payments/{payment_id}/refunds` | `payment_id` | `amount_cents`, `idempotency_key` | Issues full or partial refund. |

### 5.2 Auth & Secrets
Env vars:  
```
JUSTIFI_CLIENT_ID
JUSTIFI_CLIENT_SECRET
JUSTIFI_BASE_URL   # default https://api.justifi.ai/v1
```  
Token cached for `expires_in – 60 s`.

### 5.3 Error Handling
| Scenario | Behavior |
| -------- | -------- |
| 4xx from JustiFi | Surface sanitized message; assistant retries only on 409 |
| 5xx / timeout | Raise `ToolExecutionError`; LangChain may retry |
| Missing env vars | Fail fast with clear error |

---

## 6. Non-Functional Requirements
| Category | Requirement |
| -------- | ----------- |
| Performance | Tool latency ≤ 2 s P95 |
| Security | Secrets via env; no logging secrets |
| Observability | All tools `@traceable` → LangSmith |
| Compliance | Pass pytest, flake8, bandit; Docker image size Δ < 30 MB |

---

## 7. Technical Design Overview
**File Structure:**  
```
tools/
  justifi.py        # new adapter
tests/
  test_justifi.py
docs/
  PRD-JustiFi-MCP-v1.md
```

**Helper Functions:**  
• `_get_access_token()` → caches `access_token` in module-level dataclass.  
• `_request()` → central HTTP wrapper (adds auth + idempotency header).  

**Language/Framework:**  
Python 3.11, httpx + asyncio, Pydantic for small models.

---

## 8. Success Metrics
1. 100% unit-test pass rate (≥ 90% adapter coverage).
2. Cursor demo: assistant successfully calls `create_payment`.
3. No new high-severity bandit findings.
4. Build-time increase < 5 s.

---

## 9. Milestones & Timeline
| Day | Task |
| --- | ---- |
| 0 | PRD approval |
| 1 | Env vars added, adapter stub |
| 2 | Token logic + `create_payment` + test |
| 3 | Remaining tools + tests |
| 4 | README, end-to-end Cursor demo |
| 5 | Code review & merge |

---

## 10. Risks & Mitigations
| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Token expiry loops | Failed calls | Cache offset; refresh on 401 |
| API spec drift | Breakage | Weekly CI smoke test |
| Rate limits | Latency | Capture 429, back-off (v1.1) |

---

## 11. Open Questions
1. Need sandbox vs live env switch?
2. Any must-have endpoints beyond payments for v1?
3. Auto-generate client now or keep hand-rolled?

---

## 12. Approval
**Stakeholders:**  
• Product Owner – `@Markkif` ✅  
• Tech Lead – TBD  
• Security – TBD  

**Status:** Approved for implementation 