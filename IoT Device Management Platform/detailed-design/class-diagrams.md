# Class Diagrams — IoT Device Management Platform

## Domain Model Organization

The domain model is organized into five bounded contexts that mirror the platform's core capabilities: **Device Registry**, **Telemetry & Alerting**, **Firmware/OTA**, **Security**, and **Command Execution**. Each context owns its aggregate roots and exposes domain events for cross-context integration. Aggregates are persisted in PostgreSQL; Redis caches frequently read projections; Kafka carries domain events between services.

The diagrams below use UML class notation rendered in Mermaid. Aggregates are marked with `«aggregate»`; value objects with `«value object»`; domain events with `«event»`. All identifiers are UUID v4 generated at the application layer, never at the database layer, to ensure portability across shards.

---

## Core Domain — Device Registry

This context owns the canonical record of every device and its configuration. `Device` is the primary aggregate root. `DeviceGroup` forms a hierarchy tree (closure table in PostgreSQL) to support logical fleet segmentation without hard depth limits. `DeviceShadow` is a 1-to-1 companion aggregate that tracks desired vs. reported state; it lives in its own table to allow separate write paths with optimistic locking.

```mermaid
classDiagram
    direction TB

    class Organization {
        «aggregate»
        +UUID id
        +String name
        +String slug
        +PlanTier planTier
        +Int maxDevices
        +Int maxTelemetryRatePerSecond
        +OrganizationStatus status
        +DateTime createdAt
        +DateTime updatedAt
        +activate() void
        +suspend() void
        +upgradePlan(PlanTier) void
    }

    class Device {
        «aggregate»
        +UUID id
        +UUID organizationId
        +UUID deviceModelId
        +UUID groupId
        +String serialNumber
        +String name
        +DeviceStatus status
        +String firmwareVersion
        +DateTime lastSeenAt
        +InetAddress ipAddress
        +Decimal locationLat
        +Decimal locationLon
        +Map~String,String~ tags
        +DateTime provisionedAt
        +DateTime createdAt
        +DateTime updatedAt
        +provision(ProvisionRequest) DeviceProvisionedEvent
        +updateLastSeen(InetAddress) void
        +enable() void
        +disable() void
        +suspend(String reason) void
        +decommission() DeviceDecommissionedEvent
        +updateLocation(Decimal, Decimal) void
        +attachTag(String, String) void
        +removeTag(String) void
    }

    class DeviceGroup {
        «aggregate»
        +UUID id
        +UUID organizationId
        +UUID parentGroupId
        +String name
        +String description
        +Map~String,String~ metadata
        +Int depth
        +DateTime createdAt
        +DateTime updatedAt
        +addChild(DeviceGroup) void
        +removeChild(UUID) void
        +isAncestorOf(UUID) Boolean
    }

    class DeviceModel {
        «value object»
        +UUID id
        +UUID organizationId
        +String manufacturer
        +String modelName
        +String modelVersion
        +ConnectivityProtocol[] connectivityProtocols
        +PowerSource powerSource
        +String cpuArch
        +Int flashKb
        +Int ramKb
        +DateTime createdAt
        +supportsProtocol(ConnectivityProtocol) Boolean
    }

    class DeviceShadow {
        «aggregate»
        +UUID deviceId
        +Map desired
        +Map reported
        +Map metadata
        +Int version
        +DateTime lastUpdatedAt
        +updateDesired(Map) ShadowDeltaEvent
        +applyReported(Map) void
        +getDelta() Map
        +clearDesired(String key) void
    }

    class DeviceStatus {
        «enumeration»
        UNREGISTERED
        PROVISIONING
        ACTIVE
        INACTIVE
        SUSPENDED
        DECOMMISSIONED
    }

    class PowerSource {
        «enumeration»
        BATTERY
        WIRED
        SOLAR
        POE
        HYBRID
    }

    class ConnectivityProtocol {
        «enumeration»
        MQTT
        COAP
        HTTP
        LORAWAN
        ZIGBEE
        BLUETOOTH_LE
        LTE_M
        NB_IOT
    }

    class PlanTier {
        «enumeration»
        STARTER
        PROFESSIONAL
        ENTERPRISE
        CUSTOM
    }

    class OrganizationStatus {
        «enumeration»
        ACTIVE
        SUSPENDED
        TERMINATED
    }

    Organization "1" --> "0..*" Device : owns
    Organization "1" --> "0..*" DeviceGroup : owns
    Device "0..*" --> "1" DeviceModel : typed by
    Device "0..*" --> "1" DeviceGroup : member of
    Device "1" --> "1" DeviceShadow : shadowed by
    DeviceGroup "0..1" --> "0..*" DeviceGroup : parent-child
    Device --> DeviceStatus
    DeviceModel --> PowerSource
    DeviceModel --> ConnectivityProtocol
    Organization --> PlanTier
    Organization --> OrganizationStatus
```

