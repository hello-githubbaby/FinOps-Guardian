from typing import List, Optional

from agents.audit_safety_agent import AuditAndSafetyAgent, DecisionRecord
from agents.orchestrator_agent import OperationalEvent, OpsOrchestratorAgent
from agents.payment_ops_agent import PaymentOpsMonitorAgent


class OpsWorkflow:
    """
    Synchronous, deterministic workflow that orchestrates operational event
    routing, payment anomaly detection, and safety review. Contains no
    business logic or side effects.
    """

    def __init__(
        self,
        orchestrator: Optional[OpsOrchestratorAgent] = None,
        payment_monitor: Optional[PaymentOpsMonitorAgent] = None,
        audit_agent: Optional[AuditAndSafetyAgent] = None,
    ) -> None:
        self._orchestrator = orchestrator or OpsOrchestratorAgent()
        self._payment_monitor = payment_monitor or PaymentOpsMonitorAgent()
        self._audit_agent = audit_agent or AuditAndSafetyAgent()

    def run(self, events: List[OperationalEvent]) -> List[DecisionRecord]:
        """
        Coordinate agents to review payment-related operational events.

        Steps:
        1. Route events via OpsOrchestratorAgent.
        2. Analyze payment events with PaymentOpsMonitorAgent.
        3. Apply safety review with AuditAndSafetyAgent.
        """
        routing = self._orchestrator.route_events(events)

        payment_events = routing["payment_tasks"]
        payment_findings = (
            self._payment_monitor.analyze_events(payment_events)
            if payment_events
            else []
        )

        decisions = (
            self._audit_agent.review_findings(payment_findings)
            if payment_findings
            else []
        )

        return decisions

