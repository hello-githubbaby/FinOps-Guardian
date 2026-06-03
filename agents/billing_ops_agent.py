import logging
from typing import Dict, List, Literal
from agents.orchestrator_agent import OperationalEvent

logger = logging.getLogger(__name__)

BillingIssueType = Literal["BILLING_MISMATCH", "INCORRECT_CHARGE", "USAGE_CAP_EXCEEDED", "DUPLICATE_INVOICE"]
Severity = Literal["low", "medium", "high"]

class BillingOpsGuardianAgent:
    """
    Deterministic validator for billing workflows, subscription limits, 
    and data consent sharing usage charges.
    """

    def analyze_events(self, events: List[OperationalEvent]) -> List[Dict[str, str]]:
        """
        Inspect billing events and detect discrepancies.
        
        Returns a list of finding dictionaries with keys:
        - event_id
        - anomaly_type (maps to billing issue type)
        - severity
        - suggested_action
        - impacted_customers (string representation of customer count)
        """
        findings: List[Dict[str, str]] = []
        
        for event in events:
            payload = event.payload or {}
            findings.extend(self._detect_discrepancies(event, payload))
            
        return findings

    def _detect_discrepancies(self, event: OperationalEvent, payload: dict) -> List[Dict[str, str]]:
        findings: List[Dict[str, str]] = []
        
        invoice_id = payload.get("invoice_id", "N/A")
        charged_amount = payload.get("charged_amount")
        expected_amount = payload.get("expected_amount")
        subscription_plan = payload.get("subscription_plan", "Standard")
        
        # Check 1: Billing Mismatch (Charged vs. Expected)
        if isinstance(charged_amount, (int, float)) and isinstance(expected_amount, (int, float)):
            if abs(charged_amount - expected_amount) > 0.01:
                diff = abs(charged_amount - expected_amount)
                severity: Severity = "high" if diff > 100 else "medium"
                findings.append(
                    self._build_finding(
                        event,
                        issue_type="BILLING_MISMATCH",
                        severity=severity,
                        suggested_action=f"Reconcile Invoice {invoice_id}. Charged: {charged_amount}, Expected: {expected_amount}. Difference: {diff}.",
                        impacted_customers="1"
                    )
                )
                
        # Check 2: Charging for failed data-consent transfer sessions (incorrect charge)
        session_status = payload.get("data_session_status")
        if session_status == "failed" and isinstance(charged_amount, (int, float)) and charged_amount > 0:
            findings.append(
                self._build_finding(
                    event,
                    issue_type="INCORRECT_CHARGE",
                    severity="high",
                    suggested_action=f"Initiate refund for Invoice {invoice_id}. Customer was charged for a failed consent data session.",
                    impacted_customers="1"
                )
            )

        # Check 3: Usage Cap Exceeded on billing subscription limits
        data_transfer_count = payload.get("data_transfer_count", 0)
        max_allowed_transfers = payload.get("max_allowed_transfers", 1000)
        if data_transfer_count > max_allowed_transfers:
            findings.append(
                self._build_finding(
                    event,
                    issue_type="USAGE_CAP_EXCEEDED",
                    severity="medium",
                    suggested_action=f"Apply subscription overage rates or trigger plan upgrade notification for plan '{subscription_plan}'. Current transfers: {data_transfer_count}.",
                    impacted_customers="1"
                )
            )

        # Check 4: Duplicate Invoice detection
        is_duplicate = payload.get("is_duplicate_invoice", False)
        if is_duplicate:
            findings.append(
                self._build_finding(
                    event,
                    issue_type="DUPLICATE_INVOICE",
                    severity="high",
                    suggested_action=f"Void duplicate Invoice {invoice_id} immediately before automated payment charge runs.",
                    impacted_customers="1"
                )
            )

        for finding in findings:
            logger.info("Detected billing discrepancy", extra=finding)

        return findings

    def _build_finding(
        self,
        event: OperationalEvent,
        issue_type: BillingIssueType,
        severity: Severity,
        suggested_action: str,
        impacted_customers: str
    ) -> Dict[str, str]:
        return {
            "event_id": event.event_id,
            "anomaly_type": issue_type,
            "severity": severity,
            "suggested_action": suggested_action,
            "impacted_customers": impacted_customers
        }
