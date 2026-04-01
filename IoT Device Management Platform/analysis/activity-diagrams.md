# Activity Diagrams

Activity diagrams model the dynamic flow of actions within key platform processes. Each diagram represents the sequence of steps, decision points, parallel activities, and exception paths that govern a major operational workflow in the IoT Device Management Platform.

---

## Device Provisioning Activity

Device provisioning is the process by which a new physical device gains a verified, trusted identity within the platform and establishes its first authenticated connection. The activity spans certificate generation, device registration, configuration push, connectivity validation, and final activation.

```mermaid
flowchart TD
    A([Start: New Device to Provision]) --> B[Generate X.509 Certificate\nvia Certificate Authority]
    B --> C{Certificate\nGenerated\nSuccessfully?}
    C -- No --> D[Log Certificate Error\nNotify Platform Admin]
    D --> E([End: Provisioning Failed])
    C -- Yes --> F[Register Device in\nDevice Registry Service]
    F --> G{Device ID\nUnique?}
    G -- No --> H[Reject Registration\nReturn Conflict Error]
    H --> E
    G -- Yes --> I[Persist Device Record\nAssign Device Group]
    I --> J[Push Initial Device\nConfiguration Bundle]
    J --> K{Configuration\nDelivered?}
    K -- No --> L[Queue Configuration\nfor Next Connection]
    L --> M[Mark Device as\nPending Configuration]
    K -- Yes --> N[Device Connects via\nMQTT with Certificate]
    M --> N
    N --> O{TLS Handshake\nSuccessful?}
    O -- No --> P[Log Auth Failure\nIncrement Failure Counter]
    P --> Q{Failure Count\nExceeds Threshold?}
    Q -- Yes --> R[Lock Device Provisioning\nAlert Security Team]
    R --> E
    Q -- No --> N
    O -- Yes --> S[Validate Certificate\nAgainst CA Chain]
    S --> T{Certificate\nValid?}
    T -- No --> U[Revoke Session\nNotify Security]
    U --> E
    T -- Yes --> V[Device Sends\nHello / Registration Payload]
    V --> W[Platform Acknowledges\nRegistration via MQTT]
    W --> X[Initialize Device Shadow\nwith Default State]
    X --> Y[Publish Device\nProvisioned Event]
    Y --> Z{Initial Config\nPending?}
    Z -- Yes --> AA[Push Pending Config\nto Device]
    AA --> AB{Config\nAcknowledged?}
    AB -- No --> AC[Retry Config Push\nup to 3 times]
    AC --> AB
    AB -- Yes --> AD[Mark Device as Active]
    Z -- No --> AD
    AD --> AE[Emit DeviceActivated\nDomain Event]
    AE --> AF([End: Device Provisioned and Active])
```

The provisioning activity is designed to be idempotent at each stage. If the platform receives a duplicate provisioning request for an already-registered device with identical certificate fingerprint, the existing record is returned rather than raising an error, allowing safe retry from devices that lose connectivity during provisioning.

---

## Telemetry Ingestion Activity

Telemetry ingestion handles the continuous stream of sensor readings, status messages, and diagnostic payloads from connected devices. The pipeline must process messages durably, route them to the appropriate storage and processing systems, and trigger rules evaluation in near real-time.

```mermaid
flowchart TD
    A([Start: Device Sends Telemetry Payload]) --> B[MQTT Broker Receives\nMessage on Topic]
    B --> C{Message Size\nWithin Limit?}
    C -- No --> D[Drop Message\nPublish Error to Device]
    D --> E([End: Message Rejected])
    C -- Yes --> F[Authenticate Device\nvia Certificate / Token]
    F --> G{Authentication\nPassed?}
    G -- No --> H[Reject Message\nLog Auth Failure]
    H --> E
    G -- Yes --> I[Extract Topic Metadata\nDevice ID, Stream Name]
    I --> J[Route Message to\nIngestion Pipeline Queue]
    J --> K[Ingestion Worker\nConsumes from Queue]
    K --> L[Deserialize and\nValidate Payload Schema]
    L --> M{Schema\nValid?}
    M -- No --> N[Publish to\nDead Letter Queue]
    N --> O[Alert Device Owner\nof Schema Violation]
    O --> E
    M -- Yes --> P[Enrich Message with\nServer-Side Timestamp]
    P --> Q[Write to Time-Series\nDatabase - InfluxDB / TimescaleDB]
    Q --> R{Write\nSuccessful?}
    R -- No --> S[Retry Write\nwith Exponential Backoff]
    S --> T{Max Retries\nReached?}
    T -- Yes --> U[Route to Overflow\nStorage - Object Store]
    T -- No --> R
    R -- Yes --> V[Update Device Last-Seen\nTimestamp in Registry]
    U --> V
    V --> W[Publish Telemetry Event\nto Internal Event Bus]
    W --> X{Rules Engine\nSubscribed?}
    X -- Yes --> Y[Rules Engine Evaluates\nMessage Against Active Rules]
    Y --> Z{Any Rule\nCondition Met?}
    Z -- Yes --> AA[Trigger Rule Actions\nAlert / Command / Webhook]
    AA --> AB[Log Rule Execution\nin Audit Trail]
    Z -- No --> AC[No Action Required]
    X -- No --> AC
    AB --> AD([End: Telemetry Processed])
    AC --> AD
```

