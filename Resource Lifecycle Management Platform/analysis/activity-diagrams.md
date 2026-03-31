# Activity Diagrams

Activity diagrams showing the detailed flow of each major lifecycle process in the **Resource Lifecycle Management Platform**. Each diagram captures actors, decisions, parallel paths, and exception branches.

---

## 1. Resource Provisioning Activity

```mermaid
flowchart TD
  Start([Resource Manager Initiates Provision]) --> UploadCheck{Single or Bulk?}

  UploadCheck -->|Single| SingleForm[Submit Provision Form]
  UploadCheck -->|Bulk| CSVUpload[Upload CSV File]

  CSVUpload --> ValidateCSV{All Rows Valid?}
  ValidateCSV -->|No| CSVError[Return Per-Row Error Report]
  CSVError --> End1([End - No Records Created])
  ValidateCSV -->|Yes| BatchProcess[Process Batch Transactionally]

  SingleForm --> ValidateSchema{Schema Valid?}
  ValidateSchema -->|No| SchemaError[Return 400 Validation Error]
  SchemaError --> End2([End])
  ValidateSchema -->|Yes| PolicyCheck

  BatchProcess --> PolicyCheck{Entitlement & Quota OK?}
  PolicyCheck -->|No| QuotaError[Return 422 Quota Exceeded]
  QuotaError --> End3([End])
  PolicyCheck -->|Yes| AssignID[Assign resource_id & Write Pending Record]
  AssignID --> FieldCheck{All Mandatory Fields Present?}
  FieldCheck -->|No| StayPending[Resource Stays in Pending State]
  FieldCheck -->|Yes| TransitionAvailable[Transition to Available State]
  TransitionAvailable --> PublishEvent[Publish rlmp.resource.provisioned]
  PublishEvent --> Return201[Return 201 Created with resource_id]
  Return201 --> End4([End - Success])
```

---

## 2. Reservation Request Activity

```mermaid
flowchart TD
  Start([Requestor Submits Reservation]) --> IdempCheck{Idempotency Key Exists?}
  IdempCheck -->|Yes| ReturnOriginal[Return Original Reservation Response]
  ReturnOriginal --> End1([End])

  IdempCheck -->|No| AuthCheck{Authenticated & Authorized?}
  AuthCheck -->|No| Reject401[Reject 401 / 403]
  Reject401 --> End2([End])

  AuthCheck -->|Yes| AcquireLock[Acquire Optimistic Lock on resource+window]
  AcquireLock --> OverlapCheck{Window Overlaps Existing Reservation?}
  OverlapCheck -->|Yes| Return409[Return 409 Conflict + Alternatives]
  Return409 --> End3([End])

  OverlapCheck -->|No| PolicyEval{Policy Evaluation: Quota, Eligibility, Time Limit}
  PolicyEval -->|Deny| PolicyDeny[Return 422 Policy Denied]
  PolicyDeny --> End4([End])

  PolicyEval -->|Permit| PriorityCheck{Higher Priority Reservation Pending?}
  PriorityCheck -->|Yes, same window| Displace[Displace Lower Priority Reservation]
  Displace --> NotifyDisplaced[Notify Displaced Requestor]
  NotifyDisplaced --> CreateReservation

  PriorityCheck -->|No| CreateReservation[Create CONFIRMED Reservation Record]
  CreateReservation --> SetSLA[Set SLA Timer for Checkout Window]
  SetSLA --> PublishEvent[Publish rlmp.reservation.created]
  PublishEvent --> Return201[Return 201 Created with reservation_id + sla_due_at]
  Return201 --> End5([End - Success])
```

---

## 3. Checkout and Check-In Activity

```mermaid
flowchart TD
  Start([Custodian Scans Asset Tag]) --> LookupReservation[Lookup Active Reservation]
  LookupReservation --> WindowCheck{Within Checkout SLA Window?}
  WindowCheck -->|No| WindowError[Return 422 Checkout Window Expired]
  WindowError --> End1([End])

  WindowCheck -->|Yes| ResourceStateCheck{Resource State = Available or Reserved?}
  ResourceStateCheck -->|No| StateError[Return 409 Resource Unavailable]
  StateError --> End2([End])

  ResourceStateCheck -->|Yes| RecordCheckoutCondition[Record Condition Grade at Checkout]
  RecordCheckoutCondition --> TransitionAllocated[Transition Resource: Available → Allocated]
  TransitionAllocated --> CreateAllocation[Create Allocation Record with checkout_at and due_at]
  CreateAllocation --> RegisterOverdue[Register Allocation with Overdue Detector]
  RegisterOverdue --> PublishCheckout[Publish rlmp.allocation.checked_out]
  PublishCheckout --> Return201[Return 201 with allocation_id]
  Return201 --> Active

  Active([Resource In Use - ACTIVE State]) --> DueApproaching{Due Date Approaching?}
  DueApproaching -->|24h before| Send24hReminder[Send 24h Reminder Notification]
  Send24hReminder --> Active
  DueApproaching -->|2h before| Send2hReminder[Send 2h Reminder Notification]
  Send2hReminder --> Active
  DueApproaching -->|Due Date Passed| TriggerOverdue[Trigger Overdue Flow]
  TriggerOverdue --> OverdueProcess([See Overdue Activity Diagram])

  Active --> ReturnAction{Custodian Returns Resource}
  ReturnAction --> RecordCheckinCondition[Record Condition Grade at Check-In]
  RecordCheckinCondition --> ComputeDelta{Condition Delta?}
  ComputeDelta -->|None / Minor| TransitionInspection[Transition to Inspection State]
  ComputeDelta -->|Major / Loss| OpenIncident[Open Incident Case] --> TransitionInspection

  TransitionInspection --> InspectionPass{Inspection Pass?}
  InspectionPass -->|Pass| TransitionAvailable2[Transition to Available]
  InspectionPass -->|Fail| TransitionMaintenance[Transition to Maintenance]
  TransitionAvailable2 --> PublishCheckin[Publish rlmp.allocation.checked_in]
  TransitionMaintenance --> PublishCheckin
  PublishCheckin --> End3([End - Check-In Complete])
```

