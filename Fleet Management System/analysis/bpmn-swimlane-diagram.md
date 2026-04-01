# BPMN Swimlane Diagrams — Fleet Management System

This document presents two process diagrams modelled as swimlane flowcharts using Mermaid subgraphs. Each swimlane represents a distinct role/actor, and arrows between swimlanes show handoffs and dependencies across organisational boundaries.

---

## 1. Dispatch-to-Delivery Process

This diagram models the end-to-end process from the moment a job request is received by the Dispatcher through driver assignment, trip execution, real-time monitoring by the System, and final job closure. It covers the four swimlanes: Dispatcher, Driver, System, and Fleet Manager.

```mermaid
flowchart TD
    subgraph FleetManager["Fleet Manager"]
        FM1[Review Escalated Issues]
        FM2[Approve Reassignment\nor Job Cancellation]
        FM3[Review Completed\nTrip Summary]
        FM4[Review Driver\nPerformance Score]
    end

    subgraph Dispatcher["Dispatcher"]
        D1[Receive Job Request\nfrom Customer or Internal]
        D2[Review Job Requirements\nVehicle Type, Load, Route]
        D3[Check Driver Availability\nand Licence Class]
        D4[Check Vehicle Availability\nand Maintenance Status]
        D5[Assign Driver and Vehicle\nto Job]
        D6[Send Dispatch Notification]
        D7[Monitor Job Progress\non Live Map]
        D8{Issue Detected\nDuring Trip?}
        D9[Escalate to Fleet Manager]
        D10[Coordinate Reassignment\nor Breakdown Recovery]
        D11[Mark Job as Complete\nin Dispatch Module]
    end

    subgraph Driver["Driver"]
        DR1[Receive Assignment\nNotification via App]
        DR2[Review Job Details\nRoute, Pickup, Delivery]
        DR3[Complete Pre-Trip\nDVIR Inspection]
        DR4{Vehicle\nPasses Inspection?}
        DR5[Report Defect\nto Dispatcher]
        DR6[Confirm Ready to Depart]
        DR7[Start Trip in App]
        DR8[Navigate Assigned Route\nFollow Waypoints]
        DR9{Incident or\nDelay Occurs?}
        DR10[Report via App\nIncident or Delay]
        DR11[Complete Delivery\nor Job Task]
        DR12[End Trip in App]
        DR13[Complete Post-Trip\nDVIR Inspection]
    end

    subgraph System["System"]
        S1[Validate Assignment\nCheck Licence vs Vehicle Class]
        S2[Create Trip Record\nStatus: PENDING]
        S3[Activate GPS Tracking\nWaypoint Recording]
        S4[Monitor Geofence Zones\nEvaluate Every GPS Ping]
        S5{Geofence\nEvent Detected?}
        S6[Create Geofence Event\nDispatch Alert]
        S7[Monitor Driver Behaviour\nSpeed, Braking, Cornering]
        S8{Behaviour\nAnomaly Detected?}
        S9[Record Behaviour Event\nFlag for Score Calculation]
        S10[Set Trip Status\nto COMPLETED]
        S11[Calculate Trip Metrics\nDistance, Duration, Idle Time]
        S12[Run Driver Score Engine\nProcess Behaviour Events]
        S13[Update Driver Rolling\nPerformance Score]
        S14{Score Below\nAlert Threshold?}
        S15[Send Performance Alert\nto Fleet Manager]
        S16[Archive Trip Record]
    end

    %% Process start
    D1 --> D2
    D2 --> D3
    D3 --> D4

    %% Availability check
    D4 --> D5
    D5 --> S1

    %% System validates
    S1 --> D6
    D6 --> DR1

    %% Driver receives and prepares
    DR1 --> DR2
    DR2 --> DR3
    DR3 --> DR4
    DR4 -- Defect Found --> DR5
    DR5 --> D10
    D10 --> FM1
    FM1 --> FM2
    FM2 --> D10
    DR4 -- Passed --> DR6
    DR6 --> S2

    %% System creates trip
    S2 --> DR7
    DR7 --> S3

    %% Active trip monitoring
    S3 --> S4
    S4 --> S5
    S5 -- Yes --> S6
    S6 --> D7
    S5 -- No --> S7
    S7 --> S8
    S8 -- Yes --> S9
    S9 --> DR8
    S8 -- No --> DR8

    %% In-trip driver activity
    DR8 --> DR9
    DR9 -- Yes --> DR10
    DR10 --> D8
    D8 -- Yes --> D9
    D9 --> FM1
    D8 -- No --> D7
    DR9 -- No --> DR11

    %% Trip completion
    DR11 --> DR12
    DR12 --> S10
    S10 --> DR13
    DR13 --> S11
    S11 --> D11
    D11 --> S12

    %% Scoring
    S12 --> S13
    S13 --> S14
    S14 -- Yes --> S15
    S15 --> FM4
    S14 -- No --> S16
    S16 --> FM3
    FM3 --> FM4
```

