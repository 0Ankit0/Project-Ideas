# System Sequence Diagrams — Fleet Management System

## Overview

This document captures the major end-to-end interaction flows within the Fleet Management System (FMS). Each sequence diagram illustrates how actors, services, and data stores collaborate to deliver core platform capabilities. These diagrams serve as the authoritative reference for service contract design, integration testing strategy, and onboarding new engineers.

---

## Flow 1: Vehicle Telemetry Ingestion

This flow describes how real-time GPS telemetry emitted by an in-vehicle device is ingested, validated, persisted, and evaluated against geofence rules. High-frequency pings (typically every 5–30 seconds per vehicle) are the data backbone of live tracking, trip reconstruction, HOS correlation, and driver scoring.

```mermaid
sequenceDiagram
    autonumber
    participant Device as GPS/ELD Device
    participant MQTT as MQTT Broker (EMQ X)
    participant Telem as Telemetry Service
    participant Redis as Redis (Live Position Cache)
    participant TSDB as TimescaleDB
    participant Kafka as Apache Kafka
    participant Geo as Geofence Service
    participant Alert as Alert Service
    participant WS as WebSocket Gateway
    participant UI as Dispatcher Web App

    Device->>MQTT: PUBLISH /fleet/{vehicleId}/telemetry<br/>{lat, lon, speed, heading, altitude, odometer, timestamp}
    MQTT->>Telem: Forward message (QoS 1)
    Telem->>Telem: Validate payload schema (JSON Schema)

    alt Invalid payload
        Telem->>MQTT: PUBACK (discard, log parse error)
        Note over Telem: Dead-letter to Kafka topic: telemetry.dlq
    else Valid payload
        Telem->>Telem: Enrich ping (vehicleId → fleet metadata lookup)
        Telem->>Redis: SET vehicle:live:{vehicleId} {lat, lon, speed, heading, ts} EX 120
        Redis-->>Telem: OK
        Telem->>TSDB: INSERT INTO gps_pings (vehicle_id, lat, lon, speed, heading, altitude, odometer, ts)
        TSDB-->>Telem: INSERT 1

        alt Speed > vehicle speed limit threshold
            Telem->>Kafka: PUBLISH telemetry.speed-violation<br/>{vehicleId, speed, limit, lat, lon, ts}
            Note over Kafka: Alert Service consumes this topic
        end

        Telem->>Kafka: PUBLISH telemetry.ping<br/>{vehicleId, lat, lon, speed, ts}
        Kafka-->>Geo: Consume telemetry.ping (Geofence Service consumer group)
        Geo->>Geo: Load active geofences for vehicle (from PostGIS cache)
        Geo->>Geo: ST_Contains(geofence.polygon, POINT(lon, lat))

        alt Vehicle entered a geofence
            Geo->>Kafka: PUBLISH geofence.event<br/>{vehicleId, geofenceId, eventType: ENTER, ts}
        else Vehicle exited a geofence
            Geo->>Kafka: PUBLISH geofence.event<br/>{vehicleId, geofenceId, eventType: EXIT, ts}
        end

        Kafka-->>Alert: Consume geofence.event
        Alert->>Alert: Evaluate alert rules for this geofence/vehicle
        Alert->>Kafka: PUBLISH alert.triggered<br/>{alertId, vehicleId, driverId, severity, message}

        Kafka-->>WS: Consume telemetry.ping (WebSocket fanout group)
        WS->>UI: Push live position update (Socket.IO event: vehicle:position)
        UI->>UI: Update live map marker for vehicleId
    end
```

### Key Design Decisions

| Concern | Decision |
|---|---|
| Telemetry transport | MQTT (QoS 1) — lightweight, suitable for constrained cellular networks |
| Live position store | Redis with 120-second TTL — O(1) reads for live map queries |
| Historical store | TimescaleDB hypertable partitioned by time — efficient range scans |
| Fan-out to geofence | Kafka topic `telemetry.ping` — decouples ingestion from evaluation |
| Back-pressure | Kafka consumer lag monitoring via Prometheus; Telem Service auto-scales |

---

## Flow 2: Driver Pre-Trip DVIR Inspection

A Driver Vehicle Inspection Report (DVIR) is a federally mandated inspection that drivers must complete before operating a commercial vehicle. This flow covers the mobile-app-driven inspection workflow from authentication through vehicle status determination.

