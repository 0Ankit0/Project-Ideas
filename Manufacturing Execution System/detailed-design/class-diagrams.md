# Class Diagrams — Manufacturing Execution System

## Overview

This document presents the object-oriented domain model for the Manufacturing Execution System (MES), covering discrete manufacturing workflows for production orders, work center operations, quality management, material traceability, and external system integration. The model is organized across four cohesive subsystems: Production Management, Quality Management, Material Tracking, and Integration.

Each class diagram follows UML conventions rendered via Mermaid `classDiagram` notation. Attributes carry explicit types. Methods are shown with parameter and return types where disambiguation adds clarity. Relationships encode associations (with navigability and multiplicity), compositions (lifecycle ownership), and dependencies (loose coupling across subsystem boundaries).

Design invariants applied throughout:
- All entities use `String` UUID primary keys for distributed uniqueness
- Lifecycle status is a typed `String` attribute on the owning entity, validated against allowed transitions
- Temporal fields use `DateTime` for full audit traceability across time zones
- Methods on domain objects represent service-layer contracts and do not imply direct persistence calls

---

## Production Management Classes

The production management subsystem coordinates the lifecycle of manufacturing execution from ERP order receipt through final goods confirmation. A `ProductionOrder` is released from SAP and decomposed into `WorkOrder` records, one per `RoutingStep`. Each work order executes at a `WorkCenter` during a `Shift`, is assigned to an `Employee`, and is realized as a sequence of `Operation` instances on individual `Machine` assets.

