# Sequence Diagrams — Manufacturing Execution System

## Overview

This document details the interaction sequences for the Manufacturing Execution System's most critical workflows. Each diagram models the message flow between actors and services for a specific use case using UML sequence diagram notation rendered via Mermaid.

Participants across diagrams include the operator-facing UI, API Gateway (handles JWT authentication and request routing), and five backend microservices — Production Service, Quality Service, Material Service, and Integration Service. External systems include ERP (SAP), SCADA (OPC-UA server), IoT Hub (device management layer), Kafka (event streaming backbone), and Database (PostgreSQL with logical per-service schemas).

All service-to-service calls are synchronous REST unless explicitly marked as Kafka publish/subscribe. JWT tokens are propagated through the API Gateway; downstream services validate claims using a shared public key ring. All database mutations are wrapped in explicit transactions where data consistency requires it.

---

## Production Order Release Sequence

When the Integration Service receives a new production order pushed from SAP via IDoc/RFC webhook, it validates the payload, maps it to the MES domain model, invokes the Production Service to persist and decompose the order into work orders, and emits domain events that trigger downstream material availability checks.

```mermaid
sequenceDiagram
    autonumber
    participant SAP as ERP (SAP)
    participant IntSvc as Integration Service
    participant Kafka
    participant ProdSvc as Production Service
    participant MatSvc as Material Service
    participant DB as Database
    participant UI as Operator UI

    SAP->>IntSvc: POST /webhook/production-orders (IDoc PPORD01 payload)
    IntSvc->>IntSvc: validate payload schema and plant code
    IntSvc->>DB: INSERT erp_sync_logs (direction=INBOUND, status=RECEIVED)
    IntSvc->>ProdSvc: POST /api/production-orders (mapped order DTO)
    ProdSvc->>DB: SELECT routings WHERE id = order.routingId AND isActive = true
    DB-->>ProdSvc: routing header + routing steps
    ProdSvc->>DB: SELECT bom WHERE id = order.bomId AND isValidFor(plannedStartDate)
    DB-->>ProdSvc: BOM header + BOM lines
    ProdSvc->>ProdSvc: validate routing effectivity and BOM revision
    ProdSvc->>DB: INSERT production_orders (status=CREATED)
    ProdSvc->>DB: INSERT work_orders for each routing step (status=PENDING)
    ProdSvc-->>IntSvc: 201 Created { orderId, workOrderIds[] }
    IntSvc->>DB: UPDATE erp_sync_logs SET status=SUCCESS, mesEntityId=orderId
    IntSvc->>Kafka: publish mes.production-orders.created { orderId, productCode, plant }
    Kafka-->>MatSvc: consume mes.production-orders.created
    MatSvc->>DB: SELECT material_lots WHERE materialCode IN (BOM components) AND qualityStatus=APPROVED
    MatSvc->>MatSvc: evaluate availability against BOM requirements (FEFO)
    MatSvc->>Kafka: publish mes.materials.availability-checked { orderId, allAvailable, shortages[] }
    Kafka-->>ProdSvc: consume mes.materials.availability-checked
    ProdSvc->>DB: UPDATE production_orders SET status=READY WHERE allAvailable=true
    ProdSvc->>DB: UPDATE production_orders SET status=MATERIAL_SHORTAGE WHERE allAvailable=false
    ProdSvc->>Kafka: publish mes.production-orders.released { orderId, scheduledStart }
    Kafka-->>UI: SSE push — new production order available on board
    UI->>UI: render order card on production scheduling board
```

---

## Operation Execution Sequence

The operator scans a work order barcode to begin a specific operation. The system verifies machine availability, employee authorization against required certifications, and material readiness before activating the operation. The current recipe is streamed to the PLC via the SCADA adapter, and a domain event is emitted for OEE tracking.

