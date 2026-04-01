# Swimlane Diagrams

Swimlane diagrams illustrate the responsibilities and handoffs between actors or system components during key cross-cutting workflows. Each lane represents a distinct participant, and the flow of control between lanes represents integration points, API calls, events, and service boundaries.

---

## Device Provisioning Swimlane

This swimlane covers the end-to-end provisioning flow across four participants: the Platform Administrator who initiates the process, the physical Device being onboarded, the Certificate Authority that issues trust credentials, and the MQTT Broker that hosts the secure communication channel.

```mermaid
flowchart TD
    subgraph PlatformAdmin["Platform Admin"]
        A1[Initiate Provisioning\nRequest in Portal]
        A2[Configure Device\nMetadata and Group]
        A3[Confirm Device\nActivation in Dashboard]
    end

    subgraph CertificateAuthority["Certificate Authority"]
        CA1[Receive CSR from\nProvisioning Service]
        CA2[Validate CSR Parameters\nCheck Against Policy]
        CA3[Issue X.509 Certificate\nwith Device CN]
        CA4[Add Certificate to\nActive CRL Scope]
    end

    subgraph DeviceRegistryService["Device Registry / Platform"]
        P1[Generate CSR for\nNew Device]
        P2[Register Device Record\nAssign Device ID]
        P3[Store Certificate\nFingerprint in Registry]
        P4[Prepare Initial\nConfiguration Bundle]
        P5[Initialize Device Shadow\nwith Default Desired State]
        P6[Publish DeviceProvisioned\nEvent to Event Bus]
    end

    subgraph MQTTBroker["MQTT Broker"]
        M1[Receive CONNECT\nfrom Device]
        M2[Validate TLS Certificate\nAgainst CA Chain]
        M3[Authorize Topic\nAccess by Device ID]
        M4[Accept Connection\nEstablish Session]
        M5[Deliver Queued\nConfiguration Messages]
    end

    subgraph Device["Device"]
        D1[Receive Certificate\nand Private Key via Secure Channel]
        D2[Initiate TLS Connection\nto MQTT Broker Endpoint]
        D3[Subscribe to\nCommand and Config Topics]
        D4[Publish Hello\nMessage on Registry Topic]
        D5[Receive and Apply\nInitial Configuration]
        D6[Begin Normal\nTelemetry Operation]
    end

    A1 --> P1
    P1 --> CA1
    CA1 --> CA2
    CA2 --> CA3
    CA3 --> CA4
    CA3 --> A2
    CA3 --> P2
    P2 --> P3
    P3 --> P4
    A2 --> P4
    P4 --> D1
    D1 --> D2
    D2 --> M1
    M1 --> M2
    M2 --> M3
    M3 --> M4
    M4 --> D3
    D3 --> D4
    D4 --> P5
    P5 --> P6
    P6 --> M5
    M5 --> D5
    D5 --> D6
    D6 --> A3
```

**Handoff Summary:**
- The Platform Admin triggers certificate issuance but the CA operates autonomously once the CSR arrives.
- The Device receives credentials via a secure out-of-band channel (typically a manufacturing-time injection or secure bootstrap API), not over MQTT.
- The MQTT Broker enforces per-device topic authorization so that device `abc123` cannot publish or subscribe to topics belonging to `abc124`.
- The DeviceProvisioned event is published to the internal event bus so that downstream services (billing, analytics) can react without coupling to the provisioning flow.

---

## Firmware Update Approval and Rollout Swimlane

This swimlane models the firmware update lifecycle from an engineer submitting a firmware package through the approval gate, orchestrated deployment to a device fleet, and per-device execution. Four lanes participate: the Engineer, the Approval System (change management), the Deployment Service, and the Device Fleet.

