from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Any, Optional

EventType = Literal["payment", "billing", "support"]
Severity = Literal["low", "medium", "high"]
Decision = Literal["APPROVED", "ESCALATE_TO_HUMAN"]

class OperationalEventPayload(BaseModel):
    # Payment fields
    transaction_id: Optional[str] = None
    payment_status: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    gateway: Optional[str] = None
    gateway_response_code: Optional[str] = None
    processing_time_seconds: Optional[float] = None

    # Billing fields
    invoice_id: Optional[str] = None
    customer_id: Optional[str] = None
    subscription_plan: Optional[str] = None
    charged_amount: Optional[float] = None
    expected_amount: Optional[float] = None
    billing_cycle: Optional[str] = None
    data_session_status: Optional[str] = None
    data_transfer_count: Optional[int] = None
    max_allowed_transfers: Optional[int] = None
    is_duplicate_invoice: Optional[bool] = None

    # Support fields
    ticket_id: Optional[str] = None
    ticket_category: Optional[str] = None
    ticket_content: Optional[str] = None
    resolution_time_hours: Optional[float] = None
    customer_sentiment: Optional[str] = None

class OperationalEventSchema(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Category of operations event")
    timestamp: str = Field(..., description="ISO timestamp of event occurrence")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Raw dictionary payload")

class FindingSchema(BaseModel):
    event_id: str
    anomaly_type: str
    severity: Severity
    suggested_action: str
    impacted_customers: Optional[str] = "1"
    frequency_score: Optional[str] = "1"

class DecisionRecordSchema(BaseModel):
    event_id: str
    decision: Decision
    reason: str

class OpsHealthCheckRequest(BaseModel):
    events: List[OperationalEventSchema]

class OpsHealthCheckResponse(BaseModel):
    decisions: List[DecisionRecordSchema]
