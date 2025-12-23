from typing import Any, Dict, List, Optional

from agents.orchestrator_agent import OperationalEvent
from workflows.ops_workflow import OpsWorkflow

ALLOWED_EVENT_TYPES = {"payment", "billing", "support"}


class OpsHealthMCPServer:
    """
    MCP-compatible boundary exposing a safe, read-only workflow entrypoint.

    This server performs input validation, delegates to the ops workflow, and
    returns primitive JSON-safe data structures. No business logic, side effects,
    or network transport are implemented here.
    """

    def __init__(self, workflow: Optional[OpsWorkflow] = None) -> None:
        self._workflow = workflow or OpsWorkflow()

    def run_ops_health_check(
        self, raw_events: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Validate raw event input, invoke the ops workflow, and return reviewed decisions.

        Input schema (per event):
        - event_id: str
        - event_type: "payment" | "billing" | "support"
        - payload: dict
        - timestamp: str

        Output schema:
        {
            "decisions": [
                {
                    "event_id": str,
                    "decision": "APPROVED" | "ESCALATE_TO_HUMAN",
                    "reason": str
                },
                ...
            ]
        }
        """
        events = [self._to_operational_event(item) for item in raw_events]
        decisions = self._workflow.run(events)
        # Return primitive dicts to avoid leaking internal classes.
        return {"decisions": [dict(record) for record in decisions]}

    def _to_operational_event(self, data: Dict[str, Any]) -> OperationalEvent:
        self._validate_event_payload(data)
        return OperationalEvent(
            event_id=str(data["event_id"]),
            event_type=data["event_type"],
            payload=data.get("payload") or {},
            timestamp=str(data["timestamp"]),
        )

    def _validate_event_payload(self, data: Dict[str, Any]) -> None:
        required_keys = {"event_id", "event_type", "payload", "timestamp"}
        missing = required_keys - data.keys()
        if missing:
            raise ValueError(f"Missing required event fields: {sorted(missing)}")

        event_type = data["event_type"]
        if event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"Unsupported event_type: {event_type}")

        payload = data.get("payload")
        if payload is None:
            raise ValueError("payload must not be None")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dictionary")

