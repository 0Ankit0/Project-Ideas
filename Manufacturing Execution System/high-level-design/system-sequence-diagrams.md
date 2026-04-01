# System Sequence Diagrams — Manufacturing Execution System

This document captures the end-to-end message flows for three critical MES processes:
**Production Order Execution**, **Quality Inspection with SPC**, and **IoT Data Ingestion with OEE Calculation**.
Each diagram exposes the full temporal ordering of service calls, events, and async interactions.

---

## 1. Production Order Execution Sequence

### Overview

A Production Order (PO) travels through four distinct lifecycle phases inside MES before it is
confirmed back to SAP ERP:

| Phase | Description |
|---|---|
| **Creation / Import** | Supervisor manually creates or pulls from SAP |
| **Release** | BOM validated, materials reserved, schedule confirmed |
| **Execution** | Operators report against work orders on the shop floor |
| **Completion** | Quality gate passed, ERP confirmation sent |

The sequence below models the complete happy-path flow including the asynchronous event spine
over Kafka and the eventual ERP round-trip.

```mermaid
sequenceDiagram
    autonumber
    actor Supervisor as Production Supervisor
    participant UI as MES Web UI
    participant GW as API Gateway
    participant ProdSvc as ProductionService
    participant SchedSvc as SchedulingService
    participant MatSvc as MaterialService
    participant Kafka as Kafka Event Bus
    participant ERPSync as ERPSyncService
    participant SAP as SAP ERP

    %% ── Phase 1: Order Creation / Import ───────────────────────────────────
    rect rgb(230, 245, 255)
        Note over Supervisor,SAP: Phase 1 — Order Creation / Import
        Supervisor->>UI: Open "New Production Order" wizard
        UI->>GW: POST /api/v1/production-orders (OrderDraftDTO)
        GW->>ProdSvc: createDraft(OrderDraftDTO)
        ProdSvc->>ProdSvc: validate header fields (plant, material, qty, dates)

        alt ERP-originated order
            ProdSvc->>ERPSync: fetchOrderFromSAP(sapOrderNo)
            ERPSync->>SAP: RFC BAPI_PRODORD_GET_DETAIL
            SAP-->>ERPSync: ProdOrderDetail (BOM, routing, dates)
            ERPSync-->>ProdSvc: MappedOrderDTO
        end

        ProdSvc->>ProdSvc: resolveBOM(materialNo, plant, version)
        ProdSvc-->>GW: 201 Created { orderId, status: DRAFT }
        GW-->>UI: OrderCreatedResponse
        UI-->>Supervisor: Show draft order with BOM summary
    end

    %% ── Phase 2: Release ────────────────────────────────────────────────────
    rect rgb(230, 255, 230)
        Note over Supervisor,SAP: Phase 2 — BOM Validation & Order Release
        Supervisor->>UI: Click "Release Order"
        UI->>GW: PATCH /api/v1/production-orders/{id}/release
        GW->>ProdSvc: releaseOrder(orderId)

        ProdSvc->>MatSvc: checkAvailability(bomComponents, requiredDate)
        MatSvc->>MatSvc: query stock levels per storage location
        MatSvc-->>ProdSvc: AvailabilityCheckResult { available: true, shortages: [] }

        ProdSvc->>SchedSvc: scheduleOrder(orderId, routingId, targetDate)
        SchedSvc->>SchedSvc: load work-center capacities
        SchedSvc->>SchedSvc: apply finite scheduling algorithm
        SchedSvc-->>ProdSvc: ScheduleResult { workOrders: [...], startDate, endDate }

        ProdSvc->>MatSvc: reserveMaterials(orderId, bomComponents)
        MatSvc->>MatSvc: create MaterialReservation records
        MatSvc-->>ProdSvc: ReservationConfirmation { reservationId }

        ProdSvc->>ProdSvc: transition status → RELEASED
        ProdSvc->>Kafka: publish ProductionOrderReleased { orderId, workOrders, plant }
        Note right of Kafka: topic: production.orders.events<br/>partition key: orderId

        ERPSync-->>Kafka: consumes ProductionOrderReleased
        ERPSync->>SAP: RFC BAPI_PRODORD_RELEASE (orderId)
        SAP-->>ERPSync: Success + SAP order status updated

        ProdSvc-->>GW: 200 OK { status: RELEASED, workOrderIds: [...] }
        GW-->>UI: OrderReleasedResponse
        UI-->>Supervisor: Display Gantt / work-order list
    end

    %% ── Phase 3: Shop Floor Execution ──────────────────────────────────────
    rect rgb(255, 250, 220)
        Note over Supervisor,SAP: Phase 3 — Operator Execution Reporting
        Note over UI: Operator logs in on shop-floor terminal
        UI->>GW: POST /api/v1/work-orders/{woId}/start (operatorId, actualStart)
        GW->>ProdSvc: startWorkOrder(woId, operatorId)
        ProdSvc->>ProdSvc: transition WO → IN_PROGRESS, record actualStart
        ProdSvc->>Kafka: publish WorkOrderStarted { woId, operatorId, workCenterId }

        Note over UI,ProdSvc: Operator reports material consumption
        UI->>GW: POST /api/v1/work-orders/{woId}/goods-issue (components[])
        GW->>MatSvc: postGoodsIssue(woId, components)
        MatSvc->>MatSvc: deduct from reservation, update stock
        MatSvc->>Kafka: publish MaterialConsumed { woId, components, quantities }

        Note over UI,ProdSvc: Operator reports yield / scrap
        UI->>GW: POST /api/v1/work-orders/{woId}/confirmation (yieldQty, scrapQty)
        GW->>ProdSvc: postConfirmation(woId, yieldQty, scrapQty)
        ProdSvc->>ProdSvc: update actual quantities, calculate variance
        ProdSvc->>Kafka: publish WorkOrderConfirmed { woId, yieldQty, scrapQty }
    end

    %% ── Phase 4: Completion & ERP Sync ─────────────────────────────────────
    rect rgb(255, 230, 230)
        Note over Supervisor,SAP: Phase 4 — Quality Gate & Order Completion
        ProdSvc->>Kafka: publish ProductionOrderReadyForQuality { orderId, yieldQty }
        Note right of Kafka: QualityService consumes this event<br/>and creates inspection lot

        Note over ProdSvc: Await QualityInspectionCompleted event (async)
        Kafka-->>ProdSvc: QualityInspectionCompleted { orderId, disposition: PASS }

        ProdSvc->>ProdSvc: transition status → COMPLETED
        ProdSvc->>Kafka: publish ProductionOrderCompleted { orderId, actualQty, variance }

        ERPSync-->>Kafka: consumes ProductionOrderCompleted
        ERPSync->>SAP: RFC BAPI_PRODORD_COMPLETE (orderId, actualQty)
        SAP-->>ERPSync: GoodsReceiptDocument { grDocNo }
        ERPSync->>ProdSvc: updateERPReference(orderId, grDocNo)

        ProdSvc-->>UI: (WebSocket push) order status = COMPLETED
        UI-->>Supervisor: Show completion summary + ERP GR document
    end
```

