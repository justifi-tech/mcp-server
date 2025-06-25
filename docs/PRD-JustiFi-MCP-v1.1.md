# Product Requirements Document (PRD)
JustiFi MCP Integration – v1.1 "Payments +"  
Prepared by: AI Assistant | Date: 2025-01-25  

---

## 1. Purpose & Vision  
Expand the existing MCP server beyond core payments so engineers can manage **payment methods, payouts, balances, refunds list, and webhook endpoints** without ever leaving Cursor / VS Code.  

---

## 2. Goals & Non-Goals  
### 2.1 Goals (v1.1)  
1. Add **six new resource families** exposed as MCP tools:  
   • Payment Methods – create, retrieve, list  
   • Refunds List – list refunds for a payment  
   • Balances – retrieve current balance  
   • Payouts – retrieve, list 
   • Webhook Endpoints – list endpoints  
2. Maintain existing standards: async/await, `@traceable`, Docker-only, OAuth2 client-credentials with in-memory caching.  
3. ≥ 90 % unit-test coverage across new code.  
4. Weekly CI job detects OpenAPI spec drift.  
5. Ship within four dev-days.

### 2.2 Non-Goals (deferred)  
• Sub-accounts, disputes, reports, file uploads.  
• SSE/WebSocket streaming.  
• Multi-tenant hosting.

---

## 3. Background / References  
• JustiFi OpenAPI spec – <https://docs.justifi.tech/redocusaurus/plugin-redoc-0.yaml>  
• OAuth2 Client-Credentials flow ("Authenticate With JustiFi").  

---

## 4. User Stories  
| As a … | I want to … | So that … |  
| --- | --- | --- |  
| Front-end engineer | Create a new **payment method** for a customer | I can save cards during checkout prototype |  
| Ops engineer | View **pending payouts** | I know which funds will settle today |  
| Finance lead | Download **balance snapshot** | I can reconcile daily totals |  

---

## 5. Functional Requirements  
### 5.1 MCP Tools  
| Tool | Method / Endpoint | Required Args | Optional Args | Description |  
| ---- | ---------------- | ------------- | ------------- | ----------- |  
| `create_payment_method` | POST `/payment_methods` | `customer_id`, payment-method body fields | – | Store a new card/bank account. |  
| `retrieve_payment_method` | GET `/payment_methods/{id}` | `payment_method_id` | – | Fetch payment-method object. |  
| `list_payment_methods` | GET `/payment_methods` | – | `limit`, `after_cursor`, `before_cursor` | List customer payment methods. |  
| `list_refunds` | GET `/payments/{payment_id}/refunds` | `payment_id` | `limit`, cursors | List refunds for a payment. |  
| `retrieve_balance` | GET `/balances` | – | – | Get current available & pending balance. |  
  
| `retrieve_payout` | GET `/payouts/{id}` | `payout_id` | – | Fetch payout details. |  
| `list_payouts` | GET `/payouts` | – | `limit`, cursors | Paginate payouts. |  
| `list_webhook_endpoints` | GET `/webhook_endpoints` | – | – | Show configured webhook URLs. |  

### 5.2 Auth & Secrets  
Environment variables remain unchanged:  
```
JUSTIFI_CLIENT_ID
JUSTIFI_CLIENT_SECRET
JUSTIFI_BASE_URL   # default https://api.justifi.ai/v1
```  
Token cached until `expires_in – 60 s`.

### 5.3 Error Handling  
Identical strategy to v1.0; additionally:  
| Scenario | Behaviour |  
| -------- | --------- |  
| 401 Unauthorized | Refresh token once, retry |  
| 409 Conflict | Surface message, do not auto-retry |  

---

## 6. Non-Functional Requirements  
| Category | Requirement |  
| -------- | ----------- |  
| Performance | P95 tool latency ≤ 2 s |  
| Security | Zero-trust env vars, no secret logging |  
| Observability | All new tools `@traceable` → LangSmith |  
| Compliance | Pass pytest, flake8, bandit; image size Δ < 30 MB |  

---

## 7. Technical Design Overview  
```
tools/justifi/
  core.py              # _get_access_token, _request
  payments.py          # existing
  payment_methods.py   # NEW
  payouts.py           # NEW
  balances.py          # NEW
  webhooks.py          # NEW
schemas/               # Generated Pydantic models (datamodel-code-generator)
tests/                 # Split per resource file
docs/
  PRD-JustiFi-MCP-v1.1.md
```
• Use `datamodel-code-generator` to generate models from the OpenAPI spec → accurate JSON Schemas for `Tool` definitions.  
• Replace if/elif in `main.py` with a dispatch dict for scalability.  
• On 401, `_request` refreshes token and retries once.

---

## 8. Success Metrics  
1. 100 % unit-tests pass, ≥ 90 % coverage.  
2. Cursor demo exercises every new tool.  
3. CI drift job green (spec unchanged) for two consecutive weeks.  
4. No new high-severity bandit findings.

---

## 9. Milestones & Timeline  
| Day | Task |  
| --- | ---- |  
| 0.5 | Groundwork: download spec, endpoint inventory |  
| 1 | Scope lock & PRD approval |  
| 1.5 | Generate schemas, set up module scaffolding |  
| 2-3 | Implement tools + tests |  
| 3.5 | Docs, examples, CI drift job |  
| 4 | QA, container build, release tag `v1.1` |  

---

## 10. Risks & Mitigations  
| Risk | Impact | Mitigation |  
| ---- | ------ | ---------- |  
| API spec drift | Breakage | Weekly CI diff job |  
| Multiple replicas refreshing tokens | Duplicate refresh | Optionally share token via Redis (v1.2) |  
| Payout failures (async) | Confusing status | Add polling example in docs |  

---

## 11. Open Questions  
1. Should we auto-generate **all** endpoints in a future major version?  
2. Need sandbox/live env flag or separate containers?  
3. Do we expose webhook-endpoint creation or keep read-only?  

---

## 12. Approval  
**Stakeholders:**  
• Product Owner – `@Markkif`  
• Tech Lead – TBD  
• Security – TBD  

**Status:** Draft – pending review 