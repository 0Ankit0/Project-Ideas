# Business Rules

This document defines enforceable policy rules for **Restaurant Management System** so command processing, asynchronous jobs, and operational actions behave consistently under normal and exceptional conditions.

## Context
- Domain focus: restaurant management workflows.
- Rule categories: lifecycle transitions, authorization, compliance, and resilience.
- Enforcement points: APIs, workflow/state engines, background processors, and administrative consoles.

## Enforceable Rules
1. Every state-changing command must pass authentication, authorization, and schema validation before processing.
2. Lifecycle transitions must follow the configured state graph; invalid transitions are rejected with explicit reason codes.
3. High-impact operations (financial, security, or regulated data actions) require additional approval evidence.
4. Manual overrides must include approver identity, rationale, and expiration timestamp.
5. Retries and compensations must be idempotent and must not create duplicate business effects.

## Rule Evaluation Pipeline
```mermaid
flowchart TD
    A[Incoming Command] --> B[Validate Payload]
    B --> C{Authorized Actor?}
    C -- No --> C1[Reject + Security Audit]
    C -- Yes --> D{Business Rules Pass?}
    D -- No --> D1[Reject + Rule Violation Event]
    D -- Yes --> E{State Transition Allowed?}
    E -- No --> E1[Return Conflict]
    E -- Yes --> F[Commit Transaction]
    F --> G[Publish Domain Event]
    G --> H[Update Read Models and Alerts]
```

## Exception and Override Handling
- Overrides are restricted to approved exception classes and require dual logging (business + security audit).
- Override windows automatically expire and trigger follow-up verification tasks.
- Repeated override patterns are reviewed for policy redesign and automation improvements.

## Cross-Flow Rule Set (Operationally Critical)

| Rule ID | Rule | Applies To | Enforcement Point |
|---------|------|------------|-------------------|
| BR-ORD-PEAK-001 | During surge/critical tiers, non-essential modifiers may require manager override | Ordering | Order command validators |
| BR-KIT-ROUTE-002 | Ticket reroute requires compatible station capability profile | Kitchen orchestration | Kitchen orchestrator |
| BR-SLOT-003 | No slot confirmation without atomic capacity lock | Slot management | Seating transaction boundary |
| BR-PAY-004 | Duplicate payment captures are forbidden under all retry paths | Payments | Billing payment adapter |
| BR-CAN-005 | Post-prep cancellation must capture reason and compensation policy outcome | Cancellations | Policy + order services |
| BR-OPS-006 | Tier de-escalation requires sustained recovery window and no active critical incident | Peak-load controls | Load control engine |

## Rule Conflict Resolution Order
1. Safety/compliance rules.
2. Financial integrity rules.
3. Inventory and kitchen feasibility rules.
4. Experience/SLA optimization rules.
