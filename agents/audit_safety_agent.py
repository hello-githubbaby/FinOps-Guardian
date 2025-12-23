import logging
from typing import Dict, List, Literal, TypedDict

logger = logging.getLogger(__name__)

Severity = Literal["low", "medium", "high"]
Decision = Literal["APPROVED", "ESCALATE_TO_HUMAN"]


class Finding(TypedDict):
    event_id: str
    anomaly_type: str
    severity: Severity
    suggested_action: str


class DecisionRecord(TypedDict):
    event_id: str
    decision: Decision
    reason: str


class AuditAndSafetyAgent:
    """
    Safety and compliance gate for anomaly findings.

    This agent performs deterministic, rule-based decisions and does not
    execute any actions.
    """

    def review_findings(self, findings: List[Finding]) -> List[DecisionRecord]:
        """
        Apply escalation rules to anomaly findings.
        """
        decisions: List[DecisionRecord] = []
        for finding in findings:
            decision, reason = self._decide(finding)
            record: DecisionRecord = {
                "event_id": finding["event_id"],
                "decision": decision,
                "reason": reason,
            }
            decisions.append(record)
            logger.info("Safety decision recorded", extra=record)
        return decisions

    def _decide(self, finding: Finding) -> (Decision, str):
        severity = finding.get("severity")
        action_text = finding.get("suggested_action", "")

        if severity == "high":
            return (
                "ESCALATE_TO_HUMAN",
                "High severity finding requires human review.",
            )

        if self._mentions_payout_or_refund(action_text):
            return (
                "ESCALATE_TO_HUMAN",
                "Suggested action involves refund or payout.",
            )

        return ("APPROVED", "Routine finding approved by safety rules.")

    def _mentions_payout_or_refund(self, suggested_action: str) -> bool:
        text = suggested_action.lower()
        return "refund" in text or "payout" in text

