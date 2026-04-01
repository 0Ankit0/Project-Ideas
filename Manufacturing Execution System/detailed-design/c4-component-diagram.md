# C4 Component Diagram — Manufacturing Execution System

## Overview

This document provides C4 Model Level 3 (Component) diagrams for each microservice in the Manufacturing Execution System. Each diagram decomposes a service container into its internal components — controllers, service classes, repositories, domain models, event publishers, and validators — and shows how those components communicate with one another and with external dependencies.

Diagrams use Mermaid flowcharts to approximate C4 Component notation (which Mermaid does not natively support). Shapes and labels follow C4 conventions: components are named boxes with stereotype labels.

---

## Production Services Components

The Production Service handles the full lifecycle of production orders, operations, and work center capacity management.

```mermaid
flowchart TD
    subgraph "Production Order Service"
        direction TB

        subgraph "API Layer"
            POC["ProductionOrderController\n[REST Controller]\nHandles HTTP requests for\nproduction order CRUD and\nlifecycle transitions"]
            OPC["OperationController\n[REST Controller]\nHandles operation start/complete\nand execution queries"]
        end

        subgraph "Application Layer"
            POS["ProductionOrderService\n[Service]\nOrchestrates order creation,\nvalidation, and state machine\ntransitions"]
            OPS["OperationExecutionService\n[Service]\nManages operation start/complete,\ncalculates duration and yield"]
            SCS["ScheduleCoordinatorService\n[Service]\nCoordinates with Scheduling Svc\nfor capacity validation on release"]
        end

        subgraph "Domain Layer"
            POD["ProductionOrder\n[Domain Model]\nid, externalOrderId, productCode,\nplannedQty, status, routing"]
            OED["OperationExecution\n[Domain Model]\noperationId, workCenterId,\nstart/end times, qty, scrap"]
            SM["OrderStateMachine\n[Domain Service]\nEnforces valid lifecycle\ntransitions"]
        end

        subgraph "Infrastructure Layer"
            POR["ProductionOrderRepository\n[Repository]\nPostgreSQL CRUD for orders"]
            OER["OperationExecutionRepository\n[Repository]\nPostgreSQL CRUD for executions"]
            POV["ProductionOrderValidator\n[Validator]\nValidates routing, work center,\ndate range on creation"]
            PEP["ProductionOrderEventPublisher\n[Event Publisher]\nPublishes to Kafka topic\nproduction-order-events"]
        end
    end

    %% External dependencies
    WC_SVC["Work Center Service\n[External]"]
    KAFKA["Apache Kafka\n[Message Broker]"]
    PG["PostgreSQL\n[Database]"]

    POC --> POS
    OPC --> OPS
    POS --> SM
    POS --> POV
    POS --> POR
    POS --> PEP
    POS --> SCS
    OPS --> OER
    OPS --> PEP
    SM --> POD
    OPS --> OED
    SCS -->|capacity check REST| WC_SVC
    POR --> PG
    OER --> PG
    PEP --> KAFKA
```

### Production Service Component Responsibilities

| Component                       | Type             | Responsibility                                                                    |
|---------------------------------|------------------|-----------------------------------------------------------------------------------|
| `ProductionOrderController`     | REST Controller  | Deserialises HTTP requests, delegates to service, serialises responses            |
| `OperationController`           | REST Controller  | Handles operation start/complete/query endpoints                                  |
| `ProductionOrderService`        | Service          | Coordinates order creation, validation, and state transitions                     |
| `OperationExecutionService`     | Service          | Records operation actuals, computes yield and duration                            |
| `ScheduleCoordinatorService`    | Service          | Calls Work Center Service to validate capacity before releasing orders            |
| `ProductionOrder`               | Domain Model     | Core aggregate root; owns order status and routing reference                      |
| `OperationExecution`            | Domain Model     | Represents a single routing step execution instance                               |
| `OrderStateMachine`             | Domain Service   | Enforces the finite state machine for valid order status transitions              |
| `ProductionOrderRepository`     | Repository       | PostgreSQL persistence for production orders                                      |
| `OperationExecutionRepository`  | Repository       | PostgreSQL persistence for operation execution records                            |
| `ProductionOrderValidator`      | Validator        | Cross-field validation: routing exists, dates valid, work center registered       |
| `ProductionOrderEventPublisher` | Event Publisher  | Publishes `OrderCreated`, `OrderReleased`, `OrderCompleted` events to Kafka       |

---

## Quality Service Components

The Quality Service manages inspection plans, SPC calculations, NCR workflows, and quality disposition.

