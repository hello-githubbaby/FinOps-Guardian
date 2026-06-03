import streamlit as st
import pandas as pd
import requests
import json
import os
import sys
from typing import List, Dict, Any

# Ensure absolute import path works
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator_agent import OperationalEvent
from workflows.ops_workflow import OpsWorkflow

# Set page configuration with a premium look
st.set_page_config(
    page_title="FinOps Guardian Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API config
API_URL = "http://127.0.0.1:8000"

# Inject Custom Premium CSS (Dark Glassmorphism Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main container background */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #161a24 100%);
        color: #e2e8f0;
    }
    
    /* Card design */
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    .metric-title {
        font-size: 0.9rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 2.2rem;
        color: #ffffff;
        font-weight: 700;
        line-height: 1;
    }
    
    .metric-footer {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 8px;
    }
    
    /* Custom buttons */
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }
    
    .stButton>button:hover {
        background: linear-gradient(90deg, #6366f1 0%, #818cf8 100%);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        transform: translateY(-1px);
    }
    
    /* Table headers styling */
    thead tr th {
        background-color: #1e293b !important;
        color: #94a3b8 !important;
    }
    
    /* Status Badge styling */
    .badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: bold;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .badge-approved {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .badge-escalated {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .badge-human-approved {
        background-color: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .badge-exec-escalated {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    /* Gradient header decoration */
    .gradient-header {
        background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions for API interaction with fallback
def run_health_check_via_api(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        response = requests.post(f"{API_URL}/api/check-health", json={"events": events}, timeout=5)
        if response.status_code == 200:
            return response.json().get("decisions", [])
    except requests.exceptions.ConnectionError:
        pass
    
    # Local fallback logic if backend server is not running
    st.sidebar.warning("⚠️ API server unreachable. Running agents locally in sandbox mode.")
    return run_health_check_locally(events)

def get_sample_events_via_api() -> List[Dict[str, Any]]:
    try:
        response = requests.get(f"{API_URL}/api/sample-events", timeout=3)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        pass
    
    # Local fallback
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sample_path = os.path.join(base_dir, "data", "sample_events.json")
    if os.path.exists(sample_path):
        with open(sample_path, "r") as f:
            return json.load(f)
    return []

def get_audit_logs_via_api() -> List[Dict[str, Any]]:
    try:
        response = requests.get(f"{API_URL}/api/audit-logs", timeout=3)
        if response.status_code == 200:
            return response.json().get("decisions", [])
    except requests.exceptions.ConnectionError:
        pass
    return []

def approve_action_via_api(event_id: str, note: str) -> bool:
    try:
        response = requests.post(f"{API_URL}/api/action-approve/{event_id}", json={"user": "Ops Manager", "note": note}, timeout=3)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        pass
    return False

def escalate_action_via_api(event_id: str, note: str) -> bool:
    try:
        response = requests.post(f"{API_URL}/api/action-escalate/{event_id}", json={"user": "Ops Manager", "note": note}, timeout=3)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        pass
    return False

def clear_history_via_api() -> bool:
    try:
        response = requests.post(f"{API_URL}/api/clear-history", timeout=3)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        pass
    return False

# Local Simulation Fallback State Manager
def run_health_check_locally(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Runs the audit workflow inside the Streamlit thread and updates local cache."""
    workflow = OpsWorkflow()
    op_events = []
    event_map = {}
    
    for e in events:
        op_events.append(OperationalEvent(
            event_id=e["event_id"],
            event_type=e["event_type"],
            payload=e.get("payload") or {},
            timestamp=e["timestamp"]
        ))
        event_map[e["event_id"]] = e

    # Execute orchestrator routing
    routing = workflow._orchestrator.route_events(op_events)
    
    findings = []
    findings.extend(workflow._payment_monitor.analyze_events(routing.get("payment_tasks", [])))
    findings.extend(workflow._billing_guardian.analyze_events(routing.get("billing_tasks", [])))
    findings.extend(workflow._support_intelligence.analyze_events(routing.get("support_tasks", [])))
    
    finding_map = {f["event_id"]: f for f in findings}
    
    decisions = workflow._audit_agent.review_findings(findings)
    
    decisions_list = []
    for dec in decisions:
        event_id = dec["event_id"]
        evt = event_map.get(event_id, {})
        fnd = finding_map.get(event_id, {})
        
        # Check if already in session state
        existing = st.session_state.local_decisions.get(event_id)
        if existing:
            final_dec = existing["decision"]
            reason = existing["reason"]
        else:
            final_dec = dec["decision"]
            reason = dec["reason"]
            
        record = {
            "event_id": event_id,
            "event_type": evt.get("event_type"),
            "timestamp": evt.get("timestamp"),
            "payload": evt.get("payload"),
            "anomaly_type": fnd.get("anomaly_type", "N/A"),
            "severity": fnd.get("severity", "low" if final_dec == "APPROVED" else "high"),
            "suggested_action": fnd.get("suggested_action", "N/A"),
            "decision": final_dec,
            "reason": reason,
            "impacted_customers": fnd.get("impacted_customers", "1"),
            "frequency_score": fnd.get("frequency_score", "1")
        }
        st.session_state.local_decisions[event_id] = record
        
    return list(st.session_state.local_decisions.values())

# Initialize local session state cache
if "local_decisions" not in st.session_state:
    st.session_state.local_decisions = {}
if "events_input" not in st.session_state:
    st.session_state.events_input = ""
if "pipeline_executed" not in st.session_state:
    st.session_state.pipeline_executed = False

# Sidebar controls
st.sidebar.markdown("<h2 style='text-align: center; color: white;'>⚙️ System Controls</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

if st.sidebar.button("📂 Load Sample Events Data", use_container_width=True):
    sample_events = get_sample_events_via_api()
    st.session_state.events_input = json.dumps(sample_events, indent=2)
    st.sidebar.success("Loaded sample events into editor!")
    st.rerun()

if st.sidebar.button("🧹 Clear Simulation History", use_container_width=True):
    clear_history_via_api()
    st.session_state.local_decisions.clear()
    st.session_state.pipeline_executed = False
    st.sidebar.info("Audit log history cleared.")
    st.rerun()

# Main Dashboard layout
st.markdown('<div class="gradient-header">🛡️ FinOps Guardian</div>', unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.15rem; color: #94a3b8; margin-top: -10px; margin-bottom: 25px;'>Safety-First Operations Monitoring & Consent Flow Auditing Console</p>", unsafe_allow_html=True)

# ----------------- LIVE AUDIT LOG & DECISIONS STATS -----------------
# If pipeline has not been executed yet, force empty metrics (0)
if st.session_state.pipeline_executed:
    api_logs = get_audit_logs_via_api()
    decisions_to_use = api_logs if api_logs else list(st.session_state.local_decisions.values())
else:
    decisions_to_use = []

total_events = len(decisions_to_use)
total_anomalies = len([d for d in decisions_to_use if d["anomaly_type"] != "N/A"])
pending_escalations = len([d for d in decisions_to_use if d["decision"] == "ESCALATE_TO_HUMAN"])
auto_approved = len([d for d in decisions_to_use if d["decision"] == "APPROVED"])
human_resolved = len([d for d in decisions_to_use if d["decision"] in ["APPROVED_BY_HUMAN", "ESCALATED_TO_EXECUTIVE"]])

# Display Premium Metrics Row
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Audited Events</div>
        <div class="metric-value">{total_events}</div>
        <div class="metric-footer">Ingested operational streams</div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Anomalies Detected</div>
        <div class="metric-value" style="color: #fb7185;">{total_anomalies}</div>
        <div class="metric-footer">Across Payments, Billing & Support</div>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Automated Approvals</div>
        <div class="metric-value" style="color: #34d399;">{auto_approved}</div>
        <div class="metric-footer">Cleared by rule engine policy</div>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Pending Human Review</div>
        <div class="metric-value" style="color: #f59e0b;">{pending_escalations}</div>
        <div class="metric-footer">Awaiting manual approval override</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- EVENT EDITOR & PIPELINE -----------------
col_editor, col_pipe = st.columns([1, 1])

with col_editor:
    st.subheader("📝 Live Event Stream Editor")
    raw_json_input = st.text_area(
        "Ingest Event Batch (JSON Array)",
        value=st.session_state.events_input,
        height=320,
        placeholder="Paste a JSON list of events or click 'Load Sample Events' in the sidebar..."
    )
    
    if st.button("🚀 Execute FinOps Audit Pipeline", use_container_width=True):
        if not raw_json_input.strip():
            st.error("Please enter a JSON list of events to process.")
        else:
            try:
                parsed_events = json.loads(raw_json_input)
                if not isinstance(parsed_events, list):
                    st.error("Input must be a JSON array (list of events).")
                else:
                    # Run health check
                    st.session_state.events_input = raw_json_input
                    with st.spinner("Executing agent pipeline..."):
                        decisions_to_use = run_health_check_via_api(parsed_events)
                    st.session_state.pipeline_executed = True
                    st.success("Orchestration pipeline execution complete!")
                    st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON format: {str(e)}")

with col_pipe:
    st.subheader("⛓️ Safe AI Orchestration Flow")
    
    st.markdown("""
    <div style="background-color: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 25px; min-height: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="display: flex; justify-content: space-between; align-items: center; text-align: center;">
            <div style="width: 28%; background-color: rgba(99, 102, 241, 0.15); border: 1px solid #6366f1; border-radius: 8px; padding: 10px;">
                <b style="color: #818cf8; font-size: 0.85rem;">1. EVENT INGESTION</b>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">Raw JSON Payload</div>
            </div>
            <div style="color: #64748b; font-size: 1.5rem;">➡️</div>
            <div style="width: 32%; background-color: rgba(168, 85, 247, 0.15); border: 1px solid #a855f7; border-radius: 8px; padding: 10px;">
                <b style="color: #c084fc; font-size: 0.85rem;">2. ORCHESTRATOR</b>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">Deterministic Routing</div>
            </div>
            <div style="color: #64748b; font-size: 1.5rem;">➡️</div>
            <div style="width: 30%; background-color: rgba(236, 72, 153, 0.15); border: 1px solid #ec4899; border-radius: 8px; padding: 10px;">
                <b style="color: #f472b6; font-size: 0.85rem;">3. DOMAIN EXPERTS</b>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">Payment/Billing/Support</div>
            </div>
        </div>
        
        <div style="text-align: center; margin: 15px 0; color: #64748b; font-size: 1.2rem;">⬇️</div>
        
        <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
            <div style="width: 42%; background-color: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; border-radius: 8px; padding: 12px;">
                <b style="color: #fbbf24; font-size: 0.85rem;">4. AUDIT & SAFETY GATE</b>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">Policy engine validates output. Blocks unsafe automated acts.</div>
            </div>
            <div style="color: #64748b; font-size: 1.5rem;">➡️</div>
            <div style="width: 42%; background-color: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 8px; padding: 12px;">
                <b style="color: #34d399; font-size: 0.85rem;">5. DECISION LOGS</b>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">APPROVED or ESCALATED TO HUMAN (HITL override)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# ----------------- HUMAN IN THE LOOP ACTIONS SECTION -----------------
st.subheader("🧑‍✈️ Human-In-The-Loop (HITL) Action Desk")

escalated_items = [d for d in decisions_to_use if d["decision"] == "ESCALATE_TO_HUMAN"]

if not st.session_state.pipeline_executed or not escalated_items:
    st.info("✅ All events are currently reconciled. No pending items require human intervention.")
else:
    st.markdown("<p style='color: #fb7185;'>The following high-severity anomalies or sensitive actions have been BLOCKED by the Audit & Safety Agent. A human signature is required to proceed.</p>", unsafe_allow_html=True)
    
    for idx, item in enumerate(escalated_items):
        with st.container():
            st.markdown(f"""
            <div style="background-color: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 10px; padding: 20px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span style="font-weight: bold; color: white;">Event ID: <code style="color:#f472b6;">{item['event_id']}</code> ({item.get('event_type','unknown').upper()})</span>
                    <span class="badge badge-escalated">ESCALATED TO HUMAN</span>
                </div>
                <div style="font-size: 0.95rem; line-height: 1.5; color: #cbd5e1; margin-bottom: 15px;">
                    <b>Anomaly:</b> {item.get('anomaly_type')} <br>
                    <b>Severity:</b> <span style="color: #f43f5e; font-weight: bold;">{item.get('severity','high').upper()}</span> <br>
                    <b>Proposed Action:</b> <code style="color: #93c5fd;">{item.get('suggested_action')}</code> <br>
                    <b>Safety Block Reason:</b> {item.get('reason')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action inputs side-by-side
            btn_col1, btn_col2, note_col = st.columns([1, 1, 3])
            
            with note_col:
                audit_note = st.text_input("Audit Notes / Justification", key=f"note_{item['event_id']}", placeholder="Enter justification for overriding...")
            
            with btn_col1:
                if st.button("✔️ Approve Override", key=f"app_{item['event_id']}", use_container_width=True):
                    if not audit_note.strip():
                        st.warning("Please provide audit notes before approving.")
                    else:
                        success = approve_action_via_api(item['event_id'], audit_note)
                        if not success:
                            # Update local state directly
                            st.session_state.local_decisions[item['event_id']]["decision"] = "APPROVED_BY_HUMAN"
                            st.session_state.local_decisions[item['event_id']]["reason"] = f"Approved by Ops Manager. Note: {audit_note}"
                        st.success(f"Approved event override {item['event_id']}")
                        st.rerun()
                        
            with btn_col2:
                if st.button("❌ Escalate to Executive", key=f"esc_{item['event_id']}", use_container_width=True):
                    if not audit_note.strip():
                        st.warning("Please provide audit notes before escalating.")
                    else:
                        success = escalate_action_via_api(item['event_id'], audit_note)
                        if not success:
                            # Update local state directly
                            st.session_state.local_decisions[item['event_id']]["decision"] = "ESCALATED_TO_EXECUTIVE"
                            st.session_state.local_decisions[item['event_id']]["reason"] = f"Escalated to Executive. Note: {audit_note}"
                        st.success(f"Escalated event {item['event_id']}")
                        st.rerun()

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# ----------------- AUDIT LOG HISTORY TABLE -----------------
st.subheader("📑 Global Audit Trial Ledger")

if not st.session_state.pipeline_executed or not decisions_to_use:
    st.info("No events have been processed yet. Click 'Load Sample Events' and run the pipeline to start auditing.")
else:
    # Prepare dataframe for displaying
    display_records = []
    for item in decisions_to_use:
        # Format decision style for display
        decision_raw = item.get("decision")
        badge_html = ""
        if decision_raw == "APPROVED":
            badge_html = f'<span class="badge badge-approved">{decision_raw}</span>'
        elif decision_raw == "ESCALATE_TO_HUMAN":
            badge_html = f'<span class="badge badge-escalated">{decision_raw}</span>'
        elif decision_raw == "APPROVED_BY_HUMAN":
            badge_html = f'<span class="badge badge-human-approved">MANUAL APPROVE</span>'
        else:
            badge_html = f'<span class="badge badge-exec-escalated">EXEC ESCALATED</span>'
            
        display_records.append({
            "Event ID": item.get("event_id"),
            "Category": str(item.get("event_type")).upper(),
            "Timestamp": item.get("timestamp"),
            "Issue Cluster / Anomaly": item.get("anomaly_type"),
            "Resolution Suggestion": item.get("suggested_action"),
            "Audit Decision": badge_html,
            "Policy Decision Reason": item.get("reason"),
        })
        
    df = pd.DataFrame(display_records)
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# ----------------- ANALYTICS & MONITORING -----------------
st.subheader("📊 Operational Diagnostics & Insights")

if st.session_state.pipeline_executed and decisions_to_use:
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("#### Anomaly Type Severity Breakdown")
        
        # Pull severity and type counts
        chart_data = []
        for item in decisions_to_use:
            if item.get("anomaly_type") != "N/A":
                chart_data.append({
                    "Anomaly Type": item.get("anomaly_type"),
                    "Severity": item.get("severity", "medium").upper()
                })
                
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            severity_counts = df_chart["Severity"].value_counts().reset_index()
            severity_counts.columns = ["Severity", "Count"]
            
            # Simple bar chart
            st.bar_chart(severity_counts.set_index("Severity"), color="#818cf8")
        else:
            st.info("No anomalies detected in the current stream.")
            
    with col_chart2:
        st.write("#### FIP API / Bank Connector Health Hotspots")
        
        # Analyze support tickets to see if we can identify SBI / HDFC failures
        bank_faults = {}
        for item in decisions_to_use:
            payload = item.get("payload") or {}
            content = str(payload.get("ticket_content", "")).lower()
            if "hdfc" in content:
                bank_faults["HDFC Bank"] = bank_faults.get("HDFC Bank", 0) + 1
            elif "sbi" in content or "state bank" in content:
                bank_faults["SBI Bank"] = bank_faults.get("SBI Bank", 0) + 1
            elif "icici" in content:
                bank_faults["ICICI Bank"] = bank_faults.get("ICICI Bank", 0) + 1
            elif "axis" in content:
                bank_faults["Axis Bank"] = bank_faults.get("Axis Bank", 0) + 1
                
        if bank_faults:
            df_banks = pd.DataFrame(list(bank_faults.items()), columns=["Bank Connector", "Failures Reported"])
            st.bar_chart(df_banks.set_index("Bank Connector"), color="#ec4899")
        else:
            st.info("No Bank connector failures found in support logs.")
else:
    st.info("Run the audit pipeline to compile analytics dashboard charts.")
