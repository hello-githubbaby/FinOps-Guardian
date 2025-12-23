import logging
from typing import Dict, List, Literal

from agents.orchestrator_agent import OperationalEvent

logger = logging.getLogger(__name__)

AnomalyType = Literal["FAILED_PAYMENT", "DELAYED_PAYMENT", "DUPLICATE_PAYMENT"]
Severity = Literal["low", "medium", "high"]


class PaymentOpsMonitorAgent:
    """
    Deterministic analyzer for payment-related operational events.

    This agent flags payment anomalies without executing external calls or actions.
    """

    def analyze_events(self, events: List[OperationalEvent]) -> List[Dict[str, str]]:
        """
        Inspect payment events and emit anomaly findings.

        Returns a list of dictionaries with keys:
        - event_id
        - anomaly_type
        - severity
        - suggested_action
        """
        findings: List[Dict[str, str]] = []
        transaction_counts = self._count_transactions(events)

        for event in events:
            payload = event.payload or {}
            findings.extend(
                self._detect_anomalies(event, payload, transaction_counts)
            )

        return findings

    def _count_transactions(self, events: List[OperationalEvent]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for event in events:
            tx_id = (event.payload or {}).get("transaction_id")
            if not tx_id:
                continue
            counts[tx_id] = counts.get(tx_id, 0) + 1
        return counts

    def _detect_anomalies(
        self,
        event: OperationalEvent,
        payload: dict,
        transaction_counts: Dict[str, int],
    ) -> List[Dict[str, str]]:
        findings: List[Dict[str, str]] = []
        tx_id = payload.get("transaction_id")

        payment_status = payload.get("payment_status")
        if payment_status == "failed":
            findings.append(
                self._build_finding(
                    event,
                    anomaly_type="FAILED_PAYMENT",
                    severity="high",
                    suggested_action="Investigate failure reason and retry if safe.",
                )
            )
            return findings
        processing_time = payload.get("processing_time_seconds")
        if isinstance(processing_time, (int, float)) and processing_time > 30:
            findings.append(
                self._build_finding(
                    event,
                    anomaly_type="DELAYED_PAYMENT",
                    severity="medium",
                    suggested_action="Review processing bottlenecks and escalate if queueing persists.",
                )
            )

        if tx_id and transaction_counts.get(tx_id, 0) > 1:
            findings.append(
                self._build_finding(
                    event,
                    anomaly_type="DUPLICATE_PAYMENT",
                    severity="high",
                    suggested_action="Hold subsequent attempts and reconcile duplicates before settlement.",
                )
            )

        for finding in findings:
            logger.info("Detected payment anomaly", extra=finding)

        return findings

    def _build_finding(
        self,
        event: OperationalEvent,
        anomaly_type: AnomalyType,
        severity: Severity,
        suggested_action: str,
    ) -> Dict[str, str]:
        return {
            "event_id": event.event_id,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "suggested_action": suggested_action,
        }