```mermaid
sequenceDiagram
    autonumber
    participant Driver as Driver (Mobile App)
    participant Gateway as API Gateway (Kong)
    participant Auth as Auth Service
    participant DVIR as DVIR Service
    participant Vehicle as Vehicle Service
    participant Kafka as Apache Kafka
    participant Notify as Notification Service
    participant Dispatch as Dispatcher Web App

    Driver->>Gateway: POST /auth/login {email, password}
    Gateway->>Auth: Forward request
    Auth->>Auth: Validate credentials, check MFA requirement
    Auth-->>Gateway: 200 OK {accessToken, refreshToken, driverProfile}
    Gateway-->>Driver: 200 OK {accessToken, driverProfile}

    Driver->>Gateway: GET /vehicles/assigned?driverId={id}<br/>Authorization: Bearer {token}
    Gateway->>Auth: Validate JWT (token introspection)
    Auth-->>Gateway: 200 OK {driverId, roles}
    Gateway->>Vehicle: GET /vehicles/assigned?driverId={id}
    Vehicle-->>Gateway: 200 OK [{vehicleId, vin, make, model, licensePlate, lastDVIRStatus}]
    Gateway-->>Driver: Vehicle list with last inspection status

    Driver->>Gateway: POST /dvir/start<br/>{vehicleId, inspectionType: PRE_TRIP, driverId, odometer}
    Gateway->>DVIR: Create DVIR session
    DVIR->>DVIR: Load inspection checklist template for vehicle type
    DVIR-->>Gateway: 200 OK {dvirId, checklistItems[], previousDefects[]}
    Gateway-->>Driver: Checklist with any carry-over defects from last inspection

    Note over Driver: Driver walks around vehicle,<br/>marks each checklist item PASS / DEFECT

    loop For each checklist section (Engine, Brakes, Lights, Tires, etc.)
        Driver->>Gateway: PATCH /dvir/{dvirId}/item<br/>{itemId, status: PASS|DEFECT, defectNote?, photoUrl?}
        Gateway->>DVIR: Update checklist item
        DVIR-->>Gateway: 204 No Content
    end

    Driver->>Gateway: POST /dvir/{dvirId}/submit<br/>{signature: base64, certificationText, defectsRepaired: bool}
    Gateway->>DVIR: Submit and finalize DVIR

    DVIR->>DVIR: Validate all items completed
    DVIR->>DVIR: Persist final DVIR record with e-signature

    alt No defects reported
        DVIR->>Vehicle: PATCH /vehicles/{vehicleId}/status {status: ACTIVE}
        DVIR-->>Gateway: 201 Created {dvirId, status: SATISFACTORY, vehicleStatus: ACTIVE}
        Gateway-->>Driver: Vehicle cleared for operation
    else Defects reported — not safety-critical
        DVIR->>Vehicle: PATCH /vehicles/{vehicleId}/status {status: ACTIVE, defectsNoted: true}
        DVIR->>Kafka: PUBLISH dvir.defect-noted {dvirId, vehicleId, defects[]}
        Kafka-->>Notify: Consume dvir.defect-noted
        Notify->>Dispatch: Email/push: "Vehicle {plate} has noted defects — review before next dispatch"
        DVIR-->>Gateway: 201 Created {dvirId, status: DEFECTS_NOTED, vehicleStatus: ACTIVE}
        Gateway-->>Driver: Vehicle approved with noted defects
    else Safety-critical defects reported
        DVIR->>Vehicle: PATCH /vehicles/{vehicleId}/status {status: OUT_OF_SERVICE}
        DVIR->>Kafka: PUBLISH dvir.out-of-service {dvirId, vehicleId, criticalDefects[]}
        Kafka-->>Notify: Consume dvir.out-of-service
        Notify->>Dispatch: Urgent alert: "Vehicle {plate} placed OUT OF SERVICE — do not dispatch"
        DVIR-->>Gateway: 201 Created {dvirId, status: UNSAFE, vehicleStatus: OUT_OF_SERVICE}
        Gateway-->>Driver: Vehicle removed from service — contact dispatcher
    end
```

### DVIR Checklist Categories

| Category | Items Inspected |
|---|---|
| Engine Compartment | Oil level, coolant, belts, battery |
| Brakes | Air/hydraulic pressure, brake pads, emergency brake |
| Lights & Electrical | Headlights, turn signals, hazards, reflectors |
| Tires & Wheels | Tread depth, inflation, lug nuts, rims |
| Cab Interior | Seat belts, mirrors, wipers, horn, gauges |
| Cargo/Body | Doors, latches, coupling devices |

---

## Flow 3: Predictive Maintenance Work Order

The Maintenance Service integrates with an ML anomaly detection pipeline. When sensor telemetry patterns suggest an impending component failure, an automated work order is created, dispatched to a mechanic, and tracked through completion.

