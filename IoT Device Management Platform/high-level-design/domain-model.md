# Domain Model

This document describes the core domain entities of the IoT Device Management Platform, their
attributes, and the relationships between them. The model is intentionally technology-neutral—it
represents the business domain, not any particular database schema or ORM mapping—and serves as
the authoritative reference for all service-layer contracts and API payloads.

The model is partitioned into four bounded contexts:

| Bounded Context | Entities |
|---|---|
| **Identity & Organisation** | Organization, Fleet, DeviceModel, DeviceTemplate |
| **Device Lifecycle** | Device, DeviceCredential, DeviceShadow, Certificate |
| **Firmware & OTA** | Firmware, FirmwareVersion, OTAJob |
| **Telemetry & Alerting** | TelemetryStream, TelemetryDataPoint, Rule, RuleCondition, RuleAction, Alert |
| **Observability** | AuditLog |

---

## Class Diagram

```mermaid
classDiagram
    direction TB

    class Organization {
        +UUID id
        +String name
        +String slug
        +String billingEmail
        +String country
        +Enum plan
        +Boolean active
        +DateTime createdAt
        +DateTime updatedAt
    }

    class Fleet {
        +UUID id
        +UUID organizationId
        +String name
        +String description
        +String region
        +JSON tags
        +DateTime createdAt
        +DateTime updatedAt
    }

    class DeviceModel {
        +UUID id
        +UUID organizationId
        +String manufacturer
        +String modelNumber
        +String hardwareRevision
        +JSON supportedFirmwareVersions
        +String connectivity
        +DateTime createdAt
    }

    class DeviceTemplate {
        +UUID id
        +UUID deviceModelId
        +String name
        +JSON defaultShadow
        +JSON telemetrySchema
        +JSON commandSchema
        +DateTime createdAt
        +DateTime updatedAt
    }

    class Device {
        +UUID id
        +UUID fleetId
        +UUID deviceModelId
        +UUID deviceTemplateId
        +String serialNumber
        +String name
        +Enum status
        +String firmwareVersion
        +String ipAddress
        +String location
        +DateTime lastSeenAt
        +DateTime provisionedAt
        +DateTime createdAt
        +DateTime updatedAt
    }

    class DeviceCredential {
        +UUID id
        +UUID deviceId
        +Enum credentialType
        +String clientId
        +String passwordHash
        +DateTime expiresAt
        +Boolean revoked
        +DateTime createdAt
    }

    class DeviceShadow {
        +UUID id
        +UUID deviceId
        +JSON reported
        +JSON desired
        +JSON delta
        +Integer version
        +DateTime reportedUpdatedAt
        +DateTime desiredUpdatedAt
    }

    class Firmware {
        +UUID id
        +UUID organizationId
        +UUID deviceModelId
        +String name
        +String vendor
        +String releaseChannel
        +DateTime createdAt
    }

    class FirmwareVersion {
        +UUID id
        +UUID firmwareId
        +String version
        +String downloadUrl
        +String checksum
        +String signatureB64
        +Long sizeBytes
        +String releaseNotes
        +Enum status
        +DateTime releasedAt
        +DateTime createdAt
    }

    class OTAJob {
        +UUID id
        +UUID organizationId
        +UUID firmwareVersionId
        +UUID targetFleetId
        +UUID targetDeviceId
        +JSON rolloutPolicy
        +Integer totalDevices
        +Integer successCount
        +Integer failureCount
        +Integer pendingCount
        +Enum status
        +DateTime startedAt
        +DateTime completedAt
        +DateTime createdAt
    }

    class TelemetryStream {
        +UUID id
        +UUID deviceId
        +String streamName
        +String mqttTopic
        +JSON schema
        +String unit
        +Boolean active
        +DateTime createdAt
    }

    class TelemetryDataPoint {
        +UUID deviceId
        +String streamName
        +DateTime timestamp
        +JSON fields
        +JSON tags
    }

    class Rule {
        +UUID id
        +UUID organizationId
        +UUID fleetId
        +String name
        +String description
        +Enum severity
        +Boolean enabled
        +String triggerMetric
        +DateTime createdAt
        +DateTime updatedAt
    }

    class RuleCondition {
        +UUID id
        +UUID ruleId
        +String field
        +Enum operator
        +String thresholdValue
        +String logicalOperator
        +Integer sequenceOrder
    }

    class RuleAction {
        +UUID id
        +UUID ruleId
        +Enum actionType
        +JSON actionConfig
        +Boolean enabled
    }

    class Alert {
        +UUID id
        +UUID ruleId
        +UUID deviceId
        +Enum severity
        +Enum status
        +String triggerMetric
        +String triggerValue
        +String thresholdValue
        +JSON context
        +DateTime triggeredAt
        +DateTime acknowledgedAt
        +DateTime resolvedAt
        +UUID acknowledgedBy
    }

    class Certificate {
        +UUID id
        +UUID deviceId
        +String commonName
        +String fingerprint
        +String pem
        +String issuerDN
        +String subjectDN
        +Enum status
        +DateTime issuedAt
        +DateTime expiresAt
        +DateTime revokedAt
        +String revocationReason
    }

    class AuditLog {
        +UUID id
        +UUID organizationId
        +UUID actorId
        +String actorType
        +String action
        +String resourceType
        +UUID resourceId
        +JSON before
        +JSON after
        +String ipAddress
        +String userAgent
        +DateTime occurredAt
    }

    %% Identity & Organisation relationships
    Organization "1" --> "0..*" Fleet : has many
    Organization "1" --> "0..*" DeviceModel : owns
    Organization "1" --> "0..*" Firmware : owns
    Organization "1" --> "0..*" Rule : defines
    Organization "1" --> "0..*" AuditLog : recorded in

    %% Fleet and Device
    Fleet "1" --> "0..*" Device : contains
    DeviceModel "1" --> "0..*" Device : classified by
    DeviceModel "1" --> "0..*" DeviceTemplate : has
    DeviceTemplate "1" --> "0..*" Device : instantiated as

    %% Device relationships
    Device "1" --> "1" DeviceCredential : secured by
    Device "1" --> "1" DeviceShadow : reflected in
    Device "1" --> "0..*" TelemetryStream : emits
    Device "1" --> "0..*" Certificate : authenticated by
    Device "1" --> "0..*" Alert : triggers

    %% Telemetry
    TelemetryStream "1" --> "0..*" TelemetryDataPoint : contains

    %% Firmware and OTA
    Firmware "1" --> "1..*" FirmwareVersion : versioned as
    OTAJob "1" --> "1" FirmwareVersion : deploys
    OTAJob "0..*" --> "0..1" Fleet : targets fleet
    OTAJob "0..*" --> "0..1" Device : targets device

    %% Rules and Alerts
    Rule "1" --> "1..*" RuleCondition : evaluated by
    Rule "1" --> "1..*" RuleAction : executes
    Rule "1" --> "0..*" Alert : generates
```