The ingestion pipeline is designed for horizontal scalability. Multiple consumer workers operate in parallel, partitioned by device group or geographic region, ensuring that a telemetry surge from one device class does not affect ingestion latency for other device groups.

---

## OTA Firmware Update Activity

Over-the-air firmware updates are one of the most complex and risk-sensitive operations in the platform. The activity covers the full lifecycle from deployment creation through device reporting, including validation, rollback, and failure handling.

```mermaid
flowchart TD
    A([Start: Engineer Creates\nFirmware Deployment]) --> B[Upload Firmware Binary\nto Firmware Repository]
    B --> C[Generate SHA-256\nChecksum and Sign Binary]
    C --> D[Define Deployment:\nTarget Group, Schedule, Rollout %]
    D --> E{Approval\nRequired?}
    E -- Yes --> F[Submit Deployment\nfor Approval]
    F --> G{Deployment\nApproved?}
    G -- No --> H[Cancel Deployment\nNotify Engineer]
    H --> I([End: Deployment Cancelled])
    G -- Yes --> J[Scheduler Activates\nDeployment at Scheduled Time]
    E -- No --> J
    J --> K[Deployment Orchestrator\nSelects Target Device Batch]
    K --> L[Send Firmware Notification\nvia MQTT to Device Batch]
    L --> M{Device\nOnline?}
    M -- No --> N[Queue Notification\nfor Next Device Connection]
    N --> O[Wait for Device\nto Come Online]
    O --> M
    M -- Yes --> P[Device Receives Notification\nwith Firmware Metadata]
    P --> Q{Device Checks\nPreconditions}
    Q --> R{Battery ≥ 25%\nand Disk Space OK?}
    R -- No --> S[Device Defers Update\nReports Deferral Reason]
    S --> T[Platform Reschedules\nfor Device]
    T --> O
    R -- Yes --> U[Device Downloads\nFirmware from CDN / Repository]
    U --> V{Download\nComplete?}
    V -- No --> W{Connection Lost\nDuring Download?}
    W -- Yes --> X[Pause Download\nStore Resume Offset]
    X --> Y[Resume on\nReconnect]
    Y --> U
    W -- No --> Z[Retry Download\nSegment]
    Z --> V
    V -- Yes --> AA[Validate Checksum\nand Signature]
    AA --> AB{Validation\nPassed?}
    AB -- No --> AC[Discard Firmware\nReport Corruption]
    AC --> AD[Platform Marks\nDevice Update as Failed]
    AD --> AE{Retry\nEligible?}
    AE -- Yes --> U
    AE -- No --> AF([End: Update Failed - Checksum])
    AB -- Yes --> AG[Apply Firmware\nto Staging Partition]
    AG --> AH[Device Reboots\ninto New Firmware]
    AH --> AI{Boot\nSuccessful?}
    AI -- No --> AJ[Watchdog Triggers\nAutomatic Rollback]
    AJ --> AK[Restore Previous\nFirmware Partition]
    AK --> AL[Device Reboots\ninto Previous Firmware]
    AL --> AM[Report Rollback\nto Platform]
    AM --> AN[Platform Marks\nRollback Executed]
    AN --> AO([End: Rollback Complete])
    AI -- Yes --> AP[Device Reports\nUpdate Success with New Version]
    AP --> AQ[Platform Updates\nDevice Firmware Version]
    AQ --> AR[Advance to Next\nBatch if Staged Rollout]
    AR --> AS{All Devices\nProcessed?}
    AS -- No --> K
    AS -- Yes --> AT[Close Deployment\nGenerate Summary Report]
    AT --> AU([End: Deployment Complete])
```

The staged rollout mechanism is critical for large device fleets. Deployments begin with a canary batch (typically 1–5% of targets), and the platform automatically pauses rollout if the failure rate in the canary batch exceeds a configured threshold, preventing mass failures across the entire fleet.

---

## Alert Processing Activity

Alert processing translates raw rules engine trigger events into actionable notifications, applying deduplication, severity escalation, and multi-channel delivery. The activity ensures that alert fatigue is minimized while guaranteeing that critical conditions are never silently dropped.

