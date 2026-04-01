# C4 Code Diagram — Manufacturing Execution System

## Overview

This document provides the code-level (C4 Level 4) architecture view of the MES platform. It shows package structures, class hierarchies, key design patterns, and dependency relationships across all modules. Diagrams are expressed in Mermaid `classDiagram` and `flowchart` notation.

The codebase is organised as a multi-module Maven project (Java/Spring Boot) with a separate `edge-agents` workspace (Node.js/TypeScript). Each bounded context maps to one Maven module and one Kubernetes service.

---

## Code Organization

**Top-Level Repository Layout**

```
mes-platform/
├── services/
│   ├── production-service/          # Production orders, work centres, scheduling
│   ├── quality-service/             # SPC, inspection plans, NCR management
│   ├── material-service/            # Material tracking, lot management, GRN
│   ├── oee-service/                 # OEE calculation, downtime, KPI aggregation
│   ├── integration-service/         # SAP, SCADA, OPC-UA adapters
│   ├── analytics-service/           # Reporting, dashboards, historical queries
│   ├── notification-service/        # Alerts, shift reports, email/SMS dispatch
│   └── api-gateway/                 # Spring Cloud Gateway, auth, rate limiting
├── edge-agents/
│   ├── mqtt-bridge/                 # MQTT → Kafka normaliser
│   ├── opcua-collector/             # OPC-UA tag reader → Kafka
│   └── modbus-collector/            # Modbus TCP → Kafka
├── shared-libs/
│   ├── mes-domain-core/             # Shared value objects, domain events, exceptions
│   ├── mes-security/                # JWT validation, RBAC utilities
│   └── mes-test-support/            # Testcontainers, fixtures, PLC simulator
├── frontend/
│   └── mes-web/                     # React 18 single-page application
├── infra/
│   ├── helm/                        # Helm charts per service
│   ├── terraform/                   # AWS infrastructure (EKS, RDS, MSK)
│   └── alerting/                    # Prometheus alert rules
└── scripts/                         # Dev tooling, seed scripts
```

**Internal Module Layout (per Spring Boot service)**

```
production-service/src/main/java/com/mes/production/
├── api/
│   ├── controller/          # ProductionOrderController, WorkCenterController
│   └── dto/                 # request/ and response/ sub-packages
├── application/             # ProductionOrderApplicationService, WorkCenterApplicationService
├── domain/
│   ├── model/               # ProductionOrder, WorkCenter, Operation
│   ├── event/               # ProductionOrderReleasedEvent, OperationCompletedEvent
│   ├── exception/           # ProductionOrderNotFoundException, …
│   ├── repository/          # ProductionOrderRepository (interface)
│   └── service/             # OeeCalculator, CapacityChecker
└── infrastructure/
    ├── persistence/         # JpaProductionOrderRepository, ProductionOrderEntity
    ├── kafka/               # ProductionEventPublisher
    └── config/              # ProductionServiceConfig
```

---

## Module Structure

### Production Module

Owns production orders, work-centre definitions, operation sequences, and scheduling. Exposes the canonical `ProductionOrder` aggregate and publishes domain events consumed by OEE, material, and integration modules.

### Quality Module

Manages inspection plans, in-process quality checks, SPC charts (X-bar/R, p-chart, c-chart), control limits, and non-conformance reports (NCR). Receives `OperationCompletedEvent` to trigger mandatory inspection steps.

### Material Module

Tracks raw material lots, work-in-progress (WIP) locations, finished goods, and component consumption per production order. Integrates with SAP WM/EWM for goods movements and maintains full lot genealogy.

### Integration Module

Houses all external system adapters: SAP RFC/IDoc, SCADA OPC-UA bridge, MQTT ingest, and Modbus relay. Uses the Adapter pattern to decouple external protocol specifics from core domain logic.

### Analytics Module

Reads from read-replica databases and TimescaleDB continuous aggregates to serve historical OEE trends, SPC analysis, first-pass yield, and production summary reports. Stateless and horizontally scalable.

---

## Key Code Components