```mermaid
sequenceDiagram
    autonumber
    participant UI as Operator UI
    participant GW as API Gateway
    participant ProdSvc as Production Service
    participant MatSvc as Material Service
    participant SCADA
    participant DB as Database
    participant Kafka

    UI->>GW: POST /work-orders/{id}/operations/{opId}/start  (Bearer JWT, body: machineId)
    GW->>GW: validate JWT, extract employeeId and roles
    GW->>ProdSvc: forward request with x-employee-id header
    ProdSvc->>DB: SELECT work_order JOIN routing_step WHERE workOrderId = {id}
    DB-->>ProdSvc: work order details, operation instructions, required certifications
    ProdSvc->>ProdSvc: verify employee holds required certifications for operationCode
    alt Employee not certified
        ProdSvc-->>GW: 403 Forbidden { reason: "Missing certification: WELD-L2" }
        GW-->>UI: 403 Forbidden
    end
    ProdSvc->>DB: SELECT machines WHERE machineId = {machineId} AND status = IDLE
    DB-->>ProdSvc: machine record with scadaNodeId and theoreticalCycleTime
    alt Machine not idle or offline
        ProdSvc-->>GW: 409 Conflict { reason: "Machine currently RUNNING or DOWN" }
        GW-->>UI: 409 Conflict
    end
    ProdSvc->>MatSvc: GET /reservations?workOrderId={id}
    MatSvc->>DB: SELECT material_lots WHERE reservedForWorkOrder = {id}
    DB-->>MatSvc: reserved lot records
    MatSvc-->>ProdSvc: { lotsReady: true, lots: [{ lotId, materialCode, qty }] }
    ProdSvc->>DB: UPDATE operations SET status=IN_PROGRESS, startedAt=NOW(), machineId, operatorId
    ProdSvc->>DB: UPDATE machines SET status=RUNNING, currentOperationId={opId}
    ProdSvc->>SCADA: writeTags({ [scadaNodeId + "/Recipe"]: recipeParams, [scadaNodeId + "/RunCmd"]: true })
    SCADA-->>ProdSvc: { success: true, timestamp }
    ProdSvc->>Kafka: publish mes.operations.started { operationId, machineId, workOrderId, shiftId }
    ProdSvc-->>GW: 200 OK { operationId, startedAt, plannedCycleTimeSecs, recipe }
    GW-->>UI: 200 OK
    UI->>UI: display live operation timer, cycle count, and parameter targets
```

---

## Quality Inspection Sequence

On completing an operation that has a mandatory quality plan, the operator submits inspection readings through the UI. The Quality Service evaluates each reading against spec and control limits, updates the relevant SPC control charts, flags rule violations, and conditionally creates an NCR. Downstream services react to quality outcomes via Kafka events.