```mermaid
flowchart TD
    subgraph "Quality Management Service"
        direction TB

        subgraph "API Layer"
            IC["InspectionController\n[REST Controller]\nAccepts inspection submissions\nand result queries"]
            NCRC["NcrController\n[REST Controller]\nHandles NCR creation, update\nand disposition workflow"]
            SPCC["SpcController\n[REST Controller]\nServes control chart data\nand Cpk metrics"]
        end

        subgraph "Application Layer"
            IS["InspectionService\n[Service]\nOrchestrates measurement recording,\ntriggers SPC calculation"]
            NCRS["NcrWorkflowService\n[Service]\nManages NCR lifecycle:\nOPEN, UNDER_REVIEW, CLOSED"]
            SPCS["SpcCalculationService\n[Service]\nComputes X-bar, R-chart limits,\nCpk, and out-of-control rules"]
        end

        subgraph "Domain Layer"
            INSP["Inspection\n[Domain Model]\ninspectionPlanId, lotId,\nmeasurements, status"]
            NCR_D["NonConformanceReport\n[Domain Model]\ndefectCode, severity,\ndisposition, resolution"]
            CC["ControlChart\n[Domain Model]\ncharacteristicId, UCL, LCL,\ncentreLine, dataPoints"]
        end

        subgraph "Infrastructure Layer"
            IR["InspectionRepository\n[Repository]\nPostgreSQL storage for\ninspections and results"]
            NCRR["NcrRepository\n[Repository]\nPostgreSQL storage for NCRs"]
            SPCR["SpcDataRepository\n[Repository]\nPostgreSQL storage for\ncontrol chart data points"]
            IV["InspectionValidator\n[Validator]\nValidates plan ID, lot status,\nsample size constraints"]
            QEP["QualityEventPublisher\n[Event Publisher]\nPublishes to Kafka topic\nquality-events"]
        end
    end

    PO_SVC["Production Order Service\n[External]"]
    MAT_SVC["Material Service\n[External]"]
    NOTIF_SVC["Notification Service\n[External]"]
    KAFKA2["Apache Kafka\n[Message Broker]"]
    PG2["PostgreSQL\n[Database]"]

    IC --> IS
    NCRC --> NCRS
    SPCC --> SPCS
    IS --> SPCS
    IS --> IV
    IS --> IR
    IS --> QEP
    NCRS --> NCRR
    NCRS --> QEP
    SPCS --> SPCR
    IS -->|order context REST| PO_SVC
    IS -->|lot status REST| MAT_SVC
    QEP --> KAFKA2
    KAFKA2 -->|alert subscription| NOTIF_SVC
    IR --> PG2
    NCRR --> PG2
    SPCR --> PG2
```

---

## Integration Service Components

The Integration Service manages bi-directional data exchange with SAP S/4HANA and provides an IoT telemetry ingestion pipeline.

```mermaid
flowchart TD
    subgraph "ERP Integration Service"
        direction TB

        subgraph "Inbound Pipeline"
            IBC["InboundController\n[REST Controller]\nReceives SAP order payloads\nvia HTTP webhook"]
            IMC["InboundMessageConsumer\n[Kafka Consumer]\nConsumes erp-inbound-events\nfrom Kafka"]
            OTF["OrderTransformService\n[Service]\nMaps SAP BAPI/OData structures\nto MES domain objects"]
        end

        subgraph "Outbound Pipeline"
            COS["ConfirmationOutboundService\n[Service]\nBuilds SAP confirmation payloads\nfrom completed MES orders"]
            OMC["OutboundMessageConsumer\n[Kafka Consumer]\nConsumes production-order-events\nfor completed orders"]
            SRC["SapRfcClient\n[Infrastructure]\nExecutes SAP RFC/BAPI calls\nvia SAP JCo connector"]
        end

        subgraph "Shared"
            SYS["SyncStatusService\n[Service]\nTracks last sync time,\nerror queue depth"]
            EQ["ErrorQueue\n[Infrastructure]\nPostgreSQL dead-letter queue\nfor failed SAP calls"]
            ERPV["ErpPayloadValidator\n[Validator]\nValidates mandatory SAP\nfields before transform"]
        end
    end

    SAP["SAP S/4HANA\n[External ERP]"]
    MES_PO["Production Order Service\n[Internal]"]
    KAFKA3["Apache Kafka\n[Message Broker]"]

    IBC --> OTF
    IMC --> OTF
    OTF --> ERPV
    OTF -->|create/update order REST| MES_PO
    OMC --> COS
    COS --> SRC
    SRC -->|RFC BAPI_PRODORD_CONFIRM| SAP
    SRC -->|on failure| EQ
    KAFKA3 --> IMC
    KAFKA3 --> OMC
    MES_PO -->|events| KAFKA3
    SAP -->|OData push| IBC
```