```mermaid
classDiagram
    class ProductionOrder {
        -String id
        -String sapOrderNumber
        -OrderStatus status
        -WorkCenterId workCenterId
        -List~Operation~ operations
        -BillOfMaterials bom
        -Instant plannedStart
        -Instant plannedEnd
        +release() void
        +start() void
        +complete(BigDecimal actualQty) void
        +validate() void
        +addOperation(Operation op) void
    }

    class Operation {
        -String id
        -int sequenceNumber
        -String description
        -Duration standardTime
        -OperationStatus status
        +start(String operatorId) void
        +complete(BigDecimal yield, BigDecimal scrap) void
    }

    class WorkCenter {
        -String id
        -String name
        -WorkCenterType type
        -int capacity
        -ShiftCalendar shiftCalendar
        +isAvailable(Instant start, Duration duration) boolean
        +getOeeForShift(LocalDate date, Shift shift) OeeResult
    }

    class BillOfMaterials {
        -String itemNumber
        -List~BomComponent~ components
        +getRequiredQuantity(String materialId) BigDecimal
    }

    ProductionOrder "1" *-- "many" Operation : contains
    ProductionOrder "many" --> "1" WorkCenter : assigned to
    ProductionOrder "1" *-- "1" BillOfMaterials : uses
```

---

## Production Service Code Diagram

```mermaid
classDiagram
    direction TB

    class ProductionOrderController {
        -ProductionOrderApplicationService appService
        +createOrder(CreateOrderRequest) ResponseEntity
        +releaseOrder(String id) ResponseEntity
        +startOrder(String id) ResponseEntity
        +completeOrder(String id, CompleteOrderRequest) ResponseEntity
        +getOrder(String id) ResponseEntity
        +listOrders(OrderFilter, Pageable) ResponseEntity
    }

    class ProductionOrderApplicationService {
        -ProductionOrderRepository repository
        -WorkCenterService workCenterService
        -MaterialReservationService materialService
        -ApplicationEventPublisher eventPublisher
        +createOrder(CreateOrderCommand) ProductionOrder
        +releaseOrder(String id) ProductionOrder
        +startOrder(String id) ProductionOrder
        +completeOrder(String id, BigDecimal qty) ProductionOrder
    }

    class ProductionOrderRepository {
        <<interface>>
        +findById(String id) Optional~ProductionOrder~
        +save(ProductionOrder order) ProductionOrder
        +findByWorkCenterAndDateRange(String wc, Instant from, Instant to) List
        +findByStatus(OrderStatus status, Pageable p) Page~ProductionOrder~
    }

    class JpaProductionOrderRepository {
        +findById(String id) Optional~ProductionOrder~
        +save(ProductionOrder order) ProductionOrder
    }

    class ProductionEventPublisher {
        -KafkaTemplate kafkaTemplate
        +publishOrderReleased(ProductionOrderReleasedEvent e) void
        +publishOrderCompleted(ProductionOrderCompletedEvent e) void
        +publishOperationCompleted(OperationCompletedEvent e) void
    }

    class OeeCalculator {
        +calculate(OeeInput input) OeeResult
        -safeDivide(double n, double d) double
    }

    class CapacityChecker {
        -WorkCenterRepository wcRepo
        +checkCapacity(String workCenterId, Instant start) void
    }

    ProductionOrderController --> ProductionOrderApplicationService : delegates
    ProductionOrderApplicationService --> ProductionOrderRepository : reads/writes
    ProductionOrderApplicationService --> OeeCalculator : uses
    ProductionOrderApplicationService --> CapacityChecker : uses
    ProductionOrderApplicationService --> ProductionEventPublisher : publishes events
    JpaProductionOrderRepository ..|> ProductionOrderRepository : implements
```

**State Machine — Production Order Lifecycle**

```mermaid
flowchart LR
    CREATED -->|releaseOrder| RELEASED
    RELEASED -->|startOrder| IN_PROGRESS
    IN_PROGRESS -->|completeOrder| COMPLETED
    IN_PROGRESS -->|holdOrder| ON_HOLD
    ON_HOLD -->|resumeOrder| IN_PROGRESS
    RELEASED -->|cancelOrder| CANCELLED
    IN_PROGRESS -->|cancelOrder| CANCELLED
```

---

## Quality Service Code Diagram