---

## Entity Descriptions

### Organization
The top-level tenant in the multi-tenant hierarchy. Every resource belongs to exactly one
organization. The `plan` field controls feature access (FREE, STARTER, PROFESSIONAL, ENTERPRISE).

### Fleet
A logical grouping of devices within an organization, typically representing a physical site,
product line, or customer deployment. Fleets are the primary scope for rules, OTA jobs, and
dashboards.

### DeviceModel
Describes a class of hardware (manufacturer, model number, hardware revision). Models define
which firmware families are compatible and what telemetry schema devices of that model expose.

### DeviceTemplate
A reusable configuration blueprint derived from a DeviceModel. It specifies default shadow state,
expected telemetry schema, and available command schema, allowing new devices to be pre-configured
consistently at provisioning time.

### Device
The central entity—represents a single physical IoT device. Status values: `PENDING`,
`ACTIVE`, `INACTIVE`, `QUARANTINED`, `DECOMMISSIONED`.

### DeviceCredential
Stores the MQTT password hash (for username/password auth) or references the client certificate
(for mTLS auth). Credential type: `CERTIFICATE` or `PASSWORD`.

### DeviceShadow
A JSON document that holds the device's last-reported state (`reported`), the platform's desired
state (`desired`), and the computed `delta` (desired minus reported). Version is incremented on
every write and used for optimistic concurrency.

### Firmware
Represents a firmware product family for a specific DeviceModel (e.g., "Sensor Edge Firmware for
ModelX"). Acts as a container for multiple versioned releases.

### FirmwareVersion
A specific, immutable release of a Firmware. Once `status` is `RELEASED` the binary and checksum
are frozen. Status values: `DRAFT`, `RELEASED`, `DEPRECATED`.

### OTAJob
An ordered deployment of a FirmwareVersion to a Fleet or individual Device. The `rolloutPolicy`
JSON captures wave percentages, bake periods, and success thresholds. Status values: `PENDING`,
`IN_PROGRESS`, `PAUSED`, `COMPLETED`, `FAILED`.

### TelemetryStream
Defines a logical data channel from a device (e.g., "temperature", "GPS", "motor-current"). Each
stream maps to a dedicated MQTT sub-topic and has its own JSON schema for payload validation.

### TelemetryDataPoint
An individual time-series measurement. This entity is stored in InfluxDB (or TimescaleDB) rather
than PostgreSQL—it is shown here to make the logical model complete.

### Rule
A user-configured monitoring rule scoped to a Fleet. A rule has one or more conditions (forming a
logical AND/OR tree) and one or more actions to execute when the conditions are met.

### RuleCondition
A single predicate on a telemetry field. Operators: `GT`, `GTE`, `LT`, `LTE`, `EQ`, `NEQ`,
`CONTAINS`. Multiple conditions within a rule are combined using `logicalOperator` (AND or OR).

### RuleAction
The action performed when a rule fires. Types: `CREATE_ALERT`, `SEND_NOTIFICATION`,
`EXECUTE_COMMAND`, `CALL_WEBHOOK`.

### Alert
An event record created when a Rule's conditions are satisfied. Status values: `OPEN`,
`ACKNOWLEDGED`, `RESOLVED`. Alerts are deduplicated by (ruleId, deviceId) within a configurable
suppression window.

### Certificate
An X.509 certificate issued to a Device by the platform's internal CA or an external CA. Status
values: `ACTIVE`, `EXPIRED`, `REVOKED`.

### AuditLog
An immutable record of every state-changing operation performed by a human or service actor.
Captures before/after JSON diffs for compliance and forensic purposes.
