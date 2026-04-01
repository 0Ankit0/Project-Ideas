# State Machine Diagrams — Manufacturing Execution System

## Overview

This document specifies the state machines governing the lifecycle of all major MES entities. State machines are the authoritative source of truth for the `status` fields in the database schema and the transition validation logic in service layers. They enforce that entities can only move between valid states and that required side effects (guard conditions and entry actions) are satisfied before a transition is allowed.

Each diagram uses Mermaid `stateDiagram-v2` notation. Guard conditions are expressed in square brackets `[condition]`. Actions triggered on a transition are written after a forward-slash `/`. Composite states group logically related sub-states where the entity behaviour diverges into sub-workflows.

Allowed status values for each entity are derived directly from these diagrams and enforced via `CHECK` constraints in the database schema and enum validation in service request handlers.

---

## Production Order State Machine

A production order progresses from initial creation through scheduling, active execution, hold/resume cycles, and eventual closure. Cancellation is permitted only when no work orders have been started. The `PartiallyComplete` state captures the common scenario where some operations are done but others are still in progress, allowing the order to resume without a full reset.

```mermaid
stateDiagram-v2
    [*] --> Created : ERP sync received / manual creation

    Created --> Scheduled : schedule() [routing and BOM effectivity valid]
    Created --> Cancelled : cancel() [no work orders started] / log cancellation reason

    Scheduled --> Released : release() [material availability confirmed by Material Service]
    Scheduled --> MaterialShortage : materialCheck() [one or more BOM components unavailable]
    Scheduled --> Cancelled : cancel() [no work orders started]

    MaterialShortage --> Scheduled : reschedule() [shortage resolved, new date assigned]
    MaterialShortage --> Cancelled : cancel() [approved by production supervisor]

    Released --> InProgress : firstWorkOrder.start() / set actualStartDate = NOW()
    Released --> OnHold : hold(reason) [quality embargo or material recall]
    Released --> Cancelled : cancel() [no work orders started, approved]

    InProgress --> OnHold : hold(reason) / pause all RUNNING and READY work orders
    InProgress --> PartiallyComplete : partialCompletion() [some work orders closed, others pending]
    InProgress --> Completed : allWorkOrdersComplete() [completedQty + scrapQty >= plannedQty]

    PartiallyComplete --> InProgress : continueProduction() / resume remaining work orders
    PartiallyComplete --> OnHold : hold(reason)
    PartiallyComplete --> Completed : finalWorkOrderComplete()

    OnHold --> InProgress : resume() [hold reason resolved, approved by supervisor] / resume paused work orders
    OnHold --> PartiallyComplete : resumePartial() [only subset of work orders can resume]
    OnHold --> Cancelled : cancel() [approved by plant manager]

    Completed --> Closed : close() [GR posted to ERP, inspection records finalized] / set actualEndDate
    Completed --> InProgress : reopen(reason) [quantity correction required, approved]

    Closed --> [*]
    Cancelled --> [*]
```

**Status values:** `CREATED`, `SCHEDULED`, `MATERIAL_SHORTAGE`, `RELEASED`, `IN_PROGRESS`, `PARTIALLY_COMPLETE`, `ON_HOLD`, `COMPLETED`, `CLOSED`, `CANCELLED`

---

## Work Order State Machine

Work orders represent individual routing steps within a production order. They advance through scheduling, setup preparation, active execution, and completion, with provisions for rework loops initiated by failed quality inspections and quality holds placed on output material. A work order can only be cancelled while it has not yet started active production.