```mermaid
sequenceDiagram
    autonumber
    participant ML as ML Anomaly Model (SageMaker)
    participant Kafka as Apache Kafka
    participant Maint as Maintenance Service
    participant Vehicle as Vehicle Service
    participant Notify as Notification Service
    participant Dispatch as Dispatcher Web App
    participant Mechanic as Mechanic (Mobile/Web)
    participant DB as PostgreSQL

    Note over ML: Scheduled batch job runs every hour.<br/>Analyses last 30 days of telemetry per vehicle.

    ML->>Kafka: PUBLISH maintenance.anomaly-detected<br/>{vehicleId, componentType: ENGINE_OIL,<br/>confidenceScore: 0.91, predictedFailureDays: 12,<br/>telemetryEvidence: {avgOilTemp, pressureDrops}}

    Kafka-->>Maint: Consume maintenance.anomaly-detected
    Maint->>Maint: Check if open work order already exists for vehicleId + componentType

    alt Duplicate work order exists
        Maint->>DB: UPDATE work_orders SET confidence_score = 0.91,<br/>updated_at = NOW() WHERE id = {existing}
        Note over Maint: Suppress duplicate notification
    else No existing work order
        Maint->>Vehicle: GET /vehicles/{vehicleId} (fetch metadata)
        Vehicle-->>Maint: {vin, make, model, year, odometerMiles, assignedDriverId}

        Maint->>DB: INSERT INTO work_orders<br/>{vehicleId, type: PREDICTIVE, component: ENGINE_OIL,<br/>priority: HIGH, status: OPEN, estimatedDueDate: NOW()+12days,<br/>confidence: 0.91, evidence: {}}
        DB-->>Maint: work_order_id = WO-20240315-0042

        Maint->>Kafka: PUBLISH maintenance.work-order-created<br/>{workOrderId, vehicleId, component, priority, dueDate}

        Kafka-->>Notify: Consume maintenance.work-order-created
        Notify->>Dispatch: Push notification + email: "Predictive alert: WO-20240315-0042<br/>Vehicle {vin} — Engine Oil anomaly detected (91% confidence)"
    end

    Dispatch->>Maint: GET /work-orders/{workOrderId} (review details)
    Maint-->>Dispatch: Work order details with telemetry evidence chart URL

    Dispatch->>Maint: PATCH /work-orders/{workOrderId}<br/>{status: ASSIGNED, mechanicId, scheduledDate, shopLocation}
    Maint->>DB: UPDATE work_orders SET status = ASSIGNED, mechanic_id = {id},<br/>scheduled_date = {date}
    Maint->>Kafka: PUBLISH maintenance.work-order-assigned {workOrderId, mechanicId, vehicleId}
    Kafka-->>Notify: Consume maintenance.work-order-assigned
    Notify->>Mechanic: Push notification: "New work order WO-20240315-0042 assigned to you"

    Mechanic->>Maint: GET /work-orders/{workOrderId} (view task details)
    Maint-->>Mechanic: Full work order with vehicle history, parts list

    Note over Mechanic: Mechanic performs oil change / component inspection

    Mechanic->>Maint: PATCH /work-orders/{workOrderId}<br/>{status: IN_PROGRESS, notes: "Drained oil, inspecting pump..."}
    Maint->>DB: UPDATE work_orders SET status = IN_PROGRESS

    Mechanic->>Maint: POST /work-orders/{workOrderId}/complete<br/>{actualCostUsd, partsUsed[], laborHours, mileageAtService,<br/>technicianSignature, completionNotes}
    Maint->>DB: UPDATE work_orders SET status = COMPLETED, completed_date = NOW(),<br/>cost_usd = {cost}, mileage_at_service = {odometer}
    Maint->>DB: INSERT INTO maintenance_records {vehicleId, workOrderId, type, cost, mileage}
    Maint->>Vehicle: PATCH /vehicles/{vehicleId}/odometer-service-record {mileageAtService}
    Vehicle-->>Maint: 204 No Content

    Maint->>Kafka: PUBLISH maintenance.work-order-completed {workOrderId, vehicleId, cost}
    Kafka-->>Notify: Consume maintenance.work-order-completed
    Notify->>Dispatch: Email summary: "WO-20240315-0042 completed — cost ${cost}, vehicle cleared"

    alt Mechanic flagged additional issues
        Mechanic->>Maint: POST /work-orders (new work order from inspection)<br/>{vehicleId, type: CORRECTIVE, component: BRAKE_PADS, priority: MEDIUM}
        Maint->>DB: INSERT INTO work_orders (new record)
        Note over Maint: Cascade dispatch notification flow repeats
    end
```

---

## Flow 4: IFTA Compliance Report Generation