### Design Notes — Device Registry

`Device` and `DeviceShadow` are separate aggregates despite the 1-to-1 relationship. This separation exists because shadow updates (from devices reporting state over MQTT) happen at very high frequency — potentially thousands per second — while device metadata updates are infrequent. Splitting the aggregates allows the shadow write path to use its own optimistic-lock version counter without contending with metadata updates.

`DeviceGroup` supports a self-referential parent/child hierarchy. The `depth` attribute is maintained by the service layer on every write, and a PostgreSQL recursive CTE is used for ancestry queries. The closure table pattern is maintained in a separate `device_group_ancestors` join table for O(1) ancestor lookups.

Tags on `Device` are stored as `jsonb` in PostgreSQL with a GIN index, enabling fast queries like "all devices with tag environment=production". The `Map<String,String>` type here represents that flat key-value constraint enforced at the service layer.

---

## Telemetry Domain

The Telemetry domain handles ingestion validation, schema enforcement, and the rules engine. `AlertRule` is the aggregate root for alerting configuration. `AlertEvent` is an append-only entity (never mutated in place except for acknowledgment/resolution status fields).

```mermaid
classDiagram
    direction TB

    class TelemetryRecord {
        «value object»
        +UUID id
        +UUID deviceId
        +UUID organizationId
        +String metric
        +Float value
        +String unit
        +TelemetryQuality quality
        +DateTime deviceTimestamp
        +DateTime serverTimestamp
        +Map~String,String~ tags
        +Boolean isNormalized
        +validate() ValidationResult
        +normalize(TelemetrySchema) TelemetryRecord
    }

    class TelemetrySchema {
        «aggregate»
        +UUID id
        +UUID deviceModelId
        +String schemaVersion
        +TelemetryFieldDef[] fields
        +Boolean strictMode
        +DateTime createdAt
        +DateTime deprecatedAt
        +validateRecord(TelemetryRecord) ValidationResult
        +getField(String name) TelemetryFieldDef
        +addField(TelemetryFieldDef) void
        +deprecate() void
    }

    class TelemetryFieldDef {
        «value object»
        +String name
        +FieldType dataType
        +String unit
        +Float minValue
        +Float maxValue
        +Boolean required
        +String description
        +validate(Object value) Boolean
        +convertUnit(String targetUnit) Float
    }

    class AlertRule {
        «aggregate»
        +UUID id
        +UUID organizationId
        +String name
        +String description
        +UUID deviceGroupId
        +String metricName
        +AlertConditionType conditionType
        +ConditionOperator conditionOperator
        +Float thresholdValue
        +Int windowSeconds
        +AlertSeverity severity
        +Int cooldownSeconds
        +Boolean autoResolve
        +Int escalationTimeoutSeconds
        +NotificationChannel[] notificationChannels
        +Boolean isActive
        +DateTime createdAt
        +DateTime updatedAt
        +evaluate(TelemetryRecord, AggregationResult) AlertEvaluationResult
        +activate() void
        +deactivate() void
        +updateThreshold(Float) void
    }

    class AlertCondition {
        «value object»
        +AlertConditionType type
        +ConditionOperator operator
        +Float thresholdValue
        +Int windowSeconds
        +Float baselineValue
        +Float deviationPct
        +evaluate(Float value) Boolean
        +evaluateWindow(Float[] values) Boolean
        +evaluateRateOfChange(Float prev, Float curr, Long deltaMs) Boolean
    }

    class AlertEvent {
        «aggregate»
        +UUID id
        +UUID alertRuleId
        +UUID deviceId
        +UUID organizationId
        +Float triggeredValue
        +AlertStatus status
        +DateTime triggeredAt
        +DateTime acknowledgedAt
        +UUID acknowledgedBy
        +DateTime resolvedAt
        +Boolean autoResolved
        +DateTime escalatedAt
        +DateTime closedAt
        +String notes
        +acknowledge(UUID operatorId) void
        +resolve(Boolean auto) void
        +escalate() void
        +close(String notes) void
        +isCooldownActive(DateTime now) Boolean
    }

    class AlertConditionType {
        «enumeration»
        THRESHOLD
        ANOMALY
        RATE_OF_CHANGE
        ABSENCE
        WINDOW_AVERAGE
        WINDOW_SUM
    }

    class ConditionOperator {
        «enumeration»
        GT
        GTE
        LT
        LTE
        EQ
        NEQ
    }

    class AlertSeverity {
        «enumeration»
        INFO
        WARNING
        CRITICAL
        FATAL
    }

    class AlertStatus {
        «enumeration»
        TRIGGERED
        ACKNOWLEDGED
        ESCALATED
        RESOLVED
        CLOSED
        AUTO_CLOSED
        SUPPRESSED
    }

    class TelemetryQuality {
        «enumeration»
        GOOD
        UNCERTAIN
        BAD
        STALE
    }

    class FieldType {
        «enumeration»
        FLOAT
        INTEGER
        BOOLEAN
        STRING
        ENUM
        GEO_POINT
    }

    TelemetrySchema "1" --> "1..*" TelemetryFieldDef : defines
    AlertRule "1" --> "1" AlertCondition : configured by
    AlertRule "1" --> "0..*" AlertEvent : produces
    TelemetryRecord --> TelemetryQuality
    TelemetryFieldDef --> FieldType
    AlertRule --> AlertConditionType
    AlertRule --> AlertSeverity
    AlertCondition --> ConditionOperator
    AlertEvent --> AlertStatus
```