```mermaid
classDiagram
    class ProductionOrder {
        +String orderId
        +String erpOrderNumber
        +String productCode
        +String productDescription
        +Decimal plannedQuantity
        +Decimal completedQuantity
        +Decimal scrapQuantity
        +String uom
        +DateTime plannedStartDate
        +DateTime plannedEndDate
        +DateTime actualStartDate
        +DateTime actualEndDate
        +String status
        +String priority
        +String customerId
        +String salesOrderRef
        +String routingId
        +String bomId
        +String facilityId
        +String plantCode
        +String createdBy
        +DateTime createdAt
        +DateTime updatedAt
        +release() Boolean
        +hold(reason: String) void
        +resume() void
        +close() void
        +cancel(reason: String) void
        +calculateOEE() Decimal
        +getOpenWorkOrders() List~WorkOrder~
        +getRemainingQuantity() Decimal
        +isComplete() Boolean
        +getProgress() Decimal
    }

    class WorkOrder {
        +String workOrderId
        +String productionOrderId
        +String routingStepId
        +String workCenterId
        +Integer sequenceNumber
        +Decimal plannedQuantity
        +Decimal completedQuantity
        +Decimal scrapQuantity
        +Decimal reworkQuantity
        +DateTime scheduledStart
        +DateTime scheduledEnd
        +DateTime actualStart
        +DateTime actualEnd
        +Integer plannedDurationMins
        +Integer actualDurationMins
        +String status
        +String operatorId
        +String shiftId
        +String setupPersonId
        +DateTime createdAt
        +DateTime updatedAt
        +start(operatorId: String, shiftId: String) Boolean
        +complete(qty: Decimal, scrap: Decimal) void
        +pause(reason: String) void
        +resume() void
        +abort(reason: String) void
        +reportScrap(qty: Decimal, reasonCode: String) void
        +getDowntimeMinutes() Integer
        +getEfficiency() Decimal
        +isOverdue() Boolean
    }

    class Operation {
        +String operationId
        +String workOrderId
        +String operationCode
        +String operationName
        +String operationType
        +Integer sequence
        +String status
        +String machineId
        +String operatorId
        +Decimal plannedCycleTimeSecs
        +Decimal actualCycleTimeSecs
        +Decimal setupTimeMins
        +Decimal teardownTimeMins
        +DateTime startedAt
        +DateTime completedAt
        +String instructions
        +String completionNotes
        +Map~String,String~ parameters
        +begin(machineId: String) void
        +finish(notes: String) void
        +fail(reason: String) void
        +logParameter(key: String, value: String) void
        +getDurationSecs() Integer
        +isWithinCycleTime() Boolean
    }

    class WorkCenter {
        +String workCenterId
        +String workCenterCode
        +String workCenterName
        +String workCenterType
        +String facilityId
        +String departmentId
        +String costCenterId
        +Decimal plannedCapacityHrs
        +String defaultShiftId
        +Boolean isActive
        +String locationCode
        +String supervisorId
        +DateTime createdAt
        +getAvailableMachines() List~Machine~
        +getCurrentLoad() Decimal
        +getScheduledOrders(date: Date) List~WorkOrder~
        +getOEE(from: DateTime, to: DateTime) OEESnapshot
        +isAvailable(from: DateTime, to: DateTime) Boolean
    }

    class Machine {
        +String machineId
        +String machineCode
        +String machineName
        +String machineType
        +String workCenterId
        +String manufacturer
        +String model
        +String serialNumber
        +String assetTag
        +DateTime installDate
        +DateTime lastMaintenanceDate
        +DateTime nextMaintenanceDate
        +String status
        +Decimal theoreticalCycleTimeSecs
        +String ipAddress
        +String scadaNodeId
        +String plcAddress
        +Boolean iotEnabled
        +DateTime createdAt
        +startOperation(operationId: String) Boolean
        +stopOperation(reason: String) void
        +reportDowntime(category: String, reason: String) void
        +getLastTelemetry() Telemetry
        +getDowntimeSummary(range: DateRange) Map~String,Integer~
        +isOperational() Boolean
    }

    class Shift {
        +String shiftId
        +String shiftCode
        +String shiftName
        +String facilityId
        +Time startTime
        +Time endTime
        +Integer durationMins
        +Integer plannedBreakMins
        +Boolean isActive
        +List~String~ workingDays
        +getPlannedProductionTime() Integer
        +getActiveEmployees() List~Employee~
        +getWorkOrders(date: Date) List~WorkOrder~
    }

    class Employee {
        +String employeeId
        +String employeeCode
        +String firstName
        +String lastName
        +String email
        +String badgeId
        +String departmentId
        +String jobTitle
        +String supervisorId
        +List~String~ certifications
        +List~String~ skillCodes
        +Boolean isActive
        +DateTime hiredDate
        +isAuthorizedFor(operationCode: String) Boolean
        +getCertificationExpiry(certCode: String) DateTime
        +getActiveWorkOrders() List~WorkOrder~
        +clockIn(shiftId: String) void
        +clockOut() void
    }

    class RoutingStep {
        +String routingStepId
        +String routingId
        +Integer stepSequence
        +String operationCode
        +String operationName
        +String workCenterCode
        +Decimal plannedCycleTimeSecs
        +Decimal setupTimeMins
        +Decimal teardownTimeMins
        +Boolean isMandatory
        +String qualityPlanId
        +List~String~ resourceCodes
        +String instructions
        +String predecessorStepId
        +Boolean isActive
        +getNextStep() RoutingStep
        +getPreviousStep() RoutingStep
        +requiresQualityCheck() Boolean
    }

    ProductionOrder "1" --> "1..*" WorkOrder : generates
    WorkOrder "1" --> "1..*" Operation : contains
    WorkOrder "*" --> "1" WorkCenter : executes at
    WorkOrder "*" --> "1" Shift : runs during
    WorkOrder "*" --> "1" Employee : assigned to
    Operation "*" --> "1" Machine : runs on
    WorkCenter "1" --> "1..*" Machine : contains
    ProductionOrder "1" --> "1..*" RoutingStep : follows
```

---

## Quality Management Classes

The quality subsystem governs inspection planning, SPC charting, defect recording, and non-conformance disposition. A `QualityPlan` is attached to a routing step and specifies the characteristics to be measured. `InspectionResult` aggregates operator-entered readings and evaluates pass/fail status against spec limits. SPC control is maintained through `ControlChart` objects that apply Western Electric and Nelson rules, generating `SpcViolation` records. Severe defects escalate to `NCR` records that carry a full review and disposition workflow.