### Key Design Decisions

- **Saga Pattern**: The release phase uses an orchestration saga inside `ProductionService`. If
  `MatSvc.reserveMaterials` fails, a compensating `MatSvc.cancelReservation` is issued and the
  order reverts to `DRAFT`.
- **At-least-once delivery**: All Kafka publishes use idempotency keys (`orderId + eventType`).
  Consumers are idempotent to handle duplicate delivery.
- **ERP decoupling**: `ERPSyncService` is the sole adapter for SAP RFC calls. Other services never
  call SAP directly, preserving the anti-corruption layer.

---

## 2. Quality Inspection with SPC Sequence

### Overview

Quality in MES follows the **Inspection Lot** pattern aligned to ISO 2859 / VDA 6.3. Every
production order completion triggers an automatic inspection lot. The SPC Engine evaluates
measurements against **Western Electric Rules (WER)** and raises Out-Of-Control (OOC) alerts
when control limits are violated.

| SPC Signal | Western Electric Rule |
|---|---|
| WER-1 | 1 point beyond 3σ |
| WER-2 | 2 of 3 consecutive beyond 2σ same side |
| WER-3 | 4 of 5 consecutive beyond 1σ same side |
| WER-4 | 8 consecutive points on same side of mean |

```mermaid
sequenceDiagram
    autonumber
    actor Inspector as Quality Inspector
    participant UI as MES UI
    participant QualSvc as QualityService
    participant SPC as SPC Engine
    participant ProdSvc as ProductionService
    participant Kafka as Kafka Event Bus
    participant LIMS as LIMS (External)

    %% ── Trigger ─────────────────────────────────────────────────────────────
    rect rgb(230, 245, 255)
        Note over Inspector,LIMS: Trigger — Inspection Lot Creation
        Kafka-->>QualSvc: consume ProductionOrderReadyForQuality { orderId, materialNo, qty }
        QualSvc->>QualSvc: lookup InspectionPlan for (materialNo, plant)
        QualSvc->>QualSvc: create InspectionLot (lotNo, orderId, sampleSize from AQL table)
        QualSvc->>QualSvc: resolve Inspector via shift assignment
        QualSvc->>Kafka: publish InspectionLotCreated { lotNo, inspectorId, dueTime }
        QualSvc-->>UI: (WebSocket push) new inspection task appears in queue
    end

    %% ── Plan Load ───────────────────────────────────────────────────────────
    rect rgb(230, 255, 230)
        Note over Inspector,LIMS: Plan Load & Assignment
        Inspector->>UI: Open inspection task { lotNo }
        UI->>QualSvc: GET /api/v1/inspection-lots/{lotNo}
        QualSvc->>QualSvc: load InspectionPlan → characteristics, methods, gauges
        QualSvc-->>UI: InspectionLotDetail { characteristics[], samplePlan, instructions }
        UI-->>Inspector: Display measurement form with spec limits per characteristic

        Inspector->>UI: Confirm assignment (acknowledge task)
        UI->>QualSvc: POST /api/v1/inspection-lots/{lotNo}/assign (inspectorId)
        QualSvc->>QualSvc: set assignedTo, set status → IN_PROGRESS
    end

    %% ── Measurement Recording ───────────────────────────────────────────────
    rect rgb(255, 250, 220)
        Note over Inspector,LIMS: Measurement Recording Loop
        loop For each characteristic in inspection plan
            Inspector->>UI: Enter measurement value (manual or gage interface)
            UI->>QualSvc: POST /api/v1/inspection-lots/{lotNo}/measurements
            Note right of UI: { characteristicId, value, unit, gaugeId, timestamp }
            QualSvc->>QualSvc: validate value is numeric, check gauge calibration status
            QualSvc->>QualSvc: persist MeasurementResult

            alt Gauge connected via Bluetooth / USB
                Note over UI: Gauge sends reading automatically via HMI driver
            end
        end
    end

    %% ── SPC Analysis ─────────────────────────────────────────────────────────
    rect rgb(245, 230, 255)
        Note over Inspector,LIMS: SPC Control Chart Analysis
        QualSvc->>SPC: runAnalysis(lotNo, characteristicId, lastN: 25)
        SPC->>SPC: fetch last 25 subgroup means for characteristic
        SPC->>SPC: compute X-bar and R-chart control limits (±3σ)
        SPC->>SPC: plot current measurement on control chart

        SPC->>SPC: evaluate Western Electric Rule WER-1 (beyond 3σ)
        SPC->>SPC: evaluate Western Electric Rule WER-2 (2/3 beyond 2σ)
        SPC->>SPC: evaluate Western Electric Rule WER-3 (4/5 beyond 1σ)
        SPC->>SPC: evaluate Western Electric Rule WER-4 (8 on same side)

        alt Out-Of-Control signal detected
            SPC-->>QualSvc: OOCResult { ruleViolated: WER-1, pointIndex: 23, value: 12.4 }
            QualSvc->>Kafka: publish OOCAlertRaised { lotNo, characteristicId, rule, value, limit }
            QualSvc->>QualSvc: set inspectionLot flag → ALERT
            QualSvc-->>UI: (WebSocket push) OOC alert banner with control chart highlight
            UI-->>Inspector: Display OOC alert — prompt for assignable cause entry
            Inspector->>UI: Enter assignable cause code + corrective action
            UI->>QualSvc: POST /api/v1/ooc-alerts/{alertId}/cause (causeCode, description)
        else All measurements in control
            SPC-->>QualSvc: OOCResult { inControl: true, cpk: 1.45, cp: 1.52 }
            Note over QualSvc: No OOC alert raised, Cpk stored
        end
    end

    %% ── Disposition & Completion ─────────────────────────────────────────────
    rect rgb(255, 230, 230)
        Note over Inspector,LIMS: Lot Disposition & Completion
        QualSvc->>QualSvc: evaluate all characteristics vs spec limits (USL/LSL)
        QualSvc->>QualSvc: count defectives in sample per AQL plan

        alt Sample passes AQL acceptance number
            QualSvc->>QualSvc: dispositionLot → PASS
        else Sample exceeds AQL rejection number
            QualSvc->>QualSvc: dispositionLot → FAIL
            QualSvc->>ProdSvc: blockLot(lotNo, reason: AQL_REJECTION)
        else Reduced / tightened inspection trigger
            QualSvc->>QualSvc: adjust future sampling plan per switching rules
        end

        Inspector->>UI: Click "Complete Inspection"
        UI->>QualSvc: POST /api/v1/inspection-lots/{lotNo}/complete (disposition)
        QualSvc->>QualSvc: set status → COMPLETED, stamp completedAt

        QualSvc->>Kafka: publish QualityInspectionCompleted { lotNo, orderId, disposition, cpk }
        Note right of Kafka: ProductionService awaiting this event

        QualSvc->>LIMS: POST /lims/api/batches (batchRecord payload)
        LIMS-->>QualSvc: 201 Created { limsRef }
        QualSvc->>QualSvc: store limsRef on InspectionLot

        QualSvc-->>UI: 200 OK { lotNo, disposition, limsRef }
        UI-->>Inspector: Inspection complete — show certificate of conformance link
    end
```