```mermaid
flowchart TD
    subgraph "IoT Telemetry Service"
        direction TB

        subgraph "Ingestion"
            TC["TelemetryController\n[REST Controller]\nHTTP fallback ingest endpoint\nfor edge gateways"]
            TKC["TelemetryKafkaConsumer\n[Kafka Consumer]\nConsumes raw telemetry from\nedge-telemetry-raw topic"]
        end

        subgraph "Processing"
            TV["TelemetryValidator\n[Validator]\nValidates asset ID, tag names,\nquality flags, timestamp bounds"]
            TE["TelemetryEnricher\n[Service]\nJoins telemetry with asset\nmetadata from Asset Registry"]
            TAS["TelemetryAggregator\n[Service]\nComputes time-windowed aggregates\n(avg, min, max) per resolution"]
        end

        subgraph "Storage and Streaming"
            TR["TelemetryRepository\n[Repository]\nWrites processed readings\nto TimescaleDB hypertable"]
            WS["TelemetryWebSocketHandler\n[WebSocket Handler]\nStreams live readings\nto subscribed clients"]
            TEP["TelemetryEventPublisher\n[Event Publisher]\nPublishes telemetry-processed\nevents to Kafka"]
        end
    end

    EDGE["Edge IoT Gateway\n[External]"]
    ASSET_REG["Asset Registry\n[Internal]"]
    TSDB["TimescaleDB\n[Time-Series DB]"]
    KAFKA4["Apache Kafka\n[Message Broker]"]
    OEE_SVC["OEE Analytics Service\n[Internal]"]

    EDGE -->|MQTT via Kafka| KAFKA4
    EDGE -->|HTTP fallback| TC
    TC --> TV
    KAFKA4 --> TKC
    TKC --> TV
    TV --> TE
    TE -->|asset lookup REST| ASSET_REG
    TE --> TAS
    TAS --> TR
    TR --> TSDB
    TE --> TEP
    TE --> WS
    TEP --> KAFKA4
    KAFKA4 -->|telemetry-processed| OEE_SVC
```

---

## Analytics Service Components

The OEE Analytics Service consumes telemetry and production actuals to compute and publish OEE metrics.

```mermaid
flowchart TD
    subgraph "OEE Analytics Service"
        direction TB

        subgraph "API Layer"
            OEEC["OeeController\n[REST Controller]\nServes OEE metrics,\ntrends, and loss Pareto"]
        end

        subgraph "Consumers"
            TELKC["TelemetryConsumer\n[Kafka Consumer]\nConsumes telemetry-processed\nevents for machine state"]
            POKC["ProductionOrderConsumer\n[Kafka Consumer]\nConsumes order events for\nplanned vs actual quantities"]
            QKC["QualityConsumer\n[Kafka Consumer]\nConsumes quality-events\nfor defect counts"]
        end

        subgraph "Calculation Engine"
            ACS["AvailabilityCalculator\n[Service]\nComputes uptime ratio from\nmachine state transitions"]
            PCS["PerformanceCalculator\n[Service]\nComputes performance ratio from\ncycle time vs ideal cycle time"]
            QCS["QualityCalculator\n[Service]\nComputes quality ratio from\ngood parts vs total parts"]
            OEES["OeeAggregatorService\n[Service]\nCombines A * P * Q, persists\nper shift and triggers alerts"]
            LA["LossAnalyzer\n[Service]\nCategorises and ranks\ndowntime reason codes"]
        end

        subgraph "Infrastructure"
            OEER["OeeRepository\n[Repository]\nReads and writes OEE results\nto TimescaleDB"]
            RC["RedisCache\n[Cache]\nCaches current-shift OEE\nfor low-latency API reads"]
            OEEP["OeeEventPublisher\n[Event Publisher]\nPublishes oee-calculated-events\nfor alerting and dashboards"]
        end
    end

    TSDB2["TimescaleDB\n[Time-Series DB]"]
    REDIS["Redis\n[Cache]"]
    KAFKA5["Apache Kafka\n[Message Broker]"]
    NOTIF2["Notification Service\n[Internal]"]

    OEEC --> OEER
    OEEC --> RC
    KAFKA5 --> TELKC
    KAFKA5 --> POKC
    KAFKA5 --> QKC
    TELKC --> ACS
    POKC --> PCS
    QKC --> QCS
    ACS --> OEES
    PCS --> OEES
    QCS --> OEES
    OEES --> LA
    OEES --> OEER
    OEES --> RC
    OEES --> OEEP
    OEEP --> KAFKA5
    KAFKA5 -->|oee-calculated-events| NOTIF2
    OEER --> TSDB2
    RC --> REDIS
```

---

## Cross-Cutting Components

Cross-cutting components are shared across all microservices and deployed as shared libraries or infrastructure services.

### Auth and Security Components