---

## 4. Overdue Escalation Activity

```mermaid
flowchart TD
  Start([Overdue Detector Job - Every 5 Min]) --> ScanActive[Scan All ACTIVE Allocations]
  ScanActive --> OverdueFound{Any allocation.due_at < now?}
  OverdueFound -->|No| End1([End - No Action])

  OverdueFound -->|Yes| MarkOverdue[Update Allocation State to OVERDUE]
  MarkOverdue --> PublishOverdue[Publish rlmp.allocation.overdue - Step 1]
  PublishOverdue --> Notify[Notify Custodian - T+0]

  Notify --> Wait4h{T+4h Elapsed Without Checkin?}
  Wait4h -->|No| WaitMore([Continue Monitoring])
  Wait4h -->|Yes| WarnEscalation[Warn Custodian + Manager - Step 2]
  WarnEscalation --> PublishWarn[Publish rlmp.escalation.warned]

  PublishWarn --> Wait24h{T+24h Elapsed?}
  Wait24h -->|No| WaitMore2([Continue])
  Wait24h -->|Yes| ManagerEscalation[Escalate to Manager - Step 3]
  ManagerEscalation --> PublishManager[Publish rlmp.escalation.manager_escalated]

  PublishManager --> Wait48h{T+48h Elapsed?}
  Wait48h -->|No| WaitMore3([Continue])
  Wait48h -->|Yes| ForcedReturnEligible[Flag as Forced Return Eligible - Step 4]
  ForcedReturnEligible --> PublishForcedEligible[Publish rlmp.escalation.forced_return_eligible]
  PublishForcedEligible --> OpsReview{Ops Initiates Forced Return?}
  OpsReview -->|Yes| ForcedReturn[Execute Forced Return with Approver + Reason]
  ForcedReturn --> PublishForcedReturn[Publish rlmp.allocation.forced_return]
  PublishForcedReturn --> InspectionFlow([Initiate Inspection Flow])
  OpsReview -->|No| ContinueMonitor([Continue Monitoring - Manual Intervention Required])
```

---

## 5. Decommission Activity

```mermaid
flowchart TD
  Start([Manager Requests Decommission]) --> PreCheck{All Preconditions Met?}
  PreCheck -->|No| BlockError[Return 409 Decommission Blocked\nList Blocking Entities]
  BlockError --> End1([End])

  PreCheck -->|Yes| ValueCheck{Asset Value >= Approval Threshold?}
  ValueCheck -->|Yes| TriggerApproval[Trigger Approval Workflow]
  TriggerApproval --> WaitApproval{Approval Received?}
  WaitApproval -->|Rejected| RejectDecommission[Return Rejected with Reason]
  RejectDecommission --> End2([End])
  WaitApproval -->|Approved| ProceedDecommission

  ValueCheck -->|No| ProceedDecommission[Transition Resource to Decommissioning State]
  ProceedDecommission --> PublishApproved[Publish rlmp.resource.decommission_approved]
  PublishApproved --> QueueArchive[Queue Archive Job]
  QueueArchive --> ArchiveComplete{Archive Completed Within 24h?}
  ArchiveComplete -->|No| ArchiveAlert[Alert Operations - Archive Job Failed]
  ArchiveComplete -->|Yes| TransitionDecommissioned[Transition Resource to Decommissioned - Terminal]
  TransitionDecommissioned --> PublishDecommissioned[Publish rlmp.resource.decommissioned]
  PublishDecommissioned --> PublishArchived[Publish rlmp.resource.archived with manifest_id]
  PublishArchived --> End3([End - Decommission Complete])
```

---

## Cross-References

- State transitions: [../detailed-design/state-machine-diagrams.md](../detailed-design/state-machine-diagrams.md)
- Swimlane diagrams: [swimlane-diagrams.md](./swimlane-diagrams.md)
- Sequence diagrams: [../detailed-design/sequence-diagrams.md](../detailed-design/sequence-diagrams.md)