```mermaid
flowchart TD
    subgraph Engineer["Engineer"]
        E1[Upload Firmware Binary\nto Firmware Repository]
        E2[Configure Deployment:\nTarget Group, Schedule, Rollout %]
        E3[Submit Deployment\nfor Approval]
        E4[Monitor Rollout\nProgress Dashboard]
        E5[Approve Pause or\nCancel if Issues Arise]
    end

    subgraph ApprovalSystem["Approval System / Change Management"]
        AP1[Receive Deployment\nApproval Request]
        AP2[Notify Approvers\nvia Email and ITSM]
        AP3{Deployment\nApproved?}
        AP4[Record Approval Decision\nin Audit Trail]
        AP5[Reject and Notify\nEngineer]
    end

    subgraph DeploymentService["Deployment / OTA Service"]
        DS1[Validate Firmware Binary\nChecksum and Signature]
        DS2[Store Firmware in\nSecure CDN with Signed URLs]
        DS3[Receive Approval\nActivate Deployment at Schedule]
        DS4[Select First Batch\nCanary - 5 Percent]
        DS5[Send Firmware Notification\nto Batch via MQTT]
        DS6[Monitor Canary Batch\nSuccess and Failure Rates]
        DS7{Canary Failure Rate\nBelow Threshold?}
        DS8[Advance to Next\nRollout Batch]
        DS9[Pause Deployment\nNotify Engineer]
        DS10[Generate Final\nDeployment Report]
    end

    subgraph DeviceFleet["Device Fleet"]
        DF1[Receive Firmware\nUpdate Notification]
        DF2[Check Preconditions:\nBattery, Disk, Active Operations]
        DF3{Preconditions\nMet?}
        DF4[Defer Update\nReport Deferral Reason]
        DF5[Download Firmware\nfrom Signed CDN URL]
        DF6[Validate Checksum\nand Code Signature]
        DF7[Install to Staging\nPartition and Reboot]
        DF8{Boot into New\nFirmware Successful?}
        DF9[Report Update Success\nwith New Version String]
        DF10[Trigger Watchdog Rollback\nReport Failure]
    end

    E1 --> DS1
    DS1 --> DS2
    E2 --> E3
    E3 --> AP1
    AP1 --> AP2
    AP2 --> AP3
    AP3 -- Approved --> AP4
    AP4 --> DS3
    AP3 -- Rejected --> AP5
    AP5 --> E5
    DS3 --> DS4
    DS4 --> DS5
    DS5 --> DF1
    DF1 --> DF2
    DF2 --> DF3
    DF3 -- No --> DF4
    DF4 --> DS6
    DF3 -- Yes --> DF5
    DF5 --> DF6
    DF6 --> DF7
    DF7 --> DF8
    DF8 -- Yes --> DF9
    DF9 --> DS6
    DF8 -- No --> DF10
    DF10 --> DS6
    DS6 --> DS7
    DS7 -- Yes --> DS8
    DS8 --> DS5
    DS7 -- No --> DS9
    DS9 --> E5
    E4 --> DS6
    DS8 --> DS10
    DS10 --> E4
```

**Handoff Summary:**
- The Approval System acts as a gate that decouples engineering intent from fleet execution, enabling change management compliance.
- Signed CDN URLs prevent unauthorized firmware downloads and ensure that only the Deployment Service can authorize access to specific firmware versions.
- The canary batch analysis is automated; the Deployment Service evaluates the success rate against a configurable threshold before advancing the rollout.
- An engineer can always manually pause or cancel a deployment regardless of automated decisions.

---

## Alert Lifecycle Swimlane

This swimlane traces an alert from its origin in raw telemetry data through rules evaluation, alert management, on-call notification, and incident creation. Five lanes participate: the Device generating telemetry, the Rules Engine evaluating conditions, the Alert Manager handling deduplication and notifications, the On-Call Engineer responding, and the Incident System tracking resolution.