```mermaid
stateDiagram-v2
    [*] --> Pending : created from production order release

    Pending --> Scheduled : schedule() [work center capacity slot confirmed]
    Pending --> Cancelled : cancel() [parent production order cancelled]

    Scheduled --> ReadyToStart : materialsReady() [all components issued or reserved in FEFO order]
    Scheduled --> Cancelled : cancel() [parent order cancelled before setup begins]

    ReadyToStart --> SetupInProgress : beginSetup(setupPersonId) / record setupStartAt = NOW()
    ReadyToStart --> Cancelled : cancel() [approved, components unreserved]

    SetupInProgress --> ReadyToRun : completeSetup() [setup duration recorded, machine verified]
    SetupInProgress --> SetupOnHold : hold(reason) [tooling or fixture issue]

    SetupOnHold --> SetupInProgress : resume() [setup issue resolved]

    ReadyToRun --> InProgress : start(operatorId, machineId) / start cycle timer, push recipe to PLC
    ReadyToRun --> Cancelled : cancel() [approved by supervisor, setup reversed]

    InProgress --> Paused : pause(reason) / record downtime event, update OEE availability
    InProgress --> QualityHold : inspectionFailed() / quarantine output lot, open NCR
    InProgress --> PartialComplete : reportPartial(completedQty) [completedQty < plannedQty]
    InProgress --> Completed : complete(qty, scrap) [completedQty + scrapQty >= plannedQty]

    Paused --> InProgress : resume() / close downtime event, restart cycle timer
    Paused --> Cancelled : cancel() [approved by supervisor, no completed units]

    QualityHold --> InProgress : ncrDispositioned(REWORK) / create rework work order, re-enter qty
    QualityHold --> Completed : ncrDispositioned(ACCEPT_AS_IS) [deviation approved]
    QualityHold --> Scrapped : ncrDispositioned(SCRAP) / post scrap movement to ERP

    PartialComplete --> InProgress : continueProduction() [remaining qty > 0]
    PartialComplete --> Completed : complete(remainingQty, scrap)

    Completed --> Closed : close() [quality inspection passed, GI confirmed in ERP]
    Completed --> QualityHold : postCompletionInspectionFailed() [final inspection failed]

    Closed --> [*]
    Cancelled --> [*]
    Scrapped --> [*]
```

**Status values:** `PENDING`, `SCHEDULED`, `READY_TO_START`, `SETUP_IN_PROGRESS`, `SETUP_ON_HOLD`, `READY_TO_RUN`, `IN_PROGRESS`, `PAUSED`, `QUALITY_HOLD`, `PARTIAL_COMPLETE`, `COMPLETED`, `CLOSED`, `CANCELLED`, `SCRAPPED`

---

## Operation State Machine

Operations are the finest-grained executable units in the MES, bound to a specific machine and operator. Cycle time monitoring occurs continuously in the `InProgress` state. A cycle time breach triggers an alert sub-state that requires operator acknowledgement before production continues. Failed operations require explicit resolution before a retry is permitted to prevent repeated machine damage or scrap generation.

```mermaid
stateDiagram-v2
    [*] --> Pending : created from work order start()

    Pending --> InProgress : begin(machineId, operatorId) [machine IDLE and operator certified for operationCode]
    Pending --> Skipped : skip() [operation marked optional AND skip approved by quality engineer]

    InProgress --> Paused : pause(reason) / log downtime start, suspend cycle timer
    InProgress --> CycleTimeBreached : cycleTimerAlert() [actualTime > 120% of plannedCycleTimeSecs] / notify supervisor
    InProgress --> Failed : reportFailure(reason) / stop machine via SCADA stopMachine(), log failure
    InProgress --> Completed : complete(notes) [all mandatory parameters logged, no open alerts]

    CycleTimeBreached --> InProgress : acknowledge(reason) / log deviation, reset alert, continue timer
    CycleTimeBreached --> Failed : reportFailure(reason) / escalate to maintenance

    Paused --> InProgress : resume() [downtime event closed, machine restarted]
    Paused --> Failed : reportFailure(reason) [machine fault detected during pause]
    Paused --> Cancelled : cancel() [parent work order cancelled]

    Failed --> InProgress : retry() [machine reset confirmed, supervisor approved retry] / clear failure flag
    Failed --> Cancelled : cancel() [unrecoverable fault, work order rerouted to alternate work center]

    Completed --> [*]
    Skipped --> [*]
    Cancelled --> [*]
```

**Status values:** `PENDING`, `IN_PROGRESS`, `PAUSED`, `CYCLE_TIME_BREACHED`, `FAILED`, `COMPLETED`, `SKIPPED`, `CANCELLED`

---

## Machine State Machine

