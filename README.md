# FinOps Guardian 🛡️
### AI-Assisted Operations Health Monitoring with Safety-First Agent Architecture

FinOps Guardian is a production-grade, safety-first, AI-assisted operations monitoring system designed for modern fintech platforms. It monitors critical systems (payment gateways, subscription billing, bank data-sharing flows, support tickets), routes operational events to specialized deterministic agents, enforces strict human-in-the-loop compliance checks, and exposes the workflow securely via MCP (Model Context Protocol).

---

## 🚀 Key Features

- **Multi-Agent Architecture**:
  - **Ops Orchestrator**: Ingests, validates, and deterministically routes events to specific domain experts without LLM hallucination risk.
  - **Payment Ops Monitor**: Detects duplicate payments, processing delays, and gateway failure anomalies.
  - **Billing Ops Guardian**: Protects against billing mismatches, subscription limit overruns, and double invoicing.
  - **Support Ops Intelligence**: Clusters customer tickets and identifies systemic bank-link timeouts or SLA breaches.
  - **Audit & Safety Agent**: Serves as a compliance gate. Automatically approves minor events and flags/blocks high-risk actions (like payouts or refunds) for manual human intervention.
- **Model Context Protocol (MCP) Interface**: Full compliance with the MCP standard, registering core auditing tools for discovery and execution by LLM clients (`/mcp/tools`, `/mcp/tools/call`).
- **REST API Service**: Powered by FastAPI, featuring runtime schemas, strict validation, and interactive endpoints for simulation and overrides.
- **Premium Operations Dashboard**: A visual control console built with Streamlit featuring rich custom dark-theme styling, live metrics, a visual pipeline path, and interactive human-in-the-loop action desk widgets.
- **API-First Architecture with Sandbox Fallback**: The dashboard communicates dynamically with the FastAPI backend, but will automatically fall back to local agent sandbox execution if the backend API is offline.

---

## 🛠️ Tech Stack & Setup

### Requirements
- Python 3.9+
- Packages: `fastapi`, `uvicorn`, `streamlit`, `pandas`, `pydantic`

### Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```
*(If no requirements file is present, standard `pip install fastapi uvicorn streamlit pandas pydantic requests` is sufficient).*

---

## 🏁 How to Run

### 1. Run the Backend API & MCP Server
Start the FastAPI server on port `8000`:
```bash
python -m uvicorn mcp.context_server:app --port 8000 --reload
```
- Access Interactive API Documentation (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Discover MCP Tools: [http://127.0.0.1:8000/mcp/tools](http://127.0.0.1:8000/mcp/tools)

### 2. Run the Dashboard Frontend
Launch the Streamlit monitoring interface:
```bash
streamlit run ui/dashboard.py
```
- Streamlit will open the dashboard in your default browser (usually [http://localhost:8501](http://localhost:8501)).

---

## 🧩 Architectural Design

```
Raw Event Streams (JSON) 
         │
         ▼
 ┌───────────────┐
 │  FastAPI/MCP  │ ◄─── REST / MCP API Interface
 └───────┬───────┘
         │
         ▼
 ┌───────────────────────────────────────────────┐
 │           Ops Orchestrator Agent              │ (Deterministic Routing)
 └──────┬──────────────┬──────────────┬──────────┘
        │              │              │
        ▼              ▼              ▼
 ┌──────────┐   ┌──────────┐   ┌──────────┐
 │ Payment  │   │ Billing  │   │ Support  │ (Domain Agents: Anomaly Scanners)
 │ Monitor  │   │ Guardian │   │ Intel    │
 └──────┬───┘   └──────┬───┘   └──────┬───┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
         ┌────────────────────────────┐
         │    Audit & Safety Agent    │ (Policy Compliance & Manual Block Gate)
         └─────────────┬──────────────┘
                       │
         ┌─────────────▼──────────────┐
         │    Interactive Dashboard   │ (Human-in-the-loop Override Ledger)
         └────────────────────────────┘
```

---

## 🔒 Safety Guidelines

1. **Deterministic Layering**: All routing and basic anomaly detection run via deterministic code paths to ensure reliability and auditability.
2. **No Direct Financial Execution**: Agents suggest actions but are strictly prohibited from invoking monetary transfers, database balance modifications, or external write APIs.
3. **Audit Trails**: Every decision (automated or manual) is recorded with timestamped logs, including operator names and justification notes.