### SPC Engine Architecture Note

The `SPC Engine` is deployed as a **sidecar container** within the `QualityService` Kubernetes pod.
It exposes a gRPC interface on `localhost:50051`. This co-location eliminates network round-trips
during real-time measurement entry, keeping p99 latency under 50 ms even with 25-subgroup lookback.

---

## 3. IoT Data Ingestion and OEE Calculation Sequence

### Overview

OEE (Overall Equipment Effectiveness) is the product of three rates:

```
OEE = Availability × Performance × Quality Rate
```

| Metric | Formula | Data Source |
|---|---|---|
| **Availability** | (Planned − Downtime) / Planned | Machine state signals |
| **Performance** | (Actual cycles × Ideal cycle time) / Run time | Encoder / counter signals |
| **Quality Rate** | Good parts / Total parts | Production confirmations |

The sequence below models the journey from a raw PLC signal to a persisted OEE metric published
to downstream BI systems.

```mermaid
sequenceDiagram
    autonumber
    participant PLC as PLC / SCADA
    participant GW as IoT Gateway (OPC-UA)
    participant GG as AWS Greengrass Core
    participant MQTT as MQTT Broker (Mosquitto)
    participant IoTSvc as IoTService
    participant TSDB as TimescaleDB
    participant OEESvc as OEEService
    participant Kafka as Kafka Event Bus

    %% ── Edge Layer: PLC → Greengrass ─────────────────────────────────────────
    rect rgb(230, 245, 255)
        Note over PLC,MQTT: Edge Layer — OT Side (Plant Floor)
        PLC->>GW: OPC-UA subscription notification { nodeId: MachineState, value: RUNNING }
        Note right of PLC: Signal published every 100 ms<br/>or on state change event

        GW->>GW: tag enrichment — add assetId, plantCode, timestamp (ISO 8601 UTC)
        GW->>GG: forward enriched telemetry via local MQTT (QoS 1)
        GG->>GG: Greengrass component: validate schema (Avro schema registry)
        GG->>GG: apply edge filter — suppress duplicate state, debounce 500 ms
        GG->>GG: buffer to local SQLite if cloud connectivity lost

        alt Cloud connectivity available
            GG->>MQTT: publish to aws/mes/plant01/{machineId}/state (QoS 1)
            Note right of GG: Greengrass stream manager batches<br/>messages for bandwidth efficiency
        else Cloud disconnected (edge-resilient mode)
            GG->>GG: persist to local time-series buffer
            Note over GG: Reconnect and replay buffered data<br/>maintaining temporal ordering
        end
    end

    %% ── Cloud Ingestion ──────────────────────────────────────────────────────
    rect rgb(230, 255, 230)
        Note over MQTT,TSDB: Cloud Ingestion Layer
        MQTT-->>IoTSvc: subscribe aws/mes/plant01/+/state (wildcard)
        IoTSvc->>IoTSvc: parse topic segments → extract machineId, plant
        IoTSvc->>IoTSvc: deserialize Avro payload → MachineStateEvent POJO
        IoTSvc->>IoTSvc: validate machineId exists in asset registry
        IoTSvc->>IoTSvc: classify state: RUNNING | IDLE | SETUP | BREAKDOWN | PLANNED_DOWNTIME

        IoTSvc->>TSDB: INSERT INTO machine_state_log (time, machine_id, state, duration_ms)
        Note right of TSDB: TimescaleDB hypertable partitioned by time<br/>7-day chunk interval, 90-day retention policy

        IoTSvc->>TSDB: INSERT INTO machine_counter_log (time, machine_id, counter_type, value)
        Note right of TSDB: Stores cycle counts, speed readings,<br/>encoder pulses per second

        IoTSvc->>Kafka: publish MachineStateChanged { machineId, fromState, toState, timestamp }
        Note right of Kafka: topic: iot.machine.state<br/>partition key: machineId

        alt State transitions to BREAKDOWN
            IoTSvc->>Kafka: publish MachineBreakdownDetected { machineId, timestamp }
            Note over Kafka: MaintenanceService and AlertService consume
        end
    end

    %% ── OEE Calculation ─────────────────────────────────────────────────────
    rect rgb(255, 250, 220)
        Note over OEESvc,Kafka: OEE Calculation Engine
        OEESvc-->>Kafka: consume MachineStateChanged (group: oee-calculator)
        OEESvc->>OEESvc: load current shift definition (start, end, planned breaks)
        OEESvc->>OEESvc: determine planned production time (PPT) for shift

        %% Availability
        OEESvc->>TSDB: query machine_state_log WHERE machine_id=X AND time >= shiftStart
        TSDB-->>OEESvc: StateTimeline { RUNNING: 410min, BREAKDOWN: 25min, IDLE: 5min }
        OEESvc->>OEESvc: availability = (PPT − unplannedDowntime) / PPT
        Note over OEESvc: availability = (440 − 25) / 440 = 94.3%

        %% Performance
        OEESvc->>TSDB: query machine_counter_log WHERE machine_id=X AND time >= shiftStart
        TSDB-->>OEESvc: CycleCountData { totalCycles: 820, idealCycleTimeSec: 28 }
        OEESvc->>OEESvc: performance = (totalCycles × idealCycleTime) / runTime
        Note over OEESvc: performance = (820 × 28) / (415 × 60) = 92.1%

        %% Quality Rate
        OEESvc->>Kafka: fetch last WorkOrderConfirmed events for machine in shift window
        Kafka-->>OEESvc: [{ yieldQty: 805, scrapQty: 15 }]
        OEESvc->>OEESvc: qualityRate = goodParts / totalParts
        Note over OEESvc: quality = 805 / 820 = 98.2%

        %% OEE Score
        OEESvc->>OEESvc: oee = 0.943 × 0.921 × 0.982 = 85.2%
        OEESvc->>TSDB: INSERT INTO oee_metrics (time, machine_id, shift_id, availability, performance, quality, oee)
        Note right of TSDB: Continuous aggregate view refreshes<br/>daily/weekly/monthly rollups automatically

        OEESvc->>Kafka: publish OEECalculationCompleted { machineId, shiftId, oee: 0.852, availability, performance, quality }
        Note right of Kafka: topic: oee.metrics.calculated<br/>Consumed by: ReportingService, AlertService, ERPSyncService
    end

    %% ── Alerting & Reporting ─────────────────────────────────────────────────
    rect rgb(255, 230, 230)
        Note over OEESvc,Kafka: Downstream Alerting
        alt OEE below target threshold (e.g., < 75%)
            Kafka-->>OEESvc: (self-loop) trigger OEE alert evaluation
            OEESvc->>Kafka: publish OEEThresholdBreached { machineId, oee, threshold: 0.75 }
            Note over Kafka: NotificationService sends SMS/email to Plant Manager
        end
    end
```

### TimescaleDB Schema Notes

```sql
-- Hypertable for machine state
SELECT create_hypertable('machine_state_log', 'time', chunk_time_interval => INTERVAL '1 day');

-- Continuous aggregate for hourly OEE
CREATE MATERIALIZED VIEW oee_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', time) AS bucket,
       machine_id,
       AVG(oee) AS avg_oee,
       MIN(oee) AS min_oee
FROM oee_metrics
GROUP BY bucket, machine_id;
```

---

## Sequence Diagram Conventions

| Symbol | Meaning |
|---|---|
| `rect rgb(...)` | Logical phase boundary with color coding |
| `alt / else` | Conditional branching (if-then-else logic) |
| `loop` | Repeating interaction over a collection |
| `Note over` / `Note right of` | In-line design annotations |
| `->>` | Synchronous request / call |
| `-->>` | Synchronous response or async delivery |
| `autonumber` | Step numbers for traceability in design reviews |

All sequence diagrams are **living documents** — update them when service contracts change or new
async flows are introduced. Diagrams are the authoritative source for sequence-level API contracts
during sprint planning and integration testing.
