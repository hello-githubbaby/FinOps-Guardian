from typing import List, Optional

from agents.audit_safety_agent import AuditAndSafetyAgent, DecisionRecord
from agents.orchestrator_agent import OperationalEvent, OpsOrchestratorAgent
from agents.payment_ops_agent import PaymentOpsMonitorAgent
from agents.billing_ops_agent import BillingOpsGuardianAgent
from agents.support_ops_agent import SupportOpsIntelligenceAgent


class OpsWorkflow:
    """
    Synchronous, deterministic workflow that orchestrates operational event
    routing, anomaly detection across payments, billing, and support, and safety review.
    Contains no business logic or side effects.
    """

    def __init__(
        self,
        orchestrator: Optional[OpsOrchestratorAgent] = None,
        payment_monitor: Optional[PaymentOpsMonitorAgent] = None,
        billing_guardian: Optional[BillingOpsGuardianAgent] = None,
        support_intelligence: Optional[SupportOpsIntelligenceAgent] = None,
        audit_agent: Optional[AuditAndSafetyAgent] = None,
    ) -> None:
        self._orchestrator = orchestrator or OpsOrchestratorAgent()
        self._payment_monitor = payment_monitor or PaymentOpsMonitorAgent()
        self._billing_guardian = billing_guardian or BillingOpsGuardianAgent()
        self._support_intelligence = support_intelligence or SupportOpsIntelligenceAgent()
        self._audit_agent = audit_agent or AuditAndSafetyAgent()

    def run(self, events: List[OperationalEvent]) -> List[DecisionRecord]:
        """
        Coordinate agents to review payment, billing, and support-related operational events.

        Steps:
        1. Route events via OpsOrchestratorAgent.
        2. Analyze payment, billing, and support events with respective specialized agents.
        3. Consolidate findings and apply safety review with AuditAndSafetyAgent.
        """
        routing = self._orchestrator.route_events(events)

        # 1. Analyze Payment Events
        payment_events = routing.get("payment_tasks", [])
        payment_findings = (
            self._payment_monitor.analyze_events(payment_events)
            if payment_events
            else []
        )

        # 2. Analyze Billing Events
        billing_events = routing.get("billing_tasks", [])
        billing_findings = (
            self._billing_guardian.analyze_events(billing_events)
            if billing_events
            else []
        )

        # 3. Analyze Support Events
        support_events = routing.get("support_tasks", [])
        support_findings = (
            self._support_intelligence.analyze_events(support_events)
            if support_events
            else []
        )

        # 4. Consolidate Findings
        all_findings = []
        all_findings.extend(payment_findings)
        all_findings.extend(billing_findings)
        all_findings.extend(support_findings)

        # 5. Apply Audit & Safety Review
        decisions = (
            self._audit_agent.review_findings(all_findings)
            if all_findings
            else []
        )

        return decisions