### Design Notes — Telemetry Domain

`TelemetryRecord` is modeled as a value object because individual records are immutable once written to InfluxDB. The `normalize()` method converts units (e.g., °F → °C, PSI → bar) based on the `TelemetrySchema` for the device model, producing a new `TelemetryRecord` without mutating the original. This enables the dual-write pattern: raw record to `telemetry-raw` Kafka topic, normalized record to `telemetry-enriched`.

`AlertCondition` encapsulates all condition variants (threshold, anomaly, rate-of-change, absence) as a single value object with a polymorphic `evaluate()` method rather than a class hierarchy. This avoids the expression problem when serializing conditions to PostgreSQL JSONB. The `windowSeconds` field drives InfluxDB Flux queries for window aggregations.

---

## Firmware / OTA Domain

The OTA domain manages the lifecycle of firmware artifacts and orchestrates multi-device rollout. `OTADeployment` is the aggregate root for a rollout campaign; it manages the set of `OTADeviceJob` entities and enforces rollout strategy invariants.

```mermaid
classDiagram
    direction TB

    class FirmwareVersion {
        «aggregate»
        +UUID id
        +UUID organizationId
        +UUID deviceModelId
        +String version
        +String fileUrl
        +String fileSha256
        +Long fileSizeBytes
        +String signatureB64
        +UUID signingKeyId
        +String changelog
        +DateTime releasedAt
        +Boolean isDeprecated
        +DateTime createdAt
        +verifySignature(PublicKey) Boolean
        +generatePresignedUrl(Int ttlSeconds) String
        +deprecate() void
        +isCompatibleWith(DeviceModel) Boolean
    }

    class OTADeployment {
        «aggregate»
        +UUID id
        +UUID organizationId
        +UUID firmwareVersionId
        +UUID targetGroupId
        +RolloutStrategy strategy
        +Int canaryPct
        +WaveInterval[] waveIntervals
        +Float failureThresholdPct
        +Boolean autoRollback
        +UUID rollbackFirmwareId
        +OTADeploymentStatus status
        +DateTime startedAt
        +DateTime completedAt
        +UUID createdBy
        +DateTime createdAt
        +DateTime updatedAt
        +start() void
        +advanceWave() void
        +evaluateHealth() HealthResult
        +triggerRollback() OTARollbackTriggeredEvent
        +complete() void
        +cancel() void
        +getSuccessRate() Float
        +getFailureRate() Float
    }

    class OTADeviceJob {
        «entity»
        +UUID id
        +UUID deploymentId
        +UUID deviceId
        +OTAJobStatus status
        +Int attempt
        +Int maxAttempts
        +DateTime notifiedAt
        +DateTime downloadStartedAt
        +DateTime downloadCompletedAt
        +DateTime installedAt
        +String reportedVersion
        +String errorMessage
        +DateTime createdAt
        +DateTime updatedAt
        +markNotified() void
        +markDownloading() void
        +markDownloadComplete() void
        +markVerified() void
        +markInstalling() void
        +markComplete(String reportedVersion) void
        +markFailed(String error) void
        +scheduleRetry() void
        +isTerminal() Boolean
    }

    class WaveInterval {
        «value object»
        +Int waveNumber
        +Int targetPct
        +Int delayMinutes
        +DateTime scheduledAt
    }

    class RolloutStrategy {
        «enumeration»
        IMMEDIATE
        CANARY
        WAVE
        SCHEDULED
    }

    class OTADeploymentStatus {
        «enumeration»
        DRAFT
        VALIDATING
        ACTIVE
        PAUSED
        ROLLING_BACK
        COMPLETED
        FAILED
        CANCELLED
    }

    class OTAJobStatus {
        «enumeration»
        PENDING
        NOTIFIED
        DOWNLOADING
        DOWNLOAD_FAILED
        VERIFYING
        VERIFIED
        INSTALLING
        INSTALL_FAILED
        REBOOTING
        REPORTING
        COMPLETED
        ROLLED_BACK
        ABANDONED
    }

    FirmwareVersion "1" --> "0..*" OTADeployment : deployed via
    OTADeployment "1" --> "1..*" OTADeviceJob : contains
    OTADeployment --> RolloutStrategy
    OTADeployment --> OTADeploymentStatus
    OTADeployment "1" --> "0..*" WaveInterval : scheduled by
    OTADeviceJob --> OTAJobStatus
```