```mermaid
classDiagram
    class QualityPlan {
        +String qualityPlanId
        +String qualityPlanCode
        +String description
        +String productCode
        +String operationCode
        +String routingStepId
        +String inspectionType
        +String samplingMethod
        +Integer sampleSize
        +Integer frequency
        +String frequencyUnit
        +Boolean isDestructive
        +Boolean isMandatory
        +String status
        +String approvedBy
        +DateTime approvedAt
        +DateTime effectiveFrom
        +DateTime effectiveTo
        +getActiveCharacteristics() List~InspectionCharacteristic~
        +calculateSampleSize(lotSize: Integer) Integer
        +isApplicable(operationCode: String) Boolean
        +clone(newVersion: String) QualityPlan
    }

    class InspectionCharacteristic {
        +String characteristicId
        +String qualityPlanId
        +String name
        +String measurementType
        +String unit
        +Decimal nominalValue
        +Decimal upperSpecLimit
        +Decimal lowerSpecLimit
        +Decimal upperControlLimit
        +Decimal lowerControlLimit
        +Decimal upperWarningLimit
        +Decimal lowerWarningLimit
        +String measurementDevice
        +Boolean isCritical
        +Boolean isSPC
        +Integer sequence
        +isWithinSpec(value: Decimal) Boolean
        +isWithinControl(value: Decimal) Boolean
        +getDeviation(value: Decimal) Decimal
    }

    class InspectionResult {
        +String inspectionId
        +String qualityPlanId
        +String workOrderId
        +String operationId
        +String materialLotId
        +String inspectorId
        +String shiftId
        +DateTime inspectedAt
        +String overallResult
        +Integer sampleSize
        +Integer passCount
        +Integer failCount
        +String disposition
        +String comments
        +String linkedNCRId
        +Boolean isReinspection
        +String originalInspectionId
        +pass() void
        +fail(defectCodes: List~String~) void
        +defer(reason: String) void
        +linkNCR(ncrId: String) void
        +getPassRate() Decimal
        +requiresNCR() Boolean
    }

    class InspectionReading {
        +String readingId
        +String inspectionId
        +String characteristicId
        +Decimal measuredValue
        +String textValue
        +Boolean passedSpec
        +Boolean passedControl
        +String measurementDeviceId
        +DateTime recordedAt
        +String recordedBy
        +String comments
    }

    class ControlChart {
        +String chartId
        +String characteristicId
        +String workCenterId
        +String productCode
        +String chartType
        +Decimal upperControlLimit
        +Decimal centerLine
        +Decimal lowerControlLimit
        +Decimal upperWarningLimit
        +Decimal lowerWarningLimit
        +Integer subgroupSize
        +Integer baselineSampleCount
        +DateTime baselineFrom
        +DateTime baselineTo
        +Boolean isActive
        +DateTime lastUpdatedAt
        +addPoint(value: Decimal, ts: DateTime) ControlChartPoint
        +detectViolations() List~SpcViolation~
        +recalculateLimits() void
        +getRecentPoints(n: Integer) List~ControlChartPoint~
        +isInControl() Boolean
    }

    class ControlChartPoint {
        +String pointId
        +String chartId
        +Decimal value
        +Decimal subgroupMean
        +Decimal subgroupRange
        +DateTime timestamp
        +String workOrderId
        +String operatorId
        +Boolean isViolation
        +String violationType
        +Boolean isExcluded
        +String exclusionReason
    }

    class Defect {
        +String defectId
        +String inspectionId
        +String workOrderId
        +String operationId
        +String materialLotId
        +String defectCode
        +String defectCategory
        +String defectDescription
        +String severity
        +Integer defectCount
        +String location
        +String causeCode
        +String discoveredBy
        +DateTime discoveredAt
        +String disposition
        +String reworkInstructions
        +Boolean isReworked
        +DateTime reworkedAt
        +calculateCost() Decimal
        +reclassify(newCode: String, reason: String) void
        +linkCause(causeCode: String) void
    }

    class NCR {
        +String ncrId
        +String ncrNumber
        +String productionOrderId
        +String workOrderId
        +String materialLotId
        +String productCode
        +Decimal nonconformingQty
        +String nonconformanceType
        +String description
        +String immediateAction
        +String rootCause
        +String correctiveAction
        +String preventiveAction
        +String disposition
        +String status
        +String severity
        +String reportedBy
        +DateTime reportedAt
        +String reviewedBy
        +DateTime reviewedAt
        +String approvedBy
        +DateTime approvedAt
        +DateTime dueDate
        +open() void
        +review(findings: String) void
        +approve(disposition: String) void
        +close(preventiveAction: String) void
        +escalate(reason: String) void
        +getAge() Integer
        +isOverdue() Boolean
    }

    QualityPlan "1" --> "1..*" InspectionCharacteristic : defines
    QualityPlan "1" --> "0..*" InspectionResult : evaluated by
    InspectionResult "1" --> "1..*" InspectionReading : contains
    InspectionResult "1" --> "0..*" Defect : records
    InspectionResult "0..1" --> "0..1" NCR : triggers
    InspectionCharacteristic "1" --> "0..1" ControlChart : drives
    ControlChart "1" --> "1..*" ControlChartPoint : accumulates
```