```mermaid
sequenceDiagram
    autonumber
    participant UI as Operator UI
    participant GW as API Gateway
    participant QSvc as Quality Service
    participant ProdSvc as Production Service
    participant MatSvc as Material Service
    participant DB as Database
    participant Kafka

    UI->>GW: POST /inspections  (Bearer JWT, body: { workOrderId, operationId, materialLotId, readings[] })
    GW->>QSvc: forward request
    QSvc->>DB: SELECT quality_plans JOIN inspection_characteristics WHERE routingStepId = step.id AND isActive
    DB-->>QSvc: quality plan with characteristics and SPC config
    QSvc->>QSvc: validate that readings count satisfies sample size requirement
    loop for each characteristic reading
        QSvc->>QSvc: compare measuredValue against USL / LSL
        QSvc->>DB: SELECT control_charts WHERE characteristicId AND workCenterId
        DB-->>QSvc: control chart with UCL, LCL, recent subgroup data
        QSvc->>QSvc: apply Western Electric Rules 1-4 and Nelson Rules
        QSvc->>DB: INSERT control_chart_points (value, isViolation, violationType)
    end
    QSvc->>DB: INSERT inspection_results (status=EVALUATING)
    QSvc->>DB: INSERT inspection_readings[] linked to inspectionId
    alt All readings within specification
        QSvc->>DB: UPDATE inspection_results SET overallResult=PASS, disposition=APPROVED
        QSvc->>DB: UPDATE material_lots SET qualityStatus=APPROVED WHERE id = materialLotId
        QSvc->>Kafka: publish mes.quality.inspection-passed { inspectionId, workOrderId, lotId }
        Kafka-->>ProdSvc: consume — mark work order quality check complete, allow downstream routing
    else One or more readings outside specification
        QSvc->>DB: UPDATE inspection_results SET overallResult=FAIL, disposition=ON_HOLD
        QSvc->>DB: INSERT defects[] for each failed characteristic
        QSvc->>DB: UPDATE material_lots SET qualityStatus=ON_HOLD, isQuarantined=true WHERE id = materialLotId
        QSvc->>DB: INSERT nonconformance_reports (status=OPEN, severity based on characteristic.isCritical)
        QSvc->>Kafka: publish mes.quality.ncr-opened { ncrId, severity, workOrderId, lotId }
        Kafka-->>UI: SSE push — quality alert notification with NCR link
        Kafka-->>MatSvc: consume mes.quality.ncr-opened — quarantine affected lot, block reservations
        Kafka-->>ProdSvc: consume mes.quality.ncr-opened — place work order on QUALITY_HOLD
    end
    QSvc-->>GW: 201 Created { inspectionId, overallResult, ncrId? }
    GW-->>UI: 201 Created
    UI->>UI: display pass/fail badge and NCR details if applicable
```

---

## Material Issue Sequence

Before production can start, components defined on the BOM are issued from inventory to the work order. The Material Service selects eligible lots using a FEFO strategy, validates quantity availability, records the movements, and triggers a goods issue confirmation to SAP via the Integration Service.

```mermaid
sequenceDiagram
    autonumber
    participant UI as Operator UI
    participant GW as API Gateway
    participant MatSvc as Material Service
    participant ProdSvc as Production Service
    participant IntSvc as Integration Service
    participant DB as Database
    participant SAP as ERP (SAP)
    participant Kafka

    UI->>GW: POST /work-orders/{id}/material-issues  (Bearer JWT, body: { componentCode, requestedQty })
    GW->>MatSvc: forward request
    MatSvc->>ProdSvc: GET /work-orders/{id}  (validate work order status)
    ProdSvc->>DB: SELECT work_orders WHERE id = {id}
    DB-->>ProdSvc: work order { status, productionOrderId, bomLineId }
    ProdSvc-->>MatSvc: work order OK, bomLine confirmed
    MatSvc->>DB: SELECT material_lots WHERE materialCode = {componentCode} AND qualityStatus = APPROVED AND currentQuantity > 0 ORDER BY expiryDate ASC
    DB-->>MatSvc: eligible lots ranked by FEFO
    MatSvc->>MatSvc: select lots to satisfy requestedQty (split across lots if needed)
    MatSvc->>DB: BEGIN TRANSACTION
    MatSvc->>DB: UPDATE material_lots SET currentQuantity = currentQuantity - issuedQty, reservedQuantity = reservedQuantity - reservedQty
    MatSvc->>DB: INSERT material_movements (type=GOODS_ISSUE, workOrderId, lotId, qty, performedBy, performedAt)
    MatSvc->>DB: COMMIT
    MatSvc->>Kafka: publish mes.materials.issued { workOrderId, lotId, materialCode, qty, movementId }
    Kafka-->>IntSvc: consume mes.materials.issued
    IntSvc->>SAP: POST /api/goods-movements  { movementType: "261", materialNumber, plant, qty, batchNumber, storageLocation }
    SAP-->>IntSvc: 200 OK { sapMaterialDocument }
    IntSvc->>DB: UPDATE material_movements SET erpDocumentNumber = sapMaterialDocument
    IntSvc->>DB: UPDATE erp_sync_logs SET status=SUCCESS, erpDocumentNumber
    MatSvc-->>GW: 201 Created { movementId, lotId, issuedQty, remainingLotQty }
    GW-->>UI: 201 Created
    UI->>UI: update component checklist, show lot genealogy link
```