### Design Notes — Firmware / OTA Domain

`OTADeployment` enforces invariants about rollout progression: the `advanceWave()` method only succeeds when the current wave's `evaluateHealth()` returns a success rate above `(1 - failureThresholdPct)`. This check queries a materialized count from `OTADeviceJob` rows for the current wave cohort. The aggregate does not directly query InfluxDB; instead, `OTAService` provides a `HealthResult` DTO computed externally.

`OTADeviceJob.isTerminal()` returns true for `COMPLETED`, `ROLLED_BACK`, and `ABANDONED` — used by the scheduler to stop retrying. `maxAttempts` defaults to 3 and is configurable per deployment.

`FirmwareVersion.verifySignature()` validates an RSA-PSS SHA-256 signature over the file SHA-256 hash. The signing key is an asymmetric key managed in AWS KMS or HashiCorp Vault, referenced by `signingKeyId`. Verification happens at deployment creation time and again on the device side using the public key embedded in the device's trust store.

---

## Security Domain

The Security domain handles certificate lifecycle, CA management, and the immutable audit trail. `AuditLog` is append-only and partitioned by month in PostgreSQL.

```mermaid
classDiagram
    direction TB

    class DeviceCertificate {
        «aggregate»
        +UUID id
        +UUID deviceId
        +String thumbprint
        +String subjectDN
        +String issuerDN
        +DateTime notBefore
        +DateTime notAfter
        +Boolean isRevoked
        +DateTime revokedAt
        +String revocationReason
        +String certificatePem
        +DateTime createdAt
        +isValid(DateTime at) Boolean
        +isExpiringSoon(Int daysThreshold) Boolean
        +revoke(String reason) CertificateRevokedEvent
        +getThumbprintSHA256() String
        +getDaysUntilExpiry(DateTime from) Int
    }

    class CertificateAuthority {
        «aggregate»
        +UUID id
        +UUID organizationId
        +String name
        +CAType type
        +String subjectDN
        +String crlUrl
        +String ocspUrl
        +Boolean isActive
        +DateTime createdAt
        +issueCertificate(CSR) DeviceCertificate
        +revokeCertificate(String thumbprint, String reason) void
        +publishCRL() void
    }

    class AuditLog {
        «entity»
        +UUID id
        +UUID organizationId
        +String actorId
        +ActorType actorType
        +String action
        +String resourceType
        +UUID resourceId
        +JSONB beforeState
        +JSONB afterState
        +InetAddress ipAddress
        +String userAgent
        +UUID requestId
        +DateTime createdAt
    }

    class ProvisioningRecord {
        «value object»
        +UUID id
        +UUID deviceId
        +ProvisioningMethod method
        +String bootstrapCredentialRef
        +DateTime attemptedAt
        +Boolean success
        +String failureReason
    }

    class CAType {
        «enumeration»
        INTERNAL
        SUBORDINATE
        EXTERNAL_ACME
        AWS_ACM_PCA
        VAULT_PKI
    }

    class ActorType {
        «enumeration»
        USER
        SYSTEM
        DEVICE
        API_KEY
        SERVICE_ACCOUNT
    }

    class ProvisioningMethod {
        «enumeration»
        X509_CERTIFICATE
        PSK
        JWT_BOOTSTRAP
        ZERO_TOUCH
    }

    CertificateAuthority "1" --> "0..*" DeviceCertificate : issues
    DeviceCertificate "0..*" --> "1" Device : authenticates
    AuditLog --> ActorType
    ProvisioningRecord --> ProvisioningMethod
```

