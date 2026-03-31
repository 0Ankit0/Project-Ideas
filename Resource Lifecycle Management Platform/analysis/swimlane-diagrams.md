# Swimlane Diagrams

Cross-actor swimlane diagrams showing who does what and when in the **Resource Lifecycle Management Platform**. Each diagram is organized by horizontal swimlane (one per actor/system) to make handoffs and responsibilities unambiguous.

---

## 1. Resource Provisioning Swimlane

```mermaid
flowchart LR
  subgraph RM ["Resource Manager"]
    RM1[Fill Provision Form\nor Upload CSV]
    RM2[Receive Success / Error Response]
  end
  subgraph API ["API Gateway"]
    A1[Validate JWT & Scope]
    A2[Route to Provisioning Service]
  end
  subgraph Prov ["Provisioning Service"]
    P1[Validate Schema & Template]
    P2[Check Quota via Policy Engine]
    P3[Assign resource_id\nWrite Pending Record]
    P4[Transition to Available]
  end
  subgraph Events ["Event Bus / Outbox"]
    E1[Publish rlmp.resource.provisioned]
  end
  subgraph Audit ["Audit Writer"]
    AU1[Write Audit Record]
  end

  RM1 --> A1 --> A2 --> P1
  P1 -->|Invalid| RM2
  P1 -->|Valid| P2
  P2 -->|Quota Exceeded| RM2
  P2 -->|OK| P3 --> P4 --> E1 --> AU1
  P4 --> RM2
```

---

## 2. Reservation and Allocation Swimlane

```mermaid
flowchart LR
  subgraph REQ ["Requestor"]
    R1[Submit Reservation\nwith idempotency_key]
    R2[Receive 201 / 409 Response]
    R3[Receive Checkout Notification]
  end
  subgraph ALLOC ["Allocation Service"]
    A1[Check Idempotency Key]
    A2[Acquire Optimistic Lock\non resource+window]
    A3[Check Window Overlap]
    A4[Create CONFIRMED Reservation\nSet SLA Timer]
  end
  subgraph PE ["Policy Engine"]
    P1[Evaluate Quota,\nEligibility, Priority]
  end
  subgraph CUST ["Custodian"]
    C1[Scan Asset Tag / Submit Checkout]
    C2[Record Checkout Condition]
  end
  subgraph CUSTODY ["Custody Service"]
    CS1[Validate Reservation in Window]
    CS2[Create Allocation Record\nTransition Resource to Allocated]
    CS3[Register with Overdue Detector]
  end
  subgraph BUS ["Event Bus"]
    E1[rlmp.reservation.created]
    E2[rlmp.allocation.checked_out]
  end

  R1 --> A1
  A1 -->|Duplicate Key| R2
  A1 -->|New| A2 --> A3
  A3 -->|Conflict| R2
  A3 -->|No Conflict| P1
  P1 -->|Deny| R2
  P1 -->|Permit| A4 --> E1 --> R2

  R3 --> C1 --> CS1
  CS1 -->|Outside Window| R2
  CS1 -->|OK| C2 --> CS2 --> CS3 --> E2
```

---

## 3. Check-In and Condition Assessment Swimlane

```mermaid
flowchart LR
  subgraph CUST ["Custodian"]
    C1[Scan Asset Tag\nSubmit Check-In + Condition Grade]
  end
  subgraph CUSTODY ["Custody Service"]
    CS1[Validate Actor Authorization]
    CS2[Compute Condition Delta]
    CS3[Update Allocation - checkin_at, state=RETURNED]
    CS4[Transition Resource to Inspection]
  end
  subgraph INC ["Incident Service"]
    I1[Open Incident Case\nif delta = MAJOR or LOSS]
  end
  subgraph INSP ["Inspection Workflow"]
    IN1[Inspector Reviews Asset]
    IN2{Pass?}
  end
  subgraph RES ["Resource State"]
    RS1[Available]
    RS2[Maintenance]
  end
  subgraph BUS ["Event Bus"]
    E1[rlmp.allocation.checked_in]
    E2[rlmp.incident.opened]
  end

  C1 --> CS1 --> CS2
  CS2 -->|NONE/MINOR| CS3 --> CS4
  CS2 -->|MAJOR/LOSS| I1 --> E2 --> CS3 --> CS4
  CS4 --> E1
  CS4 --> IN1 --> IN2
  IN2 -->|Yes| RS1
  IN2 -->|No| RS2
```

---

## 4. Overdue Escalation Swimlane

```mermaid
flowchart LR
  subgraph DET ["Overdue Detector\n(System - 5 min cron)"]
    D1[Scan Active Allocations]
    D2[Detect due_at passed]
    D3[Mark OVERDUE]
  end
  subgraph ESC ["Escalation Engine"]
    E1[Step 1 - Notify Custodian T+0]
    E2[Step 2 - Warn Custodian + Manager T+4h]
    E3[Step 3 - Escalate to Manager T+24h]
    E4[Step 4 - Forced Return Eligible T+48h]
  end
  subgraph OPS ["Operations"]
    O1[Review Ops Dashboard]
    O2[Initiate Forced Return\nwith Approver + Reason]
  end
  subgraph NOTIF ["Notification Service"]
    N1[Send Email / Push]
  end
  subgraph BUS ["Event Bus"]
    B1[rlmp.allocation.overdue]
    B2[rlmp.escalation.warned]
    B3[rlmp.escalation.manager_escalated]
    B4[rlmp.escalation.forced_return_eligible]
    B5[rlmp.allocation.forced_return]
  end

  D1 --> D2 --> D3 --> B1 --> E1 --> N1
  E1 -->|T+4h, no checkin| E2 --> B2 --> N1
  E2 -->|T+24h, no checkin| E3 --> B3 --> N1
  E3 -->|T+48h, no checkin| E4 --> B4 --> O1
  O1 --> O2 --> B5
```

---

## 5. Settlement and Incident Resolution Swimlane

```mermaid
flowchart LR
  subgraph INC ["Incident Service"]
    I1[Open Incident Case]
    I2[Assign Owner + SLA]
    I3[Update Case Status]
  end
  subgraph SETTLE ["Settlement Service"]
    S1[Compute Charge\nusing Rate Card]
    S2[Create Settlement Record - PENDING]
    S3[Post Charge to Ledger via Outbox]
  end
  subgraph FIN ["Finance"]
    F1[Review Settlement Dashboard]
    F2[Approve or Dispute Charge]
  end
  subgraph LEDGER ["Financial Ledger"]
    L1[Receive Exactly-Once Event]
    L2[Journal Entry Created]
  end
  subgraph CUST ["Custodian / Requestor"]
    C1[Receive Notification]
    C2[Dispute Charge]
  end
  subgraph BUS ["Event Bus"]
    B1[rlmp.incident.opened]
    B2[rlmp.settlement.calculated]
    B3[rlmp.settlement.posted]
    B4[rlmp.settlement.disputed]
  end

  I1 --> B1 --> I2
  I2 --> I3 --> S1 --> B2 --> S2
  S2 --> F1 --> F2
  F2 -->|Approve| S3 --> B3 --> L1 --> L2
  F2 -->|Dispute| C1 --> C2 --> B4
  B4 --> INC
```

---

## Cross-References

- Activity diagrams (decision detail): [activity-diagrams.md](./activity-diagrams.md)
- System sequence diagrams: [../high-level-design/system-sequence-diagrams.md](../high-level-design/system-sequence-diagrams.md)
- Business rules driving each handoff: [business-rules.md](./business-rules.md)
