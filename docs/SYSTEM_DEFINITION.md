A. System Goal

The system is an AI-assisted operations health monitoring platform designed for fintech teams.
It helps operations teams detect, analyze, and safely resolve issues in payment processing, billing workflows, and customer support operations, while keeping humans in control of all high-risk actions.

B. Final Agent List (Frozen)

Ops Orchestrator Agent
Coordinates all agents, routes operational events, and controls execution order.

Payment Ops Monitor Agent
Monitors payment transactions and gateway events to detect anomalies and operational failures.

Billing Ops Guardian Agent
Monitors invoice generation, subscription billing, and charge consistency to detect billing issues.

Support Ops Intelligence Agent
Analyzes customer support tickets and interaction data to identify recurring issues and bottlenecks.

Audit & Safety Agent
Validates all suggested or executed actions, enforces safety rules, and maintains audit logs.

C. Inputs & Outputs
| Agent                          | Inputs                             | Outputs                              |
| ------------------------------ | ---------------------------------- | ------------------------------------ |
| Ops Orchestrator Agent         | Batched operational events         | Routed tasks to agents               |
| Payment Ops Monitor Agent      | Transaction logs, gateway events   | Payment anomalies                    |
| Billing Ops Guardian Agent     | Invoice data, subscription records | Billing discrepancies                |
| Support Ops Intelligence Agent | Support tickets, metadata          | Issue patterns & insights            |
| Audit & Safety Agent           | Proposed actions                   | Approved actions or escalation flags |

D. Explicit Non-Goals (Safety Boundaries)

The system will NOT:

Make final financial decisions

Execute refunds or payouts

Modify customer accounts

Perform real monetary transactions

Replace human operational ownership

All high-risk actions require human review and approval.