```mermaid
classDiagram
    direction TB

    class InspectionPlan {
        -String id
        -String itemNumber
        -String revision
        -List~InspectionCharacteristic~ characteristics
        -SamplingProcedure samplingProcedure
        +getApplicableCharacteristics(String operationId) List
        +isComplete() boolean
    }

    class InspectionCharacteristic {
        -String id
        -String name
        -CharacteristicType type
        -ControlLimits controlLimits
        -boolean isCritical
        +evaluate(BigDecimal measuredValue) CharacteristicResult
    }

    class SpcChart {
        -String characteristicId
        -ChartType chartType
        -List~DataPoint~ dataPoints
        -ControlLimits controlLimits
        +addSample(SpcSample sample) void
        +detectViolations() List~ControlRuleViolation~
        +recalculateControlLimits() ControlLimits
    }

    class ControlLimits {
        -BigDecimal ucl
        -BigDecimal lcl
        -BigDecimal centerLine
        -BigDecimal usl
        -BigDecimal lsl
        +isWithinControlLimits(BigDecimal value) boolean
        +isWithinSpecLimits(BigDecimal value) boolean
    }

    class NonConformanceReport {
        -String id
        -String productionOrderId
        -String characteristicId
        -NcrStatus status
        -DispositionType disposition
        -String rootCause
        +dispositionAs(DispositionType d, String justification) void
        +escalate(String supervisorId) void
    }

    class SpcService {
        -SpcChartRepository chartRepo
        -NcrRepository ncrRepo
        -ApplicationEventPublisher publisher
        +recordMeasurement(String charId, SpcSample sample) void
        +detectAndRaiseAlarms(SpcChart chart) void
    }

    class WesternElectricRules {
        <<Strategy>>
        +evaluate(List~DataPoint~ points, ControlLimits limits) List~Violation~
    }

    class NelsonRules {
        <<Strategy>>
        +evaluate(List~DataPoint~ points, ControlLimits limits) List~Violation~
    }

    class ControlRuleStrategy {
        <<interface>>
        +evaluate(List~DataPoint~ points, ControlLimits limits) List~Violation~
    }

    InspectionPlan "1" *-- "many" InspectionCharacteristic : contains
    InspectionCharacteristic "1" *-- "1" ControlLimits : bounded by
    SpcChart --> ControlLimits : uses
    SpcService --> SpcChart : manages
    SpcService --> NonConformanceReport : raises
    WesternElectricRules ..|> ControlRuleStrategy : implements
    NelsonRules ..|> ControlRuleStrategy : implements
    SpcService --> ControlRuleStrategy : applies
```

---

## Integration Adapter Code Diagram

```mermaid
classDiagram
    direction TB

    class ExternalSystemPort {
        <<interface>>
        +sendProductionConfirmation(ConfirmationPayload p) void
        +fetchProductionOrders(String plant, LocalDate date) List~ExternalOrder~
        +sendGoodsMovement(GoodsMovementPayload p) void
    }

    class SapRfcAdapter {
        -JCoDestination sapDestination
        -CircuitBreaker circuitBreaker
        -OutboxRepository outboxRepo
        +sendProductionConfirmation(ConfirmationPayload p) void
        +fetchProductionOrders(String plant, LocalDate date) List~ExternalOrder~
        +sendGoodsMovement(GoodsMovementPayload p) void
        -checkBapiReturn(JCoTable returnTable) void
        -fallback(ConfirmationPayload p, Exception ex) void
    }

    class OpcUaAdapter {
        -OpcUaClient client
        -TagConfigRepository tagConfigRepo
        -KafkaProducer kafkaProducer
        +connect(String endpointUrl) void
        +subscribe(List~String~ nodeIds) void
        +onTagChange(UaMonitoredItem item, DataValue value) void
        -normalise(String nodeId, DataValue v) TelemetryPayload
    }

    class MqttIngestAdapter {
        -MqttClient mqttClient
        -KafkaProducer kafkaProducer
        -SchemaValidator validator
        +start() void
        +onMessage(String topic, byte[] payload) void
        -routeToKafkaTopic(String mqttTopic) String
    }

    class ModbusAdapter {
        -ModbusTcpMaster master
        -PollingScheduler scheduler
        +readHoldingRegisters(int addr, int count) int[]
        +pollAndPublish() void
    }

    class IntegrationOutboxRelay {
        -OutboxRepository outboxRepo
        -ExternalSystemPort sapPort
        -KafkaProducer kafkaProducer
        +processOutbox() void
    }

    class SchemaValidator {
        -JsonSchemaFactory factory
        +validate(String schemaId, JsonNode payload) ValidationResult
    }

    SapRfcAdapter ..|> ExternalSystemPort : implements
    IntegrationOutboxRelay --> ExternalSystemPort : uses
    MqttIngestAdapter --> SchemaValidator : validates payloads
    OpcUaAdapter --> KafkaProducer : forwards telemetry
    MqttIngestAdapter --> KafkaProducer : forwards telemetry
```