```mermaid
flowchart LR
    subgraph "Kong API Gateway"
        JWV["JwtVerificationPlugin\n[Kong Plugin]\nVerifies RS256 Bearer\ntokens against Keycloak JWKS"]
        RLP["RateLimitPlugin\n[Kong Plugin]\nEnforces per-client\nrequest rate limits"]
        LOG["RequestLoggingPlugin\n[Kong Plugin]\nStructured request/response\nlogging to Elasticsearch"]
        CORS["CorsPlugin\n[Kong Plugin]\nEnforces CORS policy\nfor browser clients"]
    end

    subgraph "Shared Libraries (Java)"
        SEC["mes-security-starter\n[Spring Boot Starter]\nJWT scope enforcement,\nmethod-level @PreAuthorize"]
        AUD["mes-audit-starter\n[Spring Boot Starter]\nAudit trail logging to\ndedicated audit Kafka topic"]
        OBS["mes-observability-starter\n[Spring Boot Starter]\nMicrometer metrics, distributed\ntracing via OpenTelemetry"]
    end

    KC["Keycloak\n[Identity Provider]"]

    JWV -->|JWKS endpoint| KC
    RLP --> JWV
    LOG --> JWV
```

### Observability Components

| Component                 | Technology                     | Responsibility                                                   |
|---------------------------|--------------------------------|------------------------------------------------------------------|
| Distributed Tracing       | OpenTelemetry + Jaeger         | End-to-end trace propagation across microservices via W3C headers|
| Metrics Collection        | Micrometer + Prometheus        | JVM, HTTP, Kafka consumer lag, custom business metrics           |
| Log Aggregation           | Fluentd + Elasticsearch        | Structured JSON logs with `traceId`, `spanId`, service name      |
| Alerting                  | Grafana Alertmanager           | Threshold alerts for OEE, error rates, Kafka consumer lag        |
| Dashboards                | Grafana                        | OEE trends, API latency, queue depths, service health            |

---

## Component Communication Patterns

```mermaid
flowchart TD
    subgraph "Synchronous REST (request-response)"
        A["Scheduling Service"] -->|"GET capacity (< 200ms SLA)"| B["Work Center Service"]
        C["Quality Service"] -->|"GET lot status (< 200ms SLA)"| D["Material Service"]
        E["ERP Integration Service"] -->|"POST order (< 500ms SLA)"| F["Production Order Service"]
    end

    subgraph "Asynchronous Kafka (event-driven)"
        G["Production Order Service"] -->|"OrderCompleted event"| H["Kafka: production-order-events"]
        H --> I["ERP Integration Service\n(outbound confirmation)"]
        H --> J["OEE Analytics Service\n(actual qty update)"]
        K["IoT Telemetry Service"] -->|"TelemetryProcessed event"| L["Kafka: telemetry-processed"]
        L --> M["OEE Analytics Service\n(machine state)"]
        N["Quality Service"] -->|"InspectionFailed event"| O["Kafka: quality-events"]
        O --> P["Notification Service\n(alert dispatch)"]
    end

    subgraph "WebSocket (server push)"
        Q["IoT Telemetry Service"] -->|"Live tag readings (1-sec)"| R["Andon Board Frontend"]
        S["OEE Analytics Service"] -->|"Shift OEE updates (30-sec)"| T["OEE Dashboard Frontend"]
    end
```

### Pattern Selection Rationale

| Communication Pattern | When Used                                                             | Guarantees                              |
|-----------------------|-----------------------------------------------------------------------|-----------------------------------------|
| Synchronous REST      | Strong consistency needed; caller requires immediate response         | At-most-once; circuit-breaker protected |
| Asynchronous Kafka    | Decoupled propagation; high-throughput events; multi-consumer fanout  | At-least-once; consumer offset tracking |
| WebSocket             | Real-time push to browser clients; sub-second latency needed          | Best-effort; reconnect on disconnect    |
| gRPC (future)         | High-frequency internal service calls requiring typed contracts       | At-most-once; streaming support         |

### Resilience Patterns

All synchronous REST calls between microservices are wrapped with:

- **Circuit Breaker** (Resilience4j): Opens after 5 consecutive failures; half-opens after 30 seconds.
- **Retry** (Resilience4j): 3 retries with exponential backoff (100ms → 200ms → 400ms); not applied to non-idempotent `POST` requests.
- **Timeout**: 2,000ms default for intra-service calls; 10,000ms for SAP RFC calls.
- **Bulkhead**: Separate thread pools per downstream service to prevent cascading failures.

Kafka consumers use:

- **Dead Letter Queue**: Failed messages after 3 retries are routed to `<topic>-dlq` for manual inspection.
- **Consumer Group Offset Management**: Committed only after successful processing to ensure at-least-once delivery.
- **Back-pressure**: Consumer concurrency limited per pod; Kubernetes HPA scales consumer pods based on Kafka consumer lag metric.