---

## Machine Downtime Reporting Sequence

A downtime event can be initiated automatically from a SCADA alarm or manually reported by an operator. In both cases the system records the event, updates machine and operation state, recalculates shift OEE availability, and notifies the production team. The operator subsequently confirms the root cause category to enable accurate loss analysis.

```mermaid
sequenceDiagram
    autonumber
    participant SCADA
    participant IntSvc as Integration Service
    participant GW as API Gateway
    participant UI as Operator UI
    participant ProdSvc as Production Service
    participant DB as Database
    participant Kafka

    alt SCADA-initiated downtime alarm
        SCADA->>IntSvc: OPC-UA alarm event (machineId, alarmCode, severity, timestamp)
        IntSvc->>IntSvc: map alarm code to MES downtime reason category
        IntSvc->>ProdSvc: POST /machines/{machineId}/downtime-events  { source: SCADA, reasonCode, category }
    else Operator-reported downtime
        UI->>GW: POST /machines/{machineId}/downtime-events  (Bearer JWT, body: { reasonCode, category })
        GW->>ProdSvc: forward request with employeeId
    end
    ProdSvc->>DB: SELECT machines WHERE id = {machineId} AND status = RUNNING
    DB-->>ProdSvc: machine record with currentOperationId
    ProdSvc->>DB: UPDATE machines SET status=DOWN, downtimeStartAt=NOW()
    ProdSvc->>DB: UPDATE operations SET status=PAUSED WHERE id = currentOperationId
    ProdSvc->>DB: INSERT machine_downtime_events (machineId, category, reasonCode, startAt, source)
    ProdSvc->>ProdSvc: recalculate shift OEE availability component
    ProdSvc->>DB: UPDATE oee_snapshots SET availability = uptime / plannedProductionTime
    ProdSvc->>Kafka: publish mes.machines.downtime-started { machineId, category, shiftId, workOrderId }
    Kafka-->>UI: SSE push — machine-down alert banner
    UI->>UI: display downtime modal with category selection and timer
    UI->>GW: PUT /machines/{machineId}/downtime-events/{eventId}  { confirmedCategory, rootCause, comments }
    GW->>ProdSvc: forward category confirmation
    ProdSvc->>DB: UPDATE machine_downtime_events SET confirmedCategory, rootCause, confirmedBy, confirmedAt
    ProdSvc-->>GW: 200 OK { downtimeEventId, duration, oeeImpact }
    GW-->>UI: 200 OK
    UI->>UI: show downtime logged confirmation, update OEE widget
```

---

## ERP Synchronization Sequence

