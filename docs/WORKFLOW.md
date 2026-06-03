# FinOps Guardian: Workflow & System Architecture

This document outlines the execution model, routing mechanics, agent contracts, and safety policies that power the **FinOps Guardian** platform.

---

## 🏗️ High-Level System Architecture

FinOps Guardian operates as a **safe, read-only control-plane audit ledger**. It does not perform active mutations (e.g. executing bank transfers, issuing payouts, or altering database balances) and maintains a strict separation between automation policy and human sign-off.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client/MCP Interface
    participant Orch as Ops Orchestrator Agent
    participant PM as Payment Ops Monitor
    participant BG as Billing Ops Guardian
    participant SI as Support Ops Intelligence
    participant Safety as Audit & Safety Agent
    database Ledger as Audit Ledger

    Client->>Orch: Ingest Batch of Operational Events (JSON)
    activate Orch
    Note over Orch: Routes events deterministically based on Event Type
    Orch->>PM: Route payment_tasks
    Orch->>BG: Route billing_tasks
    Orch->>SI: Route support_tasks
    deactivate Orch

    activate PM
    PM->>PM: Run transaction scans
    PM-->>Safety: Yield Payment Findings (e.g. duplicate payments, delay)
    deactivate PM

    activate BG
    BG->>BG: Run invoice discrepancies scans
    BG-->>Safety: Yield Billing Findings (e.g. incorrect charges)
    deactivate BG

    activate SI
    SI->>SI: Cluster tickets & identify downtime
    SI-->>Safety: Yield Support Findings (e.g. Bank API failure)
    deactivate SI

    activate Safety
    Note over Safety: Apply safety policies & compliance rules
    Safety->>Ledger: Write Audit Record (APPROVED or ESCALATE_TO_HUMAN)
    Safety-->>Client: Return Decisions & Action Recommends
    deactivate Safety
```

---

## ⚙️ Core Agent Execution & Routing Policies

### 1. Ops Orchestrator Agent
- **Responsibility**: Ingest event arrays, validate schemas, and perform **deterministic routing** (zero LLM reasoning in the routing layer to eliminate routing errors).
- **Queues**:
  - `payment_tasks` (for event type `payment`)
  - `billing_tasks` (for event type `billing`)
  - `support_tasks` (for event type `support`)

### 2. Payment Ops Monitor Agent
Analyzes transactions, gateway codes, and processing latencies.
- **Rules**:
  - **FAILED_PAYMENT**: Triggers if transaction status is `failed`. (High Severity)
  - **DELAYED_PAYMENT**: Triggers if processing latency $> 30$ seconds. (Medium Severity)
  - **DUPLICATE_PAYMENT**: Triggers if the same `transaction_id` appears multiple times within a short time-window. (High Severity)

### 3. Billing Ops Guardian Agent
Checks invoices and usage caps to prevent billing leaks and incorrect billing of customers.
- **Rules**:
  - **BILLING_MISMATCH**: Triggers if the `charged_amount` is not equal to `expected_amount`. (High Severity if deviation $> 100$, else Medium)
  - **INCORRECT_CHARGE**: Triggers if a customer was charged for a failed data transfer session. (High Severity)
  - **USAGE_CAP_EXCEEDED**: Triggers if API data-transfer counts exceed standard plan allocations. (Medium Severity)
  - **DUPLICATE_INVOICE**: Triggers if a duplicate invoice flag is active. (High Severity)

### 4. Support Ops Intelligence Agent
Scans support logs and ticketing sentiment to catch systemic API downtimes.
- **Rules**:
  - **SYSTEMIC_FIP_DOWNTIME**: Triggers if $\ge 2$ support tickets mention errors with the same Financial Information Provider (e.g. "HDFC Bank", "SBI Bank") within the batch. (High/Medium Severity)
  - **SLA_BREACH**: Triggers if a high-priority ticket remains unresolved for $> 24$ hours. (High Severity)
  - **CONSENT_REDIRECT_LOOP**: Triggers if ticket content reveals redirect loops or login loops during authentication. (Medium Severity)

### 5. Audit & Safety Agent
Validates proposed actions against system security boundary guidelines.
- **Safety Policy**:
  - **Auto-Approval**: Action is marked `APPROVED` only if severity is `low` or `medium` AND the suggested action has no financial transfer implications.
  - **Human Escalation**: Action is marked `ESCALATE_TO_HUMAN` if:
    1. Finding severity is `high`.
    2. Action text contains keywords involving active financial movement (e.g., `refund`, `payout`, `chargeback`, `settlement`).
  - **Audit Logging**: Every decision is written to the ledger history with a full rationale.

---

## 🚀 Running the Production-Grade Stack

To run the full stack locally:

### 1. Start the API Server
Exposes the REST endpoints and MCP Tool Server on port 8000.
```bash
python -m uvicorn mcp.context_server:app --port 8000 --reload
```

### 2. Launch the Streamlit Dashboard
Renders the visual operations monitoring interface.
```bash
streamlit run ui/dashboard.py
```
*(If the API server on port 8000 is running, the dashboard will interact with it dynamically. If not, the dashboard will run the workflows locally inside the Streamlit sandbox, providing a robust fallback).*