### Design Notes — Security Domain

`DeviceCertificate` stores the full PEM-encoded certificate to support CRL generation and OCSP responses without requiring a separate CA API call. The `thumbprint` field is the SHA-256 fingerprint of the DER-encoded certificate, used as the lookup key in Redis for fast MQTT authentication lookups.

`AuditLog` records `beforeState` and `afterState` as JSONB diffs (RFC 7396 merge patch format) rather than full document copies to keep row size manageable. The `requestId` field links back to distributed traces in the observability stack (Jaeger/OpenTelemetry). Because `AuditLog` is append-only, no UPDATE or DELETE statements are ever issued against the table — this is enforced at the PostgreSQL level with a row-level security policy.

---

## Command Execution Domain

Remote command execution is modeled as a finite-state entity. Commands have a TTL: if the device is offline when a command is dispatched, the command is held in a Redis sorted set (keyed by `expires_at`) and delivered on reconnection, or expired automatically.

```mermaid
classDiagram
    direction TB

    class CommandExecution {
        «aggregate»
        +UUID id
        +UUID deviceId
        +UUID organizationId
        +String commandType
        +JSONB payload
        +CommandStatus status
        +Int ttlSeconds
        +DateTime expiresAt
        +DateTime dispatchedAt
        +DateTime acknowledgedAt
        +JSONB resultPayload
        +String errorMessage
        +Int attempt
        +UUID createdBy
        +DateTime createdAt
        +DateTime updatedAt
        +dispatch() CommandDispatchedEvent
        +acknowledge() void
        +complete(JSONB result) CommandCompletedEvent
        +fail(String error) void
        +expire() CommandExpiredEvent
        +isExpired(DateTime now) Boolean
        +canRetry() Boolean
    }

    class CommandStatus {
        «enumeration»
        PENDING
        DISPATCHING
        DISPATCHED
        ACKNOWLEDGED
        SUCCESS
        FAILED
        TIMEOUT
        EXPIRED
    }

    class CommandType {
        «enumeration»
        REBOOT
        CONFIG_UPDATE
        DIAGNOSTIC_COLLECT
        LOG_UPLOAD
        OTA_TRIGGER
        CUSTOM
    }

    class DeviceCommandQueue {
        «value object»
        +UUID deviceId
        +String redisKey
        +Int pendingCount
        +DateTime oldestCommandAt
        +drainToMQTT(MQTTBroker) Int
        +expire(DateTime now) Int
        +peek() CommandExecution
    }

    CommandExecution --> CommandStatus
    CommandExecution --> CommandType
    DeviceCommandQueue --> CommandExecution
```