A scheduled job triggers incremental master data synchronization between SAP and the MES. Work center capacities, material master records, and BOM structures are synchronized first. Open production orders are then delta-synced based on the last successful sync timestamp. The integration service emits a completion event that allows dependent services to refresh their caches.

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler
    participant IntSvc as Integration Service
    participant SAP as ERP (SAP)
    participant ProdSvc as Production Service
    participant MatSvc as Material Service
    participant DB as Database
    participant Kafka

    Scheduler->>IntSvc: trigger MasterDataSyncJob { plant: "1000", entities: [WC, MAT, BOM, PO] }
    IntSvc->>DB: INSERT erp_sync_logs (type=MASTER_DATA_SYNC, status=STARTED, triggeredAt)
    IntSvc->>SAP: GET /api/work-centers?plant=1000&changedAfter={lastSyncAt}
    SAP-->>IntSvc: work center records[]
    IntSvc->>DB: UPSERT work_centers ON CONFLICT (work_center_code) DO UPDATE SET name, capacity, updatedAt
    IntSvc->>SAP: GET /api/materials?plant=1000&changedAfter={lastSyncAt}
    SAP-->>IntSvc: material master records[]
    IntSvc->>DB: UPSERT materials ON CONFLICT (erp_material_number) DO UPDATE SET description, uom, shelfLife
    IntSvc->>SAP: GET /api/bom?plant=1000&changedAfter={lastSyncAt}
    SAP-->>IntSvc: BOM header and line records[]
    IntSvc->>DB: UPSERT bom, bom_lines ON CONFLICT DO UPDATE (apply effectivity date logic)
    IntSvc->>SAP: GET /api/production-orders?plant=1000&status=REL&changedAfter={lastSyncAt}
    SAP-->>IntSvc: open and changed production order records[]
    loop for each production order record
        IntSvc->>ProdSvc: POST /api/production-orders/sync  { erpOrder }
        ProdSvc->>DB: UPSERT production_orders, work_orders ON CONFLICT
        ProdSvc-->>IntSvc: { mesOrderId, action: CREATED | UPDATED | UNCHANGED }
    end
    IntSvc->>DB: UPDATE erp_sync_logs SET status=SUCCESS, syncedAt=NOW(), recordCounts
    IntSvc->>Kafka: publish mes.erp.sync-complete { plant, entityCounts, durationMs }
    Kafka-->>ProdSvc: consume — invalidate scheduling board cache, reload open orders
    Kafka-->>MatSvc: consume — invalidate material availability cache for plant
```

---

## IoT Data Ingestion Sequence

Telemetry streams arrive from IoT-enabled machines at high frequency (up to 1 Hz per device). The IoT Hub validates device registration and routes messages to Kafka. A stream processor enriches each reading with work order context, applies anomaly detection, computes rolling aggregates for OEE performance calculations, and persists results to the time-series database partition. Anomalies trigger real-time alerts to the operator UI.

```mermaid
sequenceDiagram
    autonumber
    participant Device as IoT Device
    participant Hub as IoT Hub
    participant Kafka
    participant StreamProc as Stream Processor
    participant ProdSvc as Production Service
    participant DB as Database
    participant UI as Operator UI

    Device->>Hub: MQTT publish  topic: devices/{deviceId}/messages/events  { tagName, value, unit, ts }
    Hub->>Hub: authenticate device certificate, validate registration status
    Hub->>Hub: apply message routing rules — route by deviceType
    Hub->>Kafka: produce to mes.telemetry.raw (partitionKey=machineId, payload=enriched message)
    Kafka-->>StreamProc: consume mes.telemetry.raw (micro-batch, 500ms window)
    StreamProc->>ProdSvc: GET /machines/{machineId}/active-context  (L1 cache, TTL 30s)
    ProdSvc->>DB: SELECT operations WHERE machineId AND status = IN_PROGRESS LIMIT 1
    DB-->>ProdSvc: { operationId, workOrderId, shiftId, plannedCycleTimeSecs }
    ProdSvc-->>StreamProc: enrichment context
    StreamProc->>StreamProc: stamp each reading with workOrderId, shiftId, enrichedAt
    StreamProc->>StreamProc: compute Z-score anomaly detection per tag (sliding window σ)
    StreamProc->>StreamProc: compute 1-minute rolling aggregates: avg, min, max, stddev, count
    StreamProc->>DB: COPY telemetry_readings (batch INSERT, partitioned by device_timestamp month)
    StreamProc->>DB: UPDATE oee_snapshots SET performanceRate = (actualCycles / theoreticalCycles)
    alt Anomaly score exceeds threshold (Z > 3.5)
        StreamProc->>Kafka: produce mes.telemetry.anomaly { deviceId, machineId, tagName, value, zScore }
        Kafka-->>UI: SSE push — anomaly alert { machineId, tagName, severity }
        UI->>UI: highlight affected machine on shop floor map with alert overlay
    end
    StreamProc->>Kafka: produce mes.telemetry.aggregated (1-min summaries for dashboard consumers)
    Kafka-->>UI: SSE push — live KPI metrics refresh (cycle count, temperature trend, vibration)
```