The International Fuel Tax Agreement (IFTA) requires carriers to report miles driven and fuel purchased in each jurisdiction per quarter. This flow covers automated aggregation of GPS mileage data and fuel records to produce a submission-ready IFTA report.

```mermaid
sequenceDiagram
    autonumber
    participant Officer as Compliance Officer
    participant Gateway as API Gateway
    participant Auth as Auth Service
    participant Comply as Compliance Service
    participant Trip as Trip Service
    participant Fuel as Fuel Service
    participant TSDB as TimescaleDB
    participant DB as PostgreSQL
    participant S3 as AWS S3
    participant Notify as Notification Service

    Officer->>Gateway: POST /compliance/ifta/reports<br/>{quarter: Q1, year: 2024, companyId}<br/>Authorization: Bearer {token}
    Gateway->>Auth: Validate JWT + check role: COMPLIANCE_OFFICER
    Auth-->>Gateway: 200 OK
    Gateway->>Comply: Initiate IFTA report generation

    Comply->>DB: INSERT INTO ifta_reports {companyId, quarter: Q1, year: 2024,<br/>status: PROCESSING, requestedBy, createdAt}
    DB-->>Comply: reportId = IFTA-2024-Q1-001

    Comply-->>Gateway: 202 Accepted {reportId, status: PROCESSING,<br/>estimatedCompletionSeconds: 30}
    Gateway-->>Officer: 202 Accepted — report generation started

    Note over Comply: Async processing begins

    Comply->>Trip: GET /trips?companyId={id}&startDate=2024-01-01&endDate=2024-03-31
    Trip-->>Comply: [{tripId, vehicleId, driverId, distanceMiles,<br/>startJurisdiction, endJurisdiction, route[]}...]

    Comply->>TSDB: SELECT jurisdiction, SUM(segment_miles)<br/>FROM trip_segments<br/>WHERE company_id = {id} AND ts BETWEEN Q1 dates<br/>GROUP BY jurisdiction
    TSDB-->>Comply: [{jurisdiction: TX, miles: 12450.3}, {jurisdiction: OK, miles: 3820.1}, ...]

    Comply->>Fuel: GET /fuel-records?companyId={id}&startDate=2024-01-01&endDate=2024-03-31
    Fuel-->>Comply: [{fuelRecordId, vehicleId, gallons, costUsd,<br/>purchaseState, fuelType, timestamp}...]

    loop For each jurisdiction in mileage data
        Comply->>Comply: Calculate taxable gallons = (miles / fleet_mpg)
        Comply->>Comply: Fetch IFTA tax rate for jurisdiction + fuel type
        Comply->>Comply: tax_owed = taxable_gallons × rate − fuel_purchased_in_jurisdiction
    end

    Comply->>Comply: Aggregate totals: totalMiles, totalGallons,<br/>totalTaxOwed, netTaxDue (after credits)

    Comply->>DB: UPDATE ifta_reports SET<br/>jurisdictions = {aggregated JSON},<br/>total_miles = {x}, total_gallons = {y},<br/>fuel_tax_owed = {z}, status = GENERATING_PDF

    Comply->>Comply: Render IFTA Schedule 1 PDF (Puppeteer/PDFKit)
    Comply->>S3: PUT /ifta-reports/{companyId}/IFTA-2024-Q1-001.pdf
    S3-->>Comply: {eTag, versionId, s3Key}

    Comply->>DB: UPDATE ifta_reports SET<br/>status = COMPLETED, pdf_s3_key = {key},<br/>completed_at = NOW()

    Comply->>Notify: Trigger notification {channel: EMAIL,<br/>recipient: officer@company.com,<br/>subject: "IFTA Q1 2024 Report Ready",<br/>downloadUrl: signedS3Url (expires 7 days)}
    Notify-->>Officer: Email with download link

    Officer->>Gateway: GET /compliance/ifta/reports/IFTA-2024-Q1-001
    Gateway->>Comply: Fetch report details
    Comply-->>Gateway: {reportId, status: COMPLETED,<br/>totalMiles, totalTaxOwed,<br/>jurisdictions[], downloadUrl}
    Gateway-->>Officer: Full report summary + PDF download URL
```

### IFTA Calculation Notes

| Term | Description |
|---|---|
| Taxable gallons | Miles driven in jurisdiction ÷ fleet average MPG |
| Net tax | Tax owed in jurisdiction − fuel tax already paid at pump in that jurisdiction |
| Credit | If fuel purchased in jurisdiction exceeds taxable amount, carrier gets a credit |
| Filing frequency | Quarterly — due last day of month following quarter end |
| Supported fuel types | Diesel, Gasoline, LNG, CNG, Propane (different rate tables) |