---

## Material Tracking Classes

Material tracking maintains full genealogy for raw materials, components, work-in-process, and finished goods. Every physical quantity is represented as a `MaterialLot` with a unique lot number, current status, and quality disposition. A `Batch` links input lots consumed during production to the output lots generated, forming the directed acyclic graph that enables end-to-end traceability. `BOM` and `BOMLine` drive automatic material requirements calculations and backflush logic.

```mermaid
classDiagram
    class Material {
        +String materialId
        +String materialCode
        +String materialDescription
        +String materialType
        +String uom
        +String secondaryUom
        +Decimal conversionFactor
        +String storageConditions
        +Integer shelfLifeDays
        +Boolean isLotTracked
        +Boolean isSerialTracked
        +Decimal minimumOrderQty
        +Decimal standardCost
        +String erpMaterialNumber
        +String hazmatClass
        +Boolean isActive
        +DateTime createdAt
        +getOnHandQuantity(locationId: String) Decimal
        +getAvailableLots(locationId: String) List~MaterialLot~
        +requiresInspection() Boolean
        +getLeadTimeDays() Integer
    }

    class MaterialLot {
        +String lotId
        +String lotNumber
        +String materialId
        +String supplierId
        +String supplierLotNumber
        +Decimal originalQuantity
        +Decimal currentQuantity
        +Decimal reservedQuantity
        +String uom
        +String status
        +String qualityStatus
        +String locationId
        +DateTime manufacturingDate
        +DateTime expiryDate
        +DateTime receivedDate
        +String receivedBy
        +String inspectionStatus
        +String inspectionId
        +List~String~ parentLotIds
        +List~String~ childLotIds
        +Boolean isQuarantined
        +String quarantineReason
        +receive(qty: Decimal, location: String) void
        +issue(qty: Decimal, workOrderId: String) void
        +quarantine(reason: String) void
        +release() void
        +split(qty: Decimal) MaterialLot
        +merge(other: MaterialLot) void
        +transfer(toLocation: String) void
        +getAvailableQuantity() Decimal
        +isExpired() Boolean
        +isExpiringSoon(days: Integer) Boolean
    }

    class Batch {
        +String batchId
        +String batchNumber
        +String productionOrderId
        +String workOrderId
        +String materialId
        +Decimal plannedQuantity
        +Decimal actualQuantity
        +Decimal yieldQuantity
        +Decimal scrapQuantity
        +String status
        +DateTime startedAt
        +DateTime completedAt
        +String shiftId
        +String workCenterId
        +List~String~ inputLotIds
        +List~String~ outputLotIds
        +String qualityStatus
        +start() void
        +complete(actualQty: Decimal) void
        +recordParameter(name: String, value: String) void
        +getYieldPercentage() Decimal
        +getLotLineage() Map~String,List~String~~
    }

    class BOM {
        +String bomId
        +String bomCode
        +String productCode
        +String bomDescription
        +String bomType
        +String revisionNumber
        +String status
        +Decimal baseQuantity
        +String baseUom
        +DateTime effectiveFrom
        +DateTime effectiveTo
        +String approvedBy
        +DateTime approvedAt
        +Boolean isActive
        +getActiveLines() List~BOMLine~
        +calculateRequirements(qty: Decimal) List~MaterialRequirement~
        +isValidFor(date: Date) Boolean
        +clone(newRevision: String) BOM
    }

    class BOMLine {
        +String bomLineId
        +String bomId
        +String componentMaterialId
        +Integer sequence
        +Decimal quantity
        +String uom
        +Decimal scrapFactor
        +String operationCode
        +String issueMethod
        +Boolean isPhantom
        +Boolean isByProduct
        +Decimal componentCost
        +String alternateGroupId
        +Integer alternatePriority
        +String notes
        +calculateNetQuantity(prodQty: Decimal) Decimal
        +getAlternates() List~BOMLine~
        +isBackflushed() Boolean
    }

    class MaterialMovement {
        +String movementId
        +String movementType
        +String materialId
        +String lotId
        +String fromLocationId
        +String toLocationId
        +String workOrderId
        +String productionOrderId
        +Decimal quantity
        +String uom
        +String reason
        +String referenceDocument
        +String performedBy
        +DateTime performedAt
        +Boolean isReversed
        +String reversedByMovementId
        +String erpDocumentNumber
        +reverse(reason: String) MaterialMovement
        +postToERP() Boolean
        +getValueAmount() Decimal
    }

    Material "1" --> "0..*" MaterialLot : instantiated as
    Material "1" --> "0..*" BOMLine : referenced in
    BOM "1" --> "1..*" BOMLine : composed of
    MaterialLot "1" --> "0..*" MaterialMovement : tracked via
    Batch "1" --> "1..*" MaterialLot : consumes
    Batch "1" --> "1..*" MaterialLot : produces
    Batch "*" --> "1" BOM : follows
```