---

## 2. Maintenance Work Order Process

This diagram models the complete lifecycle of a maintenance work order from automated detection or DVIR defect trigger through scheduling, execution by a mechanic or external service provider, parts procurement, quality verification, and closure with schedule recalculation.

```mermaid
flowchart TD
    subgraph System["System"]
        SY1[Monitor Mileage and\nTime Thresholds Hourly]
        SY2{Threshold\nBreached?}
        SY3[Create Maintenance\nSchedule Alert\nStatus: DUE_SOON]
        SY4[Send Alert to Dispatcher\nand Fleet Manager]
        SY5[Create Work Order\nStatus: OPEN]
        SY6[Email Work Order\nto Service Provider]
        SY7[Update Vehicle Status\nto MAINTENANCE_IN_PROGRESS]
        SY8[Receive Work Order\nCompletion Data]
        SY9[Update Vehicle\nlastServiceDate\nand Odometer]
        SY10[Recalculate Next\nMaintenance Thresholds]
        SY11[Update Vehicle Status\nto UP_TO_DATE]
        SY12[Archive Maintenance\nRecord]
    end

    subgraph FleetManager["Fleet Manager"]
        FM1[Review Maintenance\nAlert Dashboard]
        FM2{Approve or\nDefer?}
        FM3[Log Deferral Reason\nSnooze Alert]
        FM4[Review Work Order\nand Estimated Cost]
        FM5{Approve Cost\nEstimate?}
        FM6[Negotiate or\nSelect Alternative Vendor]
        FM7[Approve Additional\nRepairs if Found]
        FM8[Receive Completion\nNotification]
        FM9[Review Final Work\nOrder and Invoice]
        FM10[Close Maintenance\nRecord in System]
    end

    subgraph Dispatcher["Dispatcher"]
        DP1[Receive Maintenance\nDue Notification]
        DP2[Review Vehicle Schedule\nand Availability]
        DP3{DVIR Defect\nTriggered?}
        DP4[Mark Vehicle as\nUnavailable for Trips]
        DP5[Select Approved\nService Provider]
        DP6{Provider\nConfigured?}
        DP7[Notify Fleet Manager\nto Add Provider]
        DP8[Set Target Service Date\nand Confirm Assignment]
        DP9[Coordinate Vehicle\nTransport to Service Location]
        DP10[Confirm Vehicle\nReturned to Fleet]
    end

    subgraph Mechanic["Mechanic"]
        ME1[Receive Work Order\nEmail Notification]
        ME2[Access Work Order\nin Portal]
        ME3[Review Vehicle\nService History\nand Defect Notes]
        ME4[Perform Diagnostic\nAssessment]
        ME5[Prepare Cost Estimate\nParts and Labour]
        ME6[Perform Maintenance\nand Repairs]
        ME7{Additional\nDefects Found?}
        ME8[Document Additional\nDefects and Cost\nin Work Order]
        ME9[Record Service Details\nParts Used, Labour Hours]
        ME10[Update Odometer Reading\nin Work Order]
        ME11[Mark Work Order\nas COMPLETE]
    end

    subgraph ServiceProvider["Parts Supplier"]
        SP1[Receive Parts\nAvailability Request]
        SP2[Return Availability\nand Lead Time]
        SP3[Receive Purchase Order]
        SP4[Confirm Order and\nProvide Delivery ETA]
        SP5[Deliver Parts\nto Service Location]
    end

    %% System detection
    SY1 --> SY2
    SY2 -- No --> SY1
    SY2 -- Yes --> SY3
    SY3 --> SY4

    %% Fleet Manager and Dispatcher review
    SY4 --> FM1
    SY4 --> DP1
    FM1 --> FM2
    FM2 -- Defer --> FM3
    FM3 --> SY1
    FM2 -- Approve --> FM4

    DP1 --> DP2
    DP2 --> DP3
    DP3 -- DVIR Defect --> DP4
    DP4 --> DP5
    DP3 -- Scheduled --> DP5

    DP5 --> DP6
    DP6 -- Not Configured --> DP7
    DP7 --> FM1
    DP6 -- Configured --> DP8
    DP8 --> DP9

    %% System creates work order
    DP8 --> SY5
    SY5 --> SY6
    SY5 --> SY7

    %% Mechanic receives and assesses
    SY6 --> ME1
    ME1 --> ME2
    ME2 --> ME3
    ME3 --> ME4
    ME4 --> ME5
    ME5 --> FM4
    FM4 --> FM5
    FM5 -- Reject --> FM6
    FM6 --> DP5
    FM5 -- Approve --> ME6

    %% Parts procurement
    ME6 --> SP1
    SP1 --> SP2
    SP2 --> ME6
    ME6 --> SP3
    SP3 --> SP4
    SP4 --> SP5
    SP5 --> ME6

    %% Service execution
    ME6 --> ME7
    ME7 -- Yes --> ME8
    ME8 --> FM7
    FM7 --> ME6
    ME7 -- No --> ME9
    ME9 --> ME10
    ME10 --> ME11

    %% Completion and closure
    ME11 --> SY8
    SY8 --> SY9
    SY9 --> SY10
    SY10 --> SY11
    SY11 --> FM8
    FM8 --> FM9
    FM9 --> FM10
    FM10 --> DP10
    DP10 --> SY12
    SY12 --> SY1
```

