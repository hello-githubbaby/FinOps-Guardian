import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from workflows.ops_workflow import OpsWorkflow
from agents.orchestrator_agent import OperationalEvent
from mcp.ops_health_mcp import OpsHealthMCPServer
from mcp.tool_registry import mcp_tool_registry
from mcp.schemas import OpsHealthCheckRequest, OpsHealthCheckResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FinOps Guardian API & MCP Server",
    description="Safety-first automated finance operations auditor with human-in-the-loop control.",
    version="1.0.0"
)

# Enable CORS for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for simulation states and audit logs
AUDIT_LOG_STORE: List[Dict[str, Any]] = []
DECISION_HISTORY: Dict[str, Dict[str, Any]] = {}

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_EVENTS_PATH = os.path.join(BASE_DIR, "data", "sample_events.json")

# Initialize MCP core
mcp_core = OpsHealthMCPServer()

# Define MCP Tool input schemas
HEALTH_CHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "event_type": {"type": "string", "enum": ["payment", "billing", "support"]},
                    "timestamp": {"type": "string"},
                    "payload": {"type": "object"}
                },
                "required": ["event_id", "event_type", "payload", "timestamp"]
            }
        }
    },
    "required": ["events"]
}

GET_EVENTS_SCHEMA = {
    "type": "object",
    "properties": {}
}

# Register MCP Tools
@mcp_tool_registry.register_tool(
    name="run_ops_health_check",
    description="Run the safety-first FinOps workflow over a batch of events to audit payments, billing, and support complaints.",
    input_schema=HEALTH_CHECK_SCHEMA
)
def tool_run_ops_health_check(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """MCP Tool Handler for auditing operations."""
    return mcp_core.run_ops_health_check(events)

@mcp_tool_registry.register_tool(
    name="get_sample_events",
    description="Retrieve a batch of realistic sample events representing standard behaviors and anomalies in the system.",
    input_schema=GET_EVENTS_SCHEMA
)
def tool_get_sample_events() -> List[Dict[str, Any]]:
    """MCP Tool Handler to fetch sample events."""
    try:
        if os.path.exists(SAMPLE_EVENTS_PATH):
            with open(SAMPLE_EVENTS_PATH, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Failed to load sample events: {e}")
        return []

# --- REST API Endpoints ---

@app.get("/health")
def api_health():
    return {"status": "healthy", "service": "FinOps Guardian"}

@app.get("/api/sample-events", response_model=List[Dict[str, Any]])
def api_get_sample_events():
    """Retrieve sample events for testing."""
    return tool_get_sample_events()

@app.post("/api/check-health")
def api_check_health(payload: Dict[str, Any] = Body(...)):
    """
    Run health audit check. Also saves the results to the local
    in-memory audit store so they can be inspected in the dashboard.
    """
    events = payload.get("events")
    if not events:
        raise HTTPException(status_code=400, detail="Missing events field")
    
    # Run the workflow
    try:
        result = mcp_core.run_ops_health_check(events)
        decisions = result.get("decisions", [])
        
        # Merge event details with decision records for rich logs
        event_map = {e["event_id"]: e for e in events}
        
        # Generate rich findings mapping for the UI
        # To do this, we re-run agents individually to extract the descriptive findings
        workflow = mcp_core._workflow
        
        # Let's rebuild operational events list
        op_events = []
        for e in events:
            op_events.append(OperationalEvent(
                event_id=e["event_id"],
                event_type=e["event_type"],
                payload=e.get("payload") or {},
                timestamp=e["timestamp"]
            ))
            
        routing = workflow._orchestrator.route_events(op_events)
        
        findings = []
        findings.extend(workflow._payment_monitor.analyze_events(routing.get("payment_tasks", [])))
        findings.extend(workflow._billing_guardian.analyze_events(routing.get("billing_tasks", [])))
        findings.extend(workflow._support_intelligence.analyze_events(routing.get("support_tasks", [])))
        
        finding_map = {f["event_id"]: f for f in findings}
        
        # Save to logs
        for dec in decisions:
            event_id = dec["event_id"]
            evt = event_map.get(event_id, {})
            fnd = finding_map.get(event_id, {})
            
            # Check if already resolved by user
            existing_decision = DECISION_HISTORY.get(event_id)
            if existing_decision:
                final_dec = existing_decision["decision"]
                reason = existing_decision["reason"]
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
            
            # Update cache
            DECISION_HISTORY[event_id] = record
            
        return {"decisions": list(DECISION_HISTORY.values())}
    except Exception as e:
        logger.error(f"Error checking health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audit-logs")
def api_get_audit_logs():
    """Retrieve all current decision records and audit states."""
    return {"decisions": list(DECISION_HISTORY.values())}

@app.post("/api/action-approve/{event_id}")
def api_approve_action(event_id: str, payload: Dict[str, str] = Body(...)):
    """Simulate manual override: Human approval of a high-risk escalated action."""
    if event_id not in DECISION_HISTORY:
        raise HTTPException(status_code=404, detail="Event not found in history")
    
    user = payload.get("user", "Ops Manager")
    note = payload.get("note", "Manual approval")
    
    record = DECISION_HISTORY[event_id]
    record["decision"] = "APPROVED_BY_HUMAN"
    record["reason"] = f"Approved by {user}. Note: {note}"
    DECISION_HISTORY[event_id] = record
    
    return {"status": "success", "record": record}

@app.post("/api/action-escalate/{event_id}")
def api_escalate_action(event_id: str, payload: Dict[str, str] = Body(...)):
    """Simulate manual override: Escalate/reject or flag for executive review."""
    if event_id not in DECISION_HISTORY:
        raise HTTPException(status_code=404, detail="Event not found in history")
        
    user = payload.get("user", "Ops Manager")
    note = payload.get("note", "Manual escalation")
    
    record = DECISION_HISTORY[event_id]
    record["decision"] = "ESCALATED_TO_EXECUTIVE"
    record["reason"] = f"Escalated to Exec by {user}. Note: {note}"
    DECISION_HISTORY[event_id] = record
    
    return {"status": "success", "record": record}

@app.post("/api/clear-history")
def api_clear_history():
    """Clears history for a clean demo state."""
    DECISION_HISTORY.clear()
    return {"status": "cleared"}

# --- MCP Protocol Spec Endpoints ---

@app.get("/mcp/tools")
def api_list_mcp_tools():
    """MCP Spec: List available tools."""
    return {"tools": mcp_tool_registry.get_tool_definitions()}

@app.post("/mcp/tools/call")
def api_call_mcp_tool(payload: Dict[str, Any] = Body(...)):
    """MCP Spec: Execute a tool."""
    name = payload.get("name")
    arguments = payload.get("arguments", {})
    
    if not name:
        raise HTTPException(status_code=400, detail="Missing tool name")
        
    try:
        result = mcp_tool_registry.execute_tool(name, arguments)
        return {"result": result}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Tool {name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp.context_server:app", host="127.0.0.1", port=8000, reload=True)