---

## Integration Classes

Integration classes bridge the MES with external systems including SAP ERP, SCADA platforms, and IoT device networks. The `ERPConnector` implements a bidirectional synchronization adapter for production order receipt and goods movement confirmation. The `SCADAAdapter` uses OPC-UA to read and write machine tags in real time. `IoTDevice` instances publish telemetry to an `IoTHub`, which fans messages into a `MessageBroker` (Kafka) for downstream stream processing and enrichment.

```mermaid
classDiagram
    class ERPConnector {
        +String connectorId
        +String connectorName
        +String erpSystem
        +String erpVersion
        +String baseUrl
        +String clientId
        +String authMethod
        +Integer timeoutSecs
        +Integer retryAttempts
        +Boolean isEnabled
        +DateTime lastSyncAt
        +String lastSyncStatus
        +connect() Boolean
        +disconnect() void
        +pushProductionOrder(order: ProductionOrder) ERPSyncResult
        +pullProductionOrders(plant: String, from: Date) List~ProductionOrder~
        +confirmGoodsIssue(movement: MaterialMovement) String
        +confirmGoodsReceipt(batch: Batch) String
        +pushQualityNotification(ncr: NCR) String
        +syncMasterData(entityType: String) SyncResult
        +getHealth() HealthStatus
    }

    class ERPSyncResult {
        +String syncId
        +String connectorId
        +String direction
        +String entityType
        +String entityId
        +String erpDocumentNumber
        +Boolean success
        +String errorCode
        +String errorMessage
        +DateTime syncedAt
        +Integer retryCount
        +Map~String,String~ metadata
        +retry() ERPSyncResult
        +markFailed(error: String) void
    }

    class SCADAAdapter {
        +String adapterId
        +String adapterName
        +String protocol
        +String host
        +Integer port
        +String namespace
        +String securityMode
        +Boolean isConnected
        +DateTime connectedAt
        +List~String~ subscribedTags
        +Integer pollIntervalMs
        +DateTime lastDataAt
        +connect() Boolean
        +disconnect() void
        +readTag(tagPath: String) TagValue
        +writeTags(tags: Map~String,Object~) Boolean
        +subscribeTags(tagPaths: List~String~) void
        +sendRecipe(machineId: String, recipe: Map) Boolean
        +startMachine(machineId: String) Boolean
        +stopMachine(machineId: String) Boolean
        +getHealth() HealthStatus
    }

    class TagValue {
        +String tagPath
        +Object value
        +String dataType
        +String quality
        +DateTime timestamp
        +Boolean isGood() Boolean
        +toDecimal() Decimal
        +toBoolean() Boolean
        +toString() String
    }

    class IoTDevice {
        +String deviceId
        +String deviceName
        +String deviceType
        +String machineId
        +String manufacturer
        +String model
        +String firmwareVersion
        +String protocol
        +String connectionString
        +String status
        +DateTime lastSeenAt
        +DateTime provisionedAt
        +Map~String,String~ properties
        +Boolean isSimulated
        +provision() Boolean
        +decommission() void
        +sendCommand(command: String, payload: Map) Boolean
        +getLatestTelemetry() List~Telemetry~
        +updateFirmware(version: String) Boolean
        +getDeviceTwin() Map~String,Object~
        +isOnline() Boolean
    }

    class Telemetry {
        +String telemetryId
        +String deviceId
        +String machineId
        +String tagName
        +String dataType
        +Decimal numericValue
        +String stringValue
        +Boolean boolValue
        +String unit
        +String quality
        +DateTime deviceTimestamp
        +DateTime ingestedAt
        +Boolean isAnomaly
        +Decimal anomalyScore
        +Boolean isProcessed
        +String enrichedWorkOrderId
        +String enrichedShiftId
        +toJson() String
        +isValidQuality() Boolean
        +getAgeSecs() Integer
    }

    class IoTHub {
        +String hubId
        +String hubName
        +String connectionString
        +Integer maxDevices
        +Integer currentDeviceCount
        +String messagingTier
        +Boolean isActive
        +registerDevice(device: IoTDevice) String
        +removeDevice(deviceId: String) Boolean
        +sendCloudToDevice(deviceId: String, msg: Map) Boolean
        +invokeDirectMethod(deviceId: String, method: String, payload: Map) Map
        +getDeviceTwin(deviceId: String) Map
        +updateDesiredProperties(deviceId: String, props: Map) Boolean
        +queryDevices(condition: String) List~IoTDevice~
    }

    class MessageBroker {
        +String brokerId
        +String brokerType
        +String bootstrapServers
        +String schemaRegistryUrl
        +Map~String,String~ topicConfig
        +publish(topic: String, key: String, payload: Object) Boolean
        +subscribe(topic: String, groupId: String, handler: Function) void
        +unsubscribe(topic: String, groupId: String) void
        +getTopicLag(topic: String, groupId: String) Long
        +createTopic(name: String, partitions: Integer, replication: Integer) Boolean
    }

    ERPConnector "1" --> "0..*" ERPSyncResult : produces
    SCADAAdapter "1" --> "0..*" TagValue : reads
    IoTHub "1" --> "0..*" IoTDevice : manages
    IoTDevice "1" --> "0..*" Telemetry : emits
    ERPConnector ..> MessageBroker : publishes events via
    SCADAAdapter ..> MessageBroker : streams data via
    IoTHub ..> MessageBroker : forwards telemetry via
```

