import logging
from dataclasses import dataclass
from typing import List, Literal, TypedDict


logger = logging.getLogger(__name__)

EventType = Literal["payment", "billing", "support"]
QueueName = Literal["payment_tasks", "billing_tasks", "support_tasks"]


@dataclass(frozen=True)
class OperationalEvent:
    event_id: str
    event_type: EventType
    payload: dict
    timestamp: str


class RoutingResult(TypedDict):
    payment_tasks: List[OperationalEvent]
    billing_tasks: List[OperationalEvent]
    support_tasks: List[OperationalEvent]


class OpsOrchestratorAgent:
    """
    Control-plane agent responsible for deterministic routing of operational events
    to domain-specific task queues.

    This agent does NOT execute domain logic. It only orchestrates event dispatch.
    """

    def route_events(self, events: List[OperationalEvent]) -> RoutingResult:
        """
        Routes incoming operational events to their corresponding queues
        based solely on event type.
        """
        result: RoutingResult = {
            "payment_tasks": [],
            "billing_tasks": [],
            "support_tasks": [],
        }

        if not events:
            logger.warning("No events to route; received empty input list.")
            return result

        for event in events:
            queue_name = self._get_queue_name(event)
            result[queue_name].append(event)
            logger.info(
                "Routed event",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "queue": queue_name,
                },
            )

        return result

    def _get_queue_name(self, event: OperationalEvent) -> QueueName:
        if event.event_type == "payment":
            return "payment_tasks"
        if event.event_type == "billing":
            return "billing_tasks"
        if event.event_type == "support":
            return "support_tasks"
        raise ValueError(f"Unsupported event_type: {event.event_type}")