---

## Process Design Notes

### Handoff Points and Latency Targets

| Handoff                                    | From            | To              | Target Latency  |
|--------------------------------------------|-----------------|-----------------|-----------------|
| Maintenance alert issued to dispatcher     | System          | Dispatcher      | < 2 minutes     |
| Work order created after dispatcher approval | Dispatcher    | System          | Immediate       |
| Work order delivered to service provider   | System          | Mechanic        | < 5 minutes     |
| Cost estimate returned to fleet manager    | Mechanic        | Fleet Manager   | < 1 business day|
| Parts delivered to service location        | Parts Supplier  | Mechanic        | Per supplier ETA|
| Work order marked complete to fleet manager| Mechanic        | Fleet Manager   | < 2 minutes     |
| Vehicle status restored to UP_TO_DATE      | System          | All Users       | Immediate       |
| Driver assignment notification delivered   | System          | Driver App      | < 30 seconds    |
| Driver score updated after trip            | System          | Driver Profile  | < 5 minutes     |
| Geofence alert dispatched after event      | System          | Dispatcher      | < 10 seconds    |

### Escalation Paths

**Dispatch-to-Delivery:**
- If a DVIR defect blocks a trip, the Dispatcher escalates to the Fleet Manager for a reassignment decision.
- If an in-trip incident is severe (driver safety, cargo loss), the Dispatcher escalates to the Fleet Manager who coordinates with the Compliance Officer.
- If a driver score drops below the threshold, the System alerts the Fleet Manager to schedule a coaching session.

**Maintenance Work Order:**
- If no approved service providers are configured for the vehicle's region, the Dispatcher escalates to the Fleet Manager to onboard a new vendor.
- If the Mechanic discovers additional defects beyond the original scope, the Fleet Manager approves or defers the additional work.
- If a cost estimate is rejected, the Dispatcher is re-engaged to select an alternative service provider.
- If the vehicle is out of service beyond the expected return date, the Dispatcher is notified to arrange alternative fleet coverage.

### Compliance Considerations

All work order records, DVIR inspections, and driver assignments are retained for a minimum of 12 months in compliance with FMCSA record-keeping requirements. Critical DVIR defects that block trips are logged with timestamps and actor identities to create an auditable safety record. Deferred maintenance is logged with the authorising user's identity and the stated reason, providing an audit trail for any regulatory investigation.