**Integration Data Flow**

```mermaid
flowchart LR
    subgraph OT["OT Layer"]
        PLC["PLC / Machine"]
        SCADA["SCADA System"]
        SAP_ERP["SAP ERP"]
    end

    subgraph Edge["Edge / DMZ"]
        OpcUA["OPC-UA Collector"]
        MqttB["MQTT Bridge"]
        ModbusC["Modbus Collector"]
    end

    subgraph Core["MES Core"]
        Kafka["Apache Kafka"]
        IntSvc["Integration Service"]
        ProdSvc["Production Service"]
        Outbox["Outbox Relay"]
    end

    PLC -->|OPC-UA| OpcUA
    PLC -->|Modbus TCP| ModbusC
    SCADA -->|MQTT| MqttB
    OpcUA -->|mes.telemetry.raw| Kafka
    MqttB -->|mes.telemetry.raw| Kafka
    ModbusC -->|mes.telemetry.raw| Kafka
    Kafka -->|consume| IntSvc
    ProdSvc -->|domain events| Kafka
    Outbox -->|SAP RFC/IDoc| SAP_ERP
    SAP_ERP -->|production orders inbound| IntSvc
```

---

## Design Patterns Used

| Pattern | Applied In | Purpose |
|---|---|---|
| Repository | All domain modules | Decouple domain from persistence technology |
| Factory | `SpcChartFactory`, `OrderFactory` | Centralise creation logic for variant types |
| Strategy | `ControlRuleStrategy` (Western Electric, Nelson) | Pluggable SPC rule evaluation |
| Observer / Events | Spring `ApplicationEventPublisher` | Decoupled intra-service side effects |
| Adapter | `SapRfcAdapter`, `OpcUaAdapter`, `MqttIngestAdapter` | Insulate domain from external protocols |
| Outbox | `IntegrationOutboxRelay` | Guaranteed at-least-once delivery to external systems |
| Circuit Breaker | Resilience4j on all external calls | Fault tolerance for SAP, SCADA connections |
| CQRS (light) | Analytics service reads from read replicas | Separate command/query scalability |

---

## Code Dependencies

```mermaid
flowchart TD
    GW["api-gateway"]
    PS["production-service"]
    QS["quality-service"]
    MS["material-service"]
    OEE["oee-service"]
    IS["integration-service"]
    AS["analytics-service"]
    NS["notification-service"]
    CORE["mes-domain-core (shared lib)"]
    SEC["mes-security (shared lib)"]
    KAFKA["Apache Kafka"]
    TSDB["TimescaleDB"]
    PG["PostgreSQL"]
    REDIS["Redis"]

    GW --> PS
    GW --> QS
    GW --> MS
    GW --> OEE
    GW --> AS

    PS --> CORE
    QS --> CORE
    MS --> CORE
    OEE --> CORE
    IS --> CORE

    PS --> SEC
    QS --> SEC
    MS --> SEC

    PS -->|domain events| KAFKA
    QS -->|consumes OperationCompleted| KAFKA
    MS -->|consumes OrderReleased| KAFKA
    OEE -->|consumes telemetry| KAFKA
    IS -->|consumes all events| KAFKA
    NS -->|consumes alarm events| KAFKA

    OEE --> TSDB
    AS --> TSDB
    PS --> PG
    QS --> PG
    MS --> PG
    IS --> PG

    PS --> REDIS
    OEE --> REDIS
```

**Dependency Rules**

| Rule | Rationale |
|---|---|
| `domain` must not import `infrastructure` | Domain logic stays pure and testable without Spring |
| `application` imports `domain` interfaces only | Application services are decoupled from JPA entities |
| Services do not call each other synchronously | Inter-service communication via Kafka events only |
| `shared-libs` contain no Spring Boot auto-configuration | Shared libraries are framework-agnostic utilities |
| Edge agents do not import Java services | Edge layer is fully independent Node.js workspace |
