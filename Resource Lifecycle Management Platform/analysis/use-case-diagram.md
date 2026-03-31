# Use Case Diagram

Visual overview of all primary actors and their relationships to use cases in the **Resource Lifecycle Management Platform**.

## Actors

| Actor | Type | Description |
|---|---|---|
| Requestor | Primary | Searches catalog and submits reservation requests |
| Custodian | Primary | Checks out and returns resources; holds custody |
| Resource Manager | Primary | Manages catalog, policies, approvals, and decommissioning |
| Compliance Officer | Primary | Reviews audit evidence and manages retention policies |
| Finance | Primary | Manages settlement cases and financial reconciliation |
| Operations / SRE | Primary | Operates exception runbooks and monitors platform health |
| Overdue Detector | System | Scheduled job that detects and escalates overdue allocations |
| Policy Engine | System | Evaluates quota, eligibility, and priority rules |
| Archive Job | System | Moves decommissioned records to cold storage |

## Use Case Diagram

```mermaid
flowchart LR
  %% Actors
  Requestor([Requestor])
  Custodian([Custodian])
  Manager([Resource Manager])
  Compliance([Compliance Officer])
  Finance([Finance])
  Ops([Operations / SRE])
  Detector([Overdue Detector - System])
  PolicyEng([Policy Engine - System])
  ArchiveJob([Archive Job - System])

  %% Resource Catalog Use Cases
  Requestor --> SearchCatalog((Search Catalog))
  Manager --> ProvisionResource((Provision Resource))
  Manager --> BulkProvision((Bulk Provision via CSV))
  Manager --> ManagePolicy((Manage Allocation Policies))
  Manager --> ScheduleMaintenance((Schedule Maintenance Window))

  %% Reservation Use Cases
  Requestor --> CreateReservation((Create Reservation))
  Requestor --> CancelReservation((Cancel Reservation))
  Requestor --> ExtendAllocation((Request Extension))
  CreateReservation --> PolicyEng
  CreateReservation --> CheckConflict((Check Window Conflict))

  %% Allocation / Custody Use Cases
  Custodian --> CheckOut((Check Out Resource))
  Custodian --> CheckIn((Check In Resource))
  Custodian --> TransferCustody((Transfer Custody))
  Custodian --> ReportLoss((Report Loss / Damage))
  CheckOut --> PolicyEng
  CheckIn --> RecordCondition((Record Condition Grade))

  %% Overdue / Escalation Use Cases
  Detector --> DetectOverdue((Detect Overdue Allocation))
  DetectOverdue --> EscalateLadder((Escalate via Ladder))
  Ops --> ForceReturn((Initiate Forced Return))
  EscalateLadder --> ForceReturn

  %% Incident / Settlement Use Cases
  ReportLoss --> OpenIncident((Open Incident Case))
  RecordCondition --> OpenIncident
  Finance --> ReviewSettlement((Review Settlement Cases))
  Finance --> PostCharge((Post Damage Charge))
  Requestor --> DisputeCharge((Dispute Settlement Charge))
  OpenIncident --> ReviewSettlement

  %% Decommissioning Use Cases
  Manager --> RequestDecommission((Request Decommission))
  Manager --> ApproveDecommission((Approve Decommission))
  ArchiveJob --> ArchiveRecords((Archive Resource Records))
  RequestDecommission --> ApproveDecommission --> ArchiveRecords

  %% Compliance / Audit Use Cases
  Compliance --> PullAuditTrail((Pull Audit Trail))
  Compliance --> ManageRetention((Manage Retention Policy))
  Compliance --> ReviewOverrides((Review Override Report))

  %% Operations Use Cases
  Ops --> ViewEventStream((View Live Event Stream))
  Ops --> ReplayDLQ((Replay DLQ Message))
  Ops --> ViewDashboard((View Utilization Dashboard))
```

## Actor–Use Case Summary

| Actor | Primary Use Cases |
|---|---|
| Requestor | Search Catalog, Create Reservation, Cancel Reservation, Request Extension, Dispute Settlement Charge |
| Custodian | Check Out, Check In, Transfer Custody, Report Loss/Damage |
| Resource Manager | Provision Resource, Bulk Provision, Manage Policy, Schedule Maintenance, Request & Approve Decommission |
| Compliance Officer | Pull Audit Trail, Manage Retention, Review Override Report |
| Finance | Review Settlement Cases, Post Damage Charge |
| Operations / SRE | Forced Return, View Event Stream, Replay DLQ, View Dashboard |
| Overdue Detector | Detect Overdue, Escalate via Ladder |
| Policy Engine | Evaluate Quota, Eligibility, Priority |
| Archive Job | Archive Resource Records |

## Cross-References

- Detailed use case flows: [use-case-descriptions.md](./use-case-descriptions.md)
- Actor authorization rules: [business-rules.md](./business-rules.md)
- Functional requirements per use case: [../requirements/requirements.md](../requirements/requirements.md)