```mermaid
flowchart TD
    subgraph Device["Device"]
        DV1[Device Reports\nAbnormal Sensor Reading]
        DV2[Subsequent Readings\nContinue Elevated]
        DV3[Reading Returns\nto Normal Range]
    end

    subgraph RulesEngine["Rules Engine"]
        RE1[Evaluate Incoming\nTelemetry Against Rules]
        RE2{Rule Condition\nMet?}
        RE3[Generate Alert\nCandidate with Context]
        RE4[Evaluate Subsequent\nReadings for Persistence]
        RE5[Evaluate Auto-Resolve\nCondition Met?]
    end

    subgraph AlertManager["Alert Manager"]
        AM1[Receive Alert\nCandidate]
        AM2{Duplicate\nWithin Window?}
        AM3[Increment Occurrence\nCounter]
        AM4[Create New Alert\nRecord in Store]
        AM5[Determine Severity\nand Notification Channel]
        AM6[Dispatch Notification:\nEmail, SMS, Push, Webhook]
        AM7[Start Escalation\nTimer]
        AM8{Acknowledged\nWithin Timeout?}
        AM9[Escalate to\nSecondary On-Call]
        AM10[Mark Alert\nAuto-Resolved]
        AM11[Send Resolution\nNotification]
    end

    subgraph OnCallEngineer["On-Call Engineer"]
        OC1[Receive Alert\nNotification]
        OC2[Acknowledge Alert\nin Dashboard or via Reply]
        OC3[Investigate Device\nand Telemetry History]
        OC4[Decide: Create Incident\nor Close Alert]
        OC5[Resolve and\nClose Alert Manually]
    end

    subgraph IncidentSystem["Incident System / ITSM"]
        IS1[Receive Incident\nCreation Request]
        IS2[Create Incident Ticket\nwith Alert Context]
        IS3[Notify Incident\nResponse Team]
        IS4[Track Resolution\nand Post-Mortem]
    end

    DV1 --> RE1
    RE1 --> RE2
    RE2 -- No --> RE4
    RE2 -- Yes --> RE3
    RE3 --> AM1
    AM1 --> AM2
    AM2 -- Yes --> AM3
    AM3 --> RE4
    AM2 -- No --> AM4
    AM4 --> AM5
    AM5 --> AM6
    AM6 --> OC1
    AM6 --> AM7
    AM7 --> AM8
    AM8 -- Yes --> OC2
    AM8 -- No --> AM9
    AM9 --> OC1
    OC1 --> OC2
    OC2 --> AM8
    OC2 --> OC3
    OC3 --> OC4
    OC4 -- Create Incident --> IS1
    IS1 --> IS2
    IS2 --> IS3
    IS3 --> IS4
    OC4 -- Close Alert --> OC5
    OC5 --> AM11
    DV2 --> RE4
    RE4 --> RE1
    DV3 --> RE5
    RE5 --> AM10
    AM10 --> AM11
    IS4 --> AM11
```

**Handoff Summary:**
- The Rules Engine is stateless per evaluation cycle but the Alert Manager maintains statefulness for deduplication, acknowledgment tracking, and escalation timers.
- Auto-resolution occurs when the telemetry condition that triggered the rule no longer holds for a configurable persistence window, preventing alert noise when conditions briefly normalize and then recur.
- Escalation bypasses the primary on-call responder if acknowledgment does not occur within the SLO window, typically 15 minutes for critical alerts and 5 minutes for emergency severity.

---

## SDK Usage by Developer Swimlane

This swimlane illustrates how a developer integrating the platform SDK interacts with platform services to register a device, publish telemetry, and issue a remote command. Four lanes participate: the Developer writing application code, the SDK handling protocol and retry logic, the Device Registry authenticating and managing device state, and the Telemetry API receiving the data stream.