A machine transitions between operational modes based on production events, maintenance schedules, and SCADA signals. Accurate and timely machine state recording is the primary driver of OEE availability calculations. Breakdown detection can originate from a SCADA alarm subscription or from an operator report, triggering immediate maintenance notification.

```mermaid
stateDiagram-v2
    [*] --> Offline : initial asset provisioning / SCADA node registered

    Offline --> Idle : activate() [safety check passed, maintenance cleared, commissioning complete]
    Offline --> UnderMaintenance : scheduledCommissioning() [pre-activation maintenance required]

    Idle --> Running : assignOperation(operationId) [work order operation started, recipe loaded]
    Idle --> Setup : beginSetup(workOrderId) [work order setup phase started]
    Idle --> UnderMaintenance : maintenanceDue() [nextMaintenanceDate reached or work order raised]
    Idle --> Offline : decommission() [asset end-of-life approved]

    Setup --> Idle : setupComplete() [setup signed off, machine ready for production]
    Setup --> Breakdown : breakdownDetected(alarmCode) / alert maintenance team, log event

    Running --> Idle : operationComplete() / clear currentOperationId, update cycle count
    Running --> Breakdown : breakdownDetected(alarmCode) / stop operation, alert maintenance, open downtime event
    Running --> PlannedDowntime : plannedStop(reason) [shift end, changeover, scheduled break] / pause operation
    Running --> UnplannedDowntime : unplannedStop(reason) [SCADA signal lost, safety trip, operator report]

    PlannedDowntime --> Running : restart() [downtime event closed, machine safe to run] / resume operation, log planned loss
    PlannedDowntime --> Idle : cancelOperation() [production order cancelled mid-run]
    PlannedDowntime --> UnderMaintenance : opportunisticMaintenance() [maintenance team uses planned stop window]

    UnplannedDowntime --> Running : restart() [issue resolved, operator confirmed safe] / resume operation, log unplanned loss
    UnplannedDowntime --> Breakdown : escalate() [root cause cannot be resolved on floor, maintenance required]

    Breakdown --> UnderMaintenance : maintenanceStarted(technicianId) / create maintenance work order
    UnderMaintenance --> Idle : maintenanceComplete() [work order closed, safety re-check passed, parts signed off]
    UnderMaintenance --> Offline : decommission() [machine condemned during maintenance, asset retired]
```

**Status values:** `OFFLINE`, `IDLE`, `SETUP`, `RUNNING`, `PLANNED_DOWNTIME`, `UNPLANNED_DOWNTIME`, `BREAKDOWN`, `UNDER_MAINTENANCE`

---

## Quality Hold State Machine

A quality hold is placed on a production order, work order, or material lot when an inspection fails, an SPC rule violation is detected, or a customer complaint is received. The hold must pass through a formal review and disposition workflow before affected material can be released or scrapped. SLA timers govern review and disposition deadlines; breaches escalate automatically.

```mermaid
stateDiagram-v2
    [*] --> Open : triggered by failed inspection, SPC violation, or customer complaint / quarantine affected lots

    Open --> UnderReview : assignReviewer(qualityEngineerId) [reviewer assigned within 4-hour SLA]
    Open --> Escalated : slaBreached() [4-hour assignment SLA exceeded] / notify quality manager
    Open --> Escalated : criticalSeverity() [NCR severity = CRITICAL] / immediate escalation path

    UnderReview --> RootCauseAnalysis : requireRCA() [severity = MAJOR or CRITICAL, or repeat defect]
    UnderReview --> PendingDisposition : reviewComplete(findings) [root cause identified, evidence documented]
    UnderReview --> Escalated : escalate(reason) [scope exceeds reviewer authority]

    RootCauseAnalysis --> PendingDisposition : rcaComplete(causeCode, correctiveAction, targetDate)
    RootCauseAnalysis --> Escalated : escalate(reason) [systemic issue requiring cross-functional team]

    PendingDisposition --> AcceptAsIs : dispose(ACCEPT_AS_IS) [approved by quality manager] / create deviation record
    PendingDisposition --> Rework : dispose(REWORK) [rework instructions authored and approved]
    PendingDisposition --> Scrap : dispose(SCRAP) [approved by quality manager and plant controller]
    PendingDisposition --> ReturnToSupplier : dispose(RETURN_TO_VENDOR) [supplier defect confirmed, RMA raised]

    AcceptAsIs --> Closed : deviationApproved() / release material lot, update qualityStatus=ACCEPTED_WITH_DEVIATION
    Rework --> Closed : reworkInspectionPassed() / release reworked lot, record rework cost
    Scrap --> Closed : scrapPosted() [scrap movement confirmed in ERP] / write off inventory value
    ReturnToSupplier --> Closed : returnShipped() [RMA confirmed, replacement PO raised]

    Escalated --> UnderReview : assignSeniorReviewer(seniorQualityEngineerId) / restart review clock
    Escalated --> Closed : emergencyDisposition(approvedBy) [production-critical, board-level approval] / flag for post-incident review

    Closed --> [*]
```