### Design Notes — Command Domain

`CommandExecution.canRetry()` returns `true` when `status` is `FAILED` and `attempt < 3` and `expiresAt > now`. The retry scheduler runs as a Quartz job every 30 seconds, querying PostgreSQL for retryable commands.

`DeviceCommandQueue` is a projection over Redis — not a PostgreSQL entity. When a device reconnects (MQTT CONNECT event received via Kafka), `CommandService` calls `DeviceCommandQueue.drainToMQTT()` which publishes all queued commands to the device's MQTT command topic in order, then removes them from the sorted set. Commands are stored in Redis as JSON blobs in a `ZSET` scored by `expires_at` (Unix epoch milliseconds), allowing efficient range queries for expiry cleanup via `ZRANGEBYSCORE`.

---

## Cross-Cutting Design Patterns

### Repository Pattern

Every aggregate has a corresponding `Repository` interface in the domain layer with implementations in the infrastructure layer. For example, `DeviceRepository` exposes `findById()`, `findByOrganizationId()`, `findBySerialNumber()`, and `save()`. Spring Data JPA provides the base implementation; custom queries use JPQL or native SQL via `@Query`.

### Value Objects

Value objects are immutable and compared by value, not identity. `TelemetryRecord`, `TelemetryFieldDef`, `AlertCondition`, `WaveInterval`, and `DeviceCommandQueue` are value objects. They are serialized to JSONB columns or embedded in their owning aggregate's table row.

### Aggregate Root and Domain Events

Each aggregate root implements `AbstractAggregateRoot<T>` (Spring Data). Domain events (`DeviceProvisionedEvent`, `ShadowDeltaEvent`, `OTARollbackTriggeredEvent`, `CertificateRevokedEvent`) are registered via `registerEvent()` and published to Kafka by the `@TransactionalEventListener` in the application layer after the transaction commits — ensuring no phantom events on rollback.

### Inheritance vs. Composition

Composition is preferred over inheritance throughout. `AlertCondition` uses an internal `type` discriminator rather than subclasses because PostgreSQL JSONB columns cannot represent polymorphic class hierarchies without custom deserializers. `CommandExecution` similarly uses a `commandType` enum to dispatch to the correct handler rather than a class hierarchy of command types — this avoids the Visitor pattern overhead and simplifies Kafka deserialization.