```mermaid
flowchart TD
    subgraph Developer["Developer"]
        DEV1[Include SDK Dependency\nin Device Firmware Project]
        DEV2[Initialize SDK with\nDevice Credentials and Config]
        DEV3[Implement Telemetry\nPublish Callback]
        DEV4[Implement Command\nHandler Callback]
        DEV5[Call SDK Connect\nMethod]
        DEV6[Call SDK PublishTelemetry\nwith Sensor Data]
        DEV7[Receive CommandReceived\nEvent from SDK]
        DEV8[Execute Command Logic\nin Application Code]
        DEV9[Call SDK AckCommand\nwith Result]
    end

    subgraph SDK["IoT SDK - Client Library"]
        SDK1[Load Credentials:\nCertificate, Private Key, Endpoint]
        SDK2[Establish TLS Connection\nto MQTT Broker]
        SDK3[Subscribe to Reserved\nTopics: Commands, Config, Shadow]
        SDK4[Confirm Connection\nReady to Developer]
        SDK5[Serialize Telemetry\nPayload to JSON or CBOR]
        SDK6[Publish to Telemetry\nMQTT Topic with QoS 1]
        SDK7[Handle PUBACK\nfrom Broker]
        SDK8{PUBACK\nReceived?}
        SDK9[Retry Publish\nwith Backoff]
        SDK10[Receive Incoming\nCommand Message on Topic]
        SDK11[Deserialize and\nValidate Command Payload]
        SDK12[Deliver Command\nto Developer Callback]
        SDK13[Publish Acknowledgment\nto Command Response Topic]
        SDK14[Handle Reconnection\nwith Exponential Backoff]
    end

    subgraph DeviceRegistry["Device Registry / Auth Service"]
        DR1[Validate TLS Certificate\non MQTT Connect]
        DR2[Check Device Status:\nActive, Suspended, Decommissioned]
        DR3[Authorize Topic Access\nvia ACL Policy]
        DR4[Record Connection\nTimestamp in Registry]
        DR5[Route Incoming\nCommand to Device Topic]
    end

    subgraph TelemetryAPI["Telemetry Ingestion API"]
        TA1[Receive Telemetry\nMessage from MQTT Broker]
        TA2[Validate and Enrich\nPayload]
        TA3[Write to Time-Series\nDatabase]
        TA4[Emit Telemetry Event\nto Rules Engine]
        TA5[Return PUBACK\nto Broker]
    end

    DEV1 --> SDK1
    DEV2 --> SDK1
    DEV5 --> SDK2
    SDK2 --> DR1
    DR1 --> DR2
    DR2 --> DR3
    DR3 --> SDK3
    SDK3 --> DR4
    DR4 --> SDK4
    SDK4 --> DEV3
    SDK4 --> DEV4
    DEV3 --> DEV6
    DEV6 --> SDK5
    SDK5 --> SDK6
    SDK6 --> TA1
    TA1 --> TA2
    TA2 --> TA3
    TA3 --> TA4
    TA3 --> TA5
    TA5 --> SDK7
    SDK7 --> SDK8
    SDK8 -- Yes --> DEV6
    SDK8 -- No --> SDK9
    SDK9 --> SDK6
    DR5 --> SDK10
    SDK10 --> SDK11
    SDK11 --> SDK12
    SDK12 --> DEV7
    DEV7 --> DEV8
    DEV8 --> DEV9
    DEV9 --> SDK13
    SDK13 --> DR5
    SDK2 -- Connection Lost --> SDK14
    SDK14 --> SDK2
```

**Handoff Summary:**
- The SDK abstracts all MQTT protocol details, QoS semantics, and retry logic from the developer, exposing a simple callback-driven interface.
- QoS 1 guarantees at-least-once delivery for telemetry, which means the ingestion pipeline must be idempotent to handle potential duplicate messages from retried publishes.
- The SDK manages its own reconnection loop with exponential backoff and jitter to prevent retry storms when many devices lose connectivity simultaneously.
- The developer's command handler callback receives a strongly-typed command object deserialized by the SDK, shielding application code from raw message format changes between SDK versions.

---

## Summary

These swimlane diagrams expose the cross-cutting concerns and integration contracts between system components and external actors. They complement the sequence diagrams in `detailed-design/sequence-diagrams.md` by emphasizing ownership and responsibility boundaries rather than temporal message ordering.

| Swimlane | Lanes | Primary Integration Risk |
|---|---|---|
| Device Provisioning | Admin, CA, Platform, Broker, Device | Credential delivery, cert chain validation |
| Firmware Approval & Rollout | Engineer, Approval, Deployment, Fleet | Approval bypass, canary monitoring |
| Alert Lifecycle | Device, Rules Engine, Alert Mgr, On-Call, ITSM | Escalation failures, alert fatigue |
| SDK Developer Usage | Developer, SDK, Registry, Telemetry API | Retry storms, QoS semantics |