**Status values:** `OPEN`, `UNDER_REVIEW`, `ROOT_CAUSE_ANALYSIS`, `PENDING_DISPOSITION`, `ACCEPT_AS_IS`, `REWORK`, `SCRAP`, `RETURN_TO_SUPPLIER`, `ESCALATED`, `CLOSED`

---

## Material Lot State Machine

A material lot tracks the physical disposition of a quantity of material from initial goods receipt through consumption or final disposition. Quality status gates all consumption events. Quarantine is a reversible safety hold that can be resolved by re-inspection. Lot splits and merges generate child and sibling lots, preserving genealogy links throughout all transitions.

```mermaid
stateDiagram-v2
    [*] --> Received : goods receipt posted from ERP GR or MES production output

    Received --> InspectionPending : requiresInspection() [inspection plan exists for material type or supplier]
    Received --> Available : skipInspection() [material exempt from incoming QC, auto-approved by rule]

    InspectionPending --> UnderInspection : beginInspection(inspectorId, sampleDrawn) / create inspection_result record

    UnderInspection --> Available : inspectionPassed() / set qualityStatus=APPROVED, release lot
    UnderInspection --> Quarantined : inspectionFailed() / set qualityStatus=REJECTED, open NCR, block reservations
    UnderInspection --> ConditionalRelease : conditionalPass() [pass with deviation, approved by quality engineer]

    ConditionalRelease --> Available : deviationApproved(approvedBy) / set qualityStatus=ACCEPTED_WITH_DEVIATION
    ConditionalRelease --> Quarantined : deviationRejected() / return to quarantine, update NCR

    Available --> Reserved : reserve(workOrderId, qty) [reservedQty <= currentQuantity]
    Available --> Quarantined : quarantine(reason) [SPC violation, customer complaint, or expiry warning]
    Available --> Consumed : fullyIssued() [currentQuantity drops to 0 after final issue]
    Available --> Transferred : transfer(toLocationId) / record TRANSFER movement

    Reserved --> Available : unreserve(workOrderId) [work order cancelled or rescheduled]
    Reserved --> PartiallyIssued : issuePartial(qty) [issuedQty < reservedQuantity]
    Reserved --> Consumed : fullyIssued() [currentQuantity = 0 after issue]

    PartiallyIssued --> Reserved : remainderStillReserved() [remaining reservation maintained]
    PartiallyIssued --> Available : releaseRemainder() [remaining reservation cancelled]

    Transferred --> Available : arrivalConfirmed(toLocationId) / update locationId

    Quarantined --> UnderInspection : reinspect() [new sample drawn, previous inspection superseded]
    Quarantined --> Scrapped : dispose(SCRAP) [NCR dispositioned as scrap, approved by quality manager]
    Quarantined --> Available : holdsCleared(approvedBy) [quarantine reason resolved without re-inspection]

    Consumed --> [*]
    Scrapped --> [*]
```

**Status values:** `RECEIVED`, `INSPECTION_PENDING`, `UNDER_INSPECTION`, `CONDITIONAL_RELEASE`, `AVAILABLE`, `RESERVED`, `PARTIALLY_ISSUED`, `TRANSFERRED`, `QUARANTINED`, `CONSUMED`, `SCRAPPED`