---

## Class Relationships

The cross-subsystem diagram below shows how the four domain areas interconnect, tracing the flow from ERP-originated production orders through shop-floor execution, quality validation, and material genealogy, back to integration confirmations. Integration classes are shown as dashed dependencies to emphasize their role as adapters rather than core domain participants.

```mermaid
classDiagram
    class ProductionOrder {
        +String orderId
        +String status
        +Decimal completedQuantity
    }
    class WorkOrder {
        +String workOrderId
        +String status
    }
    class Operation {
        +String operationId
        +String status
    }
    class Machine {
        +String machineId
        +String status
    }
    class MaterialLot {
        +String lotId
        +String qualityStatus
    }
    class Batch {
        +String batchId
        +Decimal yieldQuantity
    }
    class QualityPlan {
        +String qualityPlanId
        +Boolean isMandatory
    }
    class InspectionResult {
        +String inspectionId
        +String overallResult
    }
    class NCR {
        +String ncrId
        +String status
    }
    class Telemetry {
        +String telemetryId
        +DateTime deviceTimestamp
    }
    class ERPConnector {
        +String connectorId
        +String lastSyncStatus
    }
    class SCADAAdapter {
        +String adapterId
        +Boolean isConnected
    }

    ProductionOrder "1" --> "1..*" WorkOrder : drives
    WorkOrder "1" --> "1..*" Operation : sequences
    WorkOrder "1" --> "1..*" Batch : produces
    WorkOrder "1" --> "0..*" InspectionResult : validated by
    Operation "1" --> "1" Machine : executed on
    Machine "1" --> "0..*" Telemetry : streams
    Batch "1" --> "1..*" MaterialLot : consumes and produces
    InspectionResult "0..1" --> "0..1" NCR : escalates to
    QualityPlan "1" --> "0..*" InspectionResult : governs
    ERPConnector ..> ProductionOrder : synchronizes
    ERPConnector ..> MaterialLot : posts movements
    SCADAAdapter ..> Machine : controls and monitors
    SCADAAdapter ..> Telemetry : ingests real-time data
```
