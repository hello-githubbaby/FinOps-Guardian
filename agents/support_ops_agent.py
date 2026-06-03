import logging
from typing import Dict, List, Literal
from agents.orchestrator_agent import OperationalEvent

logger = logging.getLogger(__name__)

Severity = Literal["low", "medium", "high"]

class SupportOpsIntelligenceAgent:
    """
    Support intelligence analyzer that processes customer support complaints,
    tickets, and sentiment data to detect operational failures and system downtime.
    """

    def analyze_events(self, events: List[OperationalEvent]) -> List[Dict[str, str]]:
        """
        Analyze incoming support events to identify ticket clusters, frequencies, 
        and recommended remedies.
        
        Returns a list of findings with keys:
        - event_id
        - anomaly_type (maps to issue_cluster / anomaly description)
        - severity
        - suggested_action (maps to recommended action)
        - frequency_score
        """
        findings: List[Dict[str, str]] = []
        
        # Analyze tickets in batch to determine frequency of issues
        fip_issue_counts: Dict[str, int] = {}
        for event in events:
            payload = event.payload or {}
            ticket_content = (payload.get("ticket_content") or "").lower()
            
            # Detect target Financial Information Provider (FIP)
            fip = self._detect_fip(ticket_content)
            if fip:
                fip_issue_counts[fip] = fip_issue_counts.get(fip, 0) + 1
        
        for event in events:
            payload = event.payload or {}
            findings.extend(self._analyze_ticket(event, payload, fip_issue_counts))
            
        return findings

    def _detect_fip(self, content: str) -> str:
        content_lower = content.lower()
        if "hdfc" in content_lower:
            return "HDFC Bank"
        if "sbi" in content_lower or "state bank" in content_lower:
            return "SBI Bank"
        if "icici" in content_lower:
            return "ICICI Bank"
        if "axis" in content_lower:
            return "Axis Bank"
        return ""

    def _analyze_ticket(self, event: OperationalEvent, payload: dict, fip_counts: Dict[str, int]) -> List[Dict[str, str]]:
        findings: List[Dict[str, str]] = []
        
        ticket_id = payload.get("ticket_id", "N/A")
        category = payload.get("ticket_category", "general")
        content = payload.get("ticket_content", "")
        resolution_time = payload.get("resolution_time_hours")
        sentiment = payload.get("customer_sentiment", "neutral")
        
        # Detect FIP (Bank)
        fip = self._detect_fip(content)
        fip_freq = fip_counts.get(fip, 0) if fip else 0
        
        # 1. Check for systemic FIP downtime
        if fip and fip_freq >= 2:
            findings.append(
                self._build_finding(
                    event,
                    issue_cluster=f"SYSTEMIC_FIP_DOWNTIME ({fip})",
                    severity="high" if sentiment == "negative" or sentiment == "angry" else "medium",
                    recommended_action=f"Mark {fip} connector as degraded. Temporarily route new consent requests through fallback routes or show maintenance banner.",
                    frequency_score=str(fip_freq)
                )
            )
            
        # 2. Check for SLA Breaches
        elif isinstance(resolution_time, (int, float)) and resolution_time > 24:
            findings.append(
                self._build_finding(
                    event,
                    issue_cluster="SLA_BREACH",
                    severity="high" if sentiment == "negative" or sentiment == "angry" else "medium",
                    recommended_action=f"Ticket {ticket_id} has exceeded the 24h resolution SLA. Escalate to tier-2 support operations immediately.",
                    frequency_score="1"
                )
            )
            
        # 3. Consent approval loop issues
        elif "loop" in content.lower() or "stuck" in content.lower() or "consent redirect" in content.lower():
            findings.append(
                self._build_finding(
                    event,
                    issue_cluster="CONSENT_REDIRECT_LOOP",
                    severity="medium",
                    recommended_action="Inspect client redirect URL formatting and OAuth state parameters.",
                    frequency_score=str(fip_freq if fip_freq > 0 else 1)
                )
            )
            
        # 4. Default: Negative sentiment issues
        elif sentiment in ["negative", "angry"]:
            findings.append(
                self._build_finding(
                    event,
                    issue_cluster="UNHAPPY_CUSTOMER_ALERT",
                    severity="medium",
                    recommended_action=f"Prioritize ticket {ticket_id} for high-touch customer support. Customer sentiment is {sentiment}.",
                    frequency_score="1"
                )
            )

        for finding in findings:
            logger.info("Detected support issue", extra=finding)

        return findings

    def _build_finding(
        self,
        event: OperationalEvent,
        issue_cluster: str,
        severity: Severity,
        recommended_action: str,
        frequency_score: str
    ) -> Dict[str, str]:
        return {
            "event_id": event.event_id,
            "anomaly_type": issue_cluster,
            "severity": severity,
            "suggested_action": recommended_action,
            "frequency_score": frequency_score
        }