```mermaid
flowchart TD
    A([Start: Rules Engine Detects\nCondition Match]) --> B[Create Alert Candidate\nwith Metadata and Severity]
    B --> C[Check Deduplication\nWindow - 5 minute default]
    C --> D{Identical Alert\nAlready Active?}
    D -- Yes --> E[Increment Occurrence\nCounter on Existing Alert]
    E --> F[Update Last-Seen\nTimestamp]
    F --> G([End: Deduplicated])
    D -- No --> H[Persist Alert Record\nin Alert Store]
    H --> I[Classify Alert:\nInfo / Warning / Critical / Emergency]
    I --> J{Severity\nLevel?}
    J -- Info --> K[Write to Audit Log\nOnly - No Notification]
    K --> L([End: Info Alert Logged])
    J -- Warning --> M[Send In-App\nNotification to Device Owner]
    M --> N{Notification\nDelivered?}
    N -- No --> O[Log Delivery Failure\nSchedule Retry]
    O --> P([End: Warning Queued])
    N -- Yes --> Q([End: Warning Delivered])
    J -- Critical --> R[Send Notification\nvia All Enabled Channels]
    R --> S[Email + SMS + Push\nNotification Dispatch]
    S --> T[Start Escalation\nTimer - 15 minutes default]
    T --> U{Acknowledged\nWithin Timeout?}
    U -- Yes --> V[Cancel Escalation\nMark Acknowledged]
    V --> W[Link Alert to\nIncident if Applicable]
    W --> X([End: Critical Acknowledged])
    U -- No --> Y[Escalate to\nOn-Call Secondary]
    Y --> Z{Acknowledged\nAfter Escalation?}
    Z -- Yes --> V
    Z -- No --> AA[Page Incident\nManager]
    AA --> AB[Create Incident\nTicket Automatically]
    AB --> AC([End: Incident Created])
    J -- Emergency --> AD[Immediate Page\nto All On-Call]
    AD --> AE[Create P1 Incident\nImmediately]
    AE --> AF[Notify Executive\nStakeholders]
    AF --> AG([End: P1 Incident Active])
```

Alert deduplication is stateful and window-based. The platform maintains an in-memory bloom filter seeded from the persistent alert store to perform sub-millisecond deduplication checks during high-volume alert storms. Alerts for the same device and same rule within the deduplication window are collapsed into a single record with an occurrence count.

---

## Device Decommissioning Activity

Device decommissioning permanently removes a device from the platform, revoking its credentials, purging or archiving its data according to retention policy, and ensuring no orphaned state remains in any subsystem.

```mermaid
flowchart TD
    A([Start: Admin Initiates\nDevice Decommission]) --> B{Device\nCurrently Online?}
    B -- Yes --> C[Send Disconnect\nCommand to Device]
    C --> D{Device Acknowledges\nDisconnect?}
    D -- No --> E[Force Close\nMQTT Session on Broker]
    D -- Yes --> F[Device Initiates\nGraceful Shutdown]
    F --> G[Device Closes\nMQTT Connection]
    B -- No --> H[Proceed Directly\nto Revocation]
    E --> H
    G --> H
    H --> I[Revoke Device Certificate\nvia CA CRL Update]
    I --> J[Remove Device from\nActive Sessions Table]
    J --> K[Disable Device Record\nin Device Registry]
    K --> L{Data Retention\nPolicy?}
    L -- Purge Immediately --> M[Delete Telemetry Data\nfrom Time-Series DB]
    M --> N[Delete Device Shadow\nand Configuration]
    N --> O[Delete Device Record\nfrom Registry]
    O --> P[Log Purge Event\nin Compliance Audit Trail]
    P --> Q([End: Device Purged])
    L -- Archive --> R[Export Telemetry to\nCold Storage - S3 / Blob]
    R --> S[Tag Archive with\nDevice ID and Date Range]
    S --> T[Delete Hot Storage\nTelemetry Data]
    T --> U[Archive Device Shadow\nand Configuration]
    U --> V[Mark Device Record\nas Archived]
    V --> W[Log Archive Event\nin Compliance Audit Trail]
    W --> X([End: Device Archived])
    L -- Retain for Legal Hold --> Y[Tag Device Data\nwith Legal Hold Flag]
    Y --> Z[Restrict Access\nto Legal Team Only]
    Z --> AA[Disable Device Record\nwithout Data Deletion]
    AA --> AB[Notify Legal Team\nof Decommission]
    AB --> AC([End: Legal Hold Active])
```

Decommissioning is an irreversible operation that requires confirmation from a platform administrator with the `device:decommission` permission. The system enforces a 24-hour soft-delete window during which the decommission can be cancelled, after which the process becomes permanent. All decommissioning actions are recorded in the immutable compliance audit trail with the initiating user's identity and timestamp.

---

## Summary

These activity diagrams capture the control flow and decision logic for the five most operationally significant workflows in the IoT Device Management Platform. Each diagram is designed to be traceable to the corresponding sequence diagrams and state machine diagrams in the detailed design, providing multiple complementary views of the same underlying system behavior.

| Activity | Primary Actors | Key Risk Points |
|---|---|---|
| Device Provisioning | Platform, CA, Device | Certificate issuance, auth failures |
| Telemetry Ingestion | Device, Broker, Pipeline, Rules Engine | Schema violations, write failures |
| OTA Firmware Update | Engineer, Orchestrator, Device | Boot failure, corrupted firmware |
| Alert Processing | Rules Engine, Alert Manager, On-Call | Alert fatigue, escalation failures |
| Device Decommissioning | Admin, CA, Storage | Data residency, orphaned state |
