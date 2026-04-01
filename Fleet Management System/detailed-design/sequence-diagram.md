# Sequence Diagrams — Fleet Management System

## Overview

This document describes five detailed interaction flows across the Fleet Management System. Each diagram captures the full end-to-end behavior including error paths, retry logic, and integration with external systems.

---

## 1. Real-Time GPS Telemetry Processing

This flow describes how a GPS ping travels from a physical device installed in a vehicle all the way through ingestion, validation, live cache update, time-series persistence, geofence evaluation, and driver notification.

```mermaid
sequenceDiagram
    autonumber
    participant DEV as GPS Device
    participant MQTT as MQTT Broker<br/>(AWS IoT Core)
    participant SQS as SQS Queue
    participant TS as Telemetry Service
    participant RC as Redis Cache
    participant TSDB as TimescaleDB
    participant GS as Geofence Service
    participant AS as Alert Service
    participant KF as Kafka
    participant NS as Notification Service
    participant MA as Driver Mobile App

    DEV->>MQTT: Publish telemetry payload<br/>topic: device/{vehicleId}/telemetry
    Note over DEV,MQTT: Binary payload: lat/lng/speed/<br/>heading/odometer/engineOn/fuelLevel

    MQTT-->>SQS: IoT Rule forwards message
    SQS-->>TS: Receive message (long-poll)

    TS->>TS: Parse binary payload → GpsPing schema
    TS->>TS: Validate coordinates (range check)
    TS->>TS: Validate speed plausibility (< 200 mph)
    TS->>TS: Check timestamp ordering (no replay)

    alt Validation failed
        TS->>KF: Publish telemetry.invalid event
        TS->>RC: Increment bad-ping counter for vehicleId
        Note over TS: Dead-letter SQS message after 3 retries
    else Validation passed
        TS->>RC: HSET vehicle:position:{vehicleId}<br/>lat, lng, speed, ts, engineOn
        Note over TS,RC: Redis TTL: 300s per position key

        TS->>TSDB: Batch INSERT into gps_pings hypertable
        Note over TS,TSDB: Bulk insert every 100 pings or 5s,<br/>whichever comes first

        alt TSDB write fails
            TS->>TS: Retry with exponential backoff (3x)
            TS->>KF: Publish telemetry.write.failed if all retries exhausted
        end

        TS->>KF: Publish telemetry.position.updated event
        Note over TS,KF: Topic: telemetry.position.updated<br/>Partition key: vehicleId

        KF-->>GS: Consume telemetry.position.updated

        GS->>RC: GET active geofences for fleet group
        Note over GS,RC: Cache miss: query PostGIS, warm cache

        GS->>GS: ST_Within / ST_Intersects evaluation<br/>for all active geofences

        alt Vehicle enters or exits geofence
            GS->>TSDB: INSERT GeofenceEvent record
            GS->>KF: Publish geofence.breach event
            Note over GS,KF: Includes: vehicleId, driverId,<br/>geofenceId, eventType, severity

            KF-->>AS: Consume geofence.breach

            AS->>AS: Load AlertRule for geofence
            AS->>AS: Evaluate rule conditions<br/>(speed, time-of-day, direction)

            alt Alert rule triggered
                AS->>TSDB: INSERT Alert record
                AS->>KF: Publish alert.created event

                KF-->>NS: Consume alert.created

                NS->>MA: Push notification via FCM/APNs
                Note over NS,MA: "Entering restricted zone:<br/>Warehouse District Geofence"

                opt Driver acknowledges
                    MA->>NS: ACK push notification
                    NS->>AS: Mark alert acknowledged
                end
            end
        end
    end
```

---

## 2. Driver Mobile App — Pre-Trip DVIR Submission

This flow covers a driver performing a DOT-compliant pre-trip vehicle inspection using the mobile app. It includes defect handling and fleet manager notification.

```mermaid
sequenceDiagram
    autonumber
    participant DR as Driver
    participant MA as Mobile App
    participant GW as API Gateway
    participant DS as DVIR Service
    participant VS as Vehicle Service
    participant DB as PostgreSQL
    participant KF as Kafka
    participant FM as Fleet Manager
    participant NS as Notification Service

    DR->>MA: Tap "Start Pre-Trip Inspection"
    MA->>GW: POST /dvir/start<br/>{ vehicleId, driverId, inspectionType: PRE_TRIP }
    GW->>DS: Route request (JWT validated)

    DS->>VS: GET /vehicles/{vehicleId}/assignment
    VS->>DB: SELECT driver_id FROM vehicles WHERE id = vehicleId
    DB-->>VS: Return assigned driver
    VS-->>DS: Return vehicle assignment

    alt Driver not assigned to this vehicle
        DS-->>GW: 403 Forbidden — vehicle not assigned
        GW-->>MA: Error: vehicle assignment mismatch
        MA-->>DR: Show error toast
    else Driver is correctly assigned
        DS->>DB: SELECT * FROM dvir_templates WHERE vehicle_type = ?
        DB-->>DS: Return 20-point inspection template
        DS->>DB: INSERT DVIR record (status: DRAFT)
        DS-->>GW: 201 Created — DVIR id + inspection checklist
        GW-->>MA: Return DVIR session + checklist items

        loop For each of 20 inspection items
            DR->>MA: Mark item PASS / FAIL / N/A
            MA->>MA: Store response locally (offline-capable)
        end

        opt Defect found on inspection item
            DR->>MA: Add defect description + photo
            MA->>GW: POST /dvir/{dvirId}/defect<br/>{ component, description, severity, photoBase64 }
            GW->>DS: Add defect to DVIR
            DS->>DB: INSERT dvir_defects record
            DS->>DS: Upload photo to S3
            DB-->>DS: Defect saved
        end

        DR->>MA: Sign inspection and submit
        MA->>GW: POST /dvir/{dvirId}/submit<br/>{ signature, odometerReading }
        GW->>DS: Submit DVIR

        DS->>DS: Validate all required checklist items completed
        DS->>DB: UPDATE dvir SET status = SUBMITTED, signed_at = NOW()

        alt No defects found
            DS->>VS: PATCH /vehicles/{vehicleId}/status { status: ACTIVE }
            DS->>DB: UPDATE vehicles SET status = ACTIVE
            DS->>KF: Publish dvir.submitted { result: CLEARED }
            DS-->>GW: 200 OK — vehicle cleared for operation
            GW-->>MA: DVIR submitted — vehicle cleared ✓
            MA-->>DR: Show green confirmation screen
        else Defects found requiring attention
            DS->>VS: PATCH /vehicles/{vehicleId}/status { status: OUT_OF_SERVICE }
            DS->>DB: UPDATE vehicles SET status = OUT_OF_SERVICE
            DS->>KF: Publish dvir.submitted { result: DEFECT_FOUND }

            KF-->>NS: Consume dvir.submitted
            NS->>FM: Push + email notification<br/>"DVIR Defects Found — Vehicle {plate}"
            NS->>DR: Push: "Trip held — vehicle has defects. Contact dispatcher."

            DS-->>GW: 200 OK — vehicle grounded, defects logged
            GW-->>MA: Show defect summary and dispatcher contact
            MA-->>DR: Display defect list and next steps
        end
    end
```

---

## 3. Predictive Maintenance Trigger and Work Order Lifecycle

This flow captures how the ML-based predictive maintenance engine detects an anomaly from telemetry data and generates a work order that is fulfilled by a mechanic.

```mermaid
sequenceDiagram
    autonumber
    participant KF as Kafka
    participant ML as ML Maintenance Service
    participant MS as Maintenance Service
    participant DB as PostgreSQL
    participant DS as Dispatcher
    participant ME as Mechanic
    participant MA as Mobile App
    participant VS as Vehicle Service
    participant NS as Notification Service

    loop Continuous telemetry stream monitoring
        KF-->>ML: Consume telemetry.position.updated events
        ML->>ML: Apply feature extraction<br/>(rolling avg engine temp, RPM, vibration)
        ML->>ML: Run anomaly detection model<br/>(Isolation Forest / LSTM threshold)
    end

    alt Anomaly threshold exceeded
        ML->>ML: Compute confidence score ≥ 0.82
        ML->>ML: Identify failure mode (engine overheat risk)

        ML->>MS: POST /maintenance/work-orders<br/>{ vehicleId, type: PREDICTIVE, description, confidence }
        MS->>DB: INSERT work_orders (status: OPEN)
        MS->>DB: UPDATE maintenance_schedules SET next_service_due = NOW()+48h

        MS->>KF: Publish maintenance.work-order.created

        KF-->>NS: Consume maintenance.work-order.created
        NS->>DS: Push notification + email<br/>"Predictive alert: Engine temp anomaly — Truck #T-042"

        DS->>MS: GET /maintenance/work-orders/{workOrderId}
        MS->>DB: SELECT work order with vehicle details
        DB-->>MS: Return work order
        MS-->>DS: Return work order detail

        DS->>MS: PATCH /maintenance/work-orders/{workOrderId}/assign<br/>{ mechanicId }
        MS->>DB: UPDATE work_orders SET assigned_mechanic_id = ?, status = IN_PROGRESS
        MS->>KF: Publish maintenance.work-order.assigned

        KF-->>NS: Consume maintenance.work-order.assigned
        NS->>ME: Push notification<br/>"Work order assigned: Truck #T-042 engine inspection"

        ME->>MA: Open work order in mobile app
        MA->>MS: PATCH /maintenance/work-orders/{workOrderId}/accept
        MS->>DB: UPDATE work_orders SET status = ACCEPTED

        ME->>MA: Record parts used + labor hours
        MA->>MS: POST /maintenance/work-orders/{workOrderId}/service-report<br/>{ parts[], laborHours, notes }

        MS->>DB: INSERT maintenance_records record
        MS->>DB: INSERT parts records

        ME->>MA: Mark work order complete
        MA->>MS: PATCH /maintenance/work-orders/{workOrderId}/complete
        MS->>DB: UPDATE work_orders SET status = COMPLETED, completed_at = NOW()

        MS->>VS: PATCH /vehicles/{vehicleId}<br/>{ odometerMiles, engineHours, status: ACTIVE }
        VS->>DB: UPDATE vehicles record

        MS->>DB: UPDATE maintenance_schedules SET last_service_date = NOW()
        MS->>KF: Publish maintenance.work-order.completed
        KF-->>NS: Consume event
        NS->>DS: Notification: "Work order #WO-2847 completed — vehicle cleared"
    end
```

---

## 4. Geofence Breach Detection and Multi-Channel Alert Dispatch

This flow details how a vehicle crossing a geofence boundary is detected, evaluated, and escalated across multiple notification channels, ending with fleet manager acknowledgement.

```mermaid
sequenceDiagram
    autonumber
    participant TS as Telemetry Service
    participant KF as Kafka
    participant GS as Geofence Service
    participant RC as Redis
    participant PG as PostgreSQL<br/>(PostGIS)
    participant AS as Alert Service
    participant NS as Notification Service
    participant FM as Fleet Manager (Web)
    participant DR as Driver Mobile App
    participant SMS as SMS Gateway<br/>(Twilio)
    participant EM as Email Service<br/>(SES)

    TS->>KF: Publish telemetry.position.updated<br/>{ vehicleId: V-101, lat: 37.77, lng: -122.41, speed: 28 }

    KF-->>GS: Consume telemetry.position.updated (consumer group: geofence-svc)

    GS->>RC: GET geofences:active:{fleetGroupId}
    Note over GS,RC: Returns cached list of active geofence IDs

    alt Cache miss
        GS->>PG: SELECT id, geometry, speed_limit FROM geofences<br/>WHERE is_active = true AND fleet_group_id = ?
        PG-->>GS: Return geofences with PostGIS geometry
        GS->>RC: SET geofences:active:{fleetGroupId} EX 300
    end

    GS->>PG: SELECT g.id FROM geofences g<br/>WHERE ST_Within(ST_SetSRID(ST_MakePoint(-122.41, 37.77), 4326), g.geometry)<br/>AND g.id = ANY(cachedIds)
    PG-->>GS: Return matching geofenceId = GF-014

    GS->>PG: SELECT * FROM geofence_events<br/>WHERE vehicle_id = V-101 AND geofence_id = GF-014<br/>AND event_type = ENTERED ORDER BY occurred_at DESC LIMIT 1
    Note over GS,PG: Check if vehicle was previously inside<br/>to determine ENTER vs REMAIN event

    alt Vehicle just entered geofence (state transition: outside → inside)
        GS->>PG: INSERT INTO geofence_events<br/>{ vehicleId, geofenceId, eventType: ENTERED, speed: 28 }
        GS->>KF: Publish geofence.breach<br/>{ vehicleId, driverId, geofenceId, eventType: ENTERED,<br/>speed: 28, speedLimit: 15, severity: CRITICAL }

        KF-->>AS: Consume geofence.breach (consumer group: alert-svc)

        AS->>PG: SELECT * FROM alert_rules<br/>WHERE geofence_id = GF-014 AND is_active = true
        PG-->>AS: Return 2 alert rules:<br/>1. SPEED_IN_ZONE (threshold: speedLimit exceeded)<br/>2. UNAUTHORIZED_ENTRY (time window check)

        loop Evaluate each alert rule
            AS->>AS: Evaluate rule condition against event context
        end

        alt Speed exceeds geofence limit (28 mph > 15 mph limit)
            AS->>PG: INSERT INTO alerts { severity: CRITICAL,<br/>title: "Speed Violation in Restricted Zone",<br/>vehicleId, driverId }
            AS->>KF: Publish alert.created { alertId, channels: [PUSH, SMS, EMAIL] }

            KF-->>NS: Consume alert.created

            par Parallel notification dispatch
                NS->>DR: FCM push: "⚠️ Speed alert — Slow down in Warehouse Zone"
                NS->>SMS: Twilio SMS to fleet manager<br/>"CRITICAL: Vehicle T-042 speeding in Warehouse District (28 mph / 15 mph limit)"
                NS->>EM: SES email to fleet manager + safety officer
            end

            FM->>AS: PATCH /alerts/{alertId}/acknowledge { userId }
            AS->>PG: UPDATE alerts SET is_acknowledged = true,<br/>acknowledged_by = ?, acknowledged_at = NOW()
            AS->>KF: Publish alert.acknowledged
            KF-->>NS: Consume alert.acknowledged
            NS->>DR: Push: "Alert acknowledged by dispatcher"

            AS-->>FM: 200 OK — alert resolved
        end
    else Vehicle already inside geofence (REMAIN event — no re-alert)
        GS->>GS: Suppress duplicate breach event
        Note over GS: De-duplication window: 60s per vehicle+geofence pair
    end
```

---

## 5. IFTA Quarterly Report Generation

This flow describes the compliance officer requesting an IFTA quarterly fuel tax report, including mileage aggregation by jurisdiction using PostGIS state boundary intersections.

```mermaid
sequenceDiagram
    autonumber
    participant CO as Compliance Officer
    participant WEB as Web Dashboard
    participant GW as API Gateway
    participant CS as Compliance Service
    participant TS as Trip Service
    participant FS as Fuel Service
    participant PG as PostgreSQL<br/>(PostGIS)
    participant TSDB as TimescaleDB
    participant PDF as PDF Generator<br/>(Puppeteer)
    participant S3 as AWS S3
    participant EM as Email Service<br/>(SES)

    CO->>WEB: Navigate to Compliance → IFTA Reports
    WEB->>GW: GET /compliance/ifta/preview?year=2024&quarter=3
    GW->>CS: Route to Compliance Service

    CS->>TS: GET /trips?year=2024&quarter=3&fleetGroupId=FG-01
    TS->>PG: SELECT id, start_odometer, end_odometer,<br/>origin_lat, origin_lng, dest_lat, dest_lng,<br/>actual_start, actual_end FROM trips<br/>WHERE date_range AND status = COMPLETED
    PG-->>TS: Return 1,847 completed trips
    TS-->>CS: Return trip list

    loop For each trip (batched in 100s)
        CS->>TSDB: SELECT lat, lng, timestamp FROM gps_pings<br/>WHERE vehicle_id = ? AND timestamp BETWEEN trip.start AND trip.end<br/>ORDER BY timestamp
        TSDB-->>CS: Return GPS track for trip

        CS->>PG: SELECT s.state_code,<br/>SUM(ST_Length(ST_Intersection(track_line, s.geometry)::geography)) AS miles<br/>FROM us_states s<br/>WHERE ST_Intersects(ST_MakeLine(pings), s.geometry)<br/>GROUP BY s.state_code
        Note over CS,PG: PostGIS line-state intersection<br/>computes miles driven per jurisdiction
        PG-->>CS: Return mileage breakdown: { TX: 312.4, OK: 87.1, KS: 44.3, ... }
    end

    CS->>FS: GET /fuel-records?year=2024&quarter=3&fleetGroupId=FG-01
    FS->>PG: SELECT state_code, SUM(gallons) FROM fuel_records<br/>WHERE date_range GROUP BY state_code
    PG-->>FS: Return fuel purchased per state
    FS-->>CS: Return fuel records: { TX: 4312.2 gal, OK: 891.0 gal, ... }

    CS->>CS: Aggregate mileage by jurisdiction across all trips
    CS->>CS: Calculate MPG per vehicle (total miles / total gallons)
    CS->>CS: Calculate total fuel consumed (miles / fleet avg MPG)
    CS->>CS: Compute taxable gallons per state<br/>(gallons used in state − gallons purchased in state)
    CS->>CS: Apply state-specific IFTA tax rates
    CS->>CS: Calculate net tax owed or credit per jurisdiction

    CS->>PG: INSERT INTO ifta_reports { year, quarter, fleetGroupId,<br/>totalMiles, totalGallons, status: DRAFT }
    CS->>PG: INSERT INTO ifta_jurisdictions (bulk) { reportId, stateCode,<br/>taxableMiles, taxPaidGallons, taxableGallons, taxRate, netTax }

    CS-->>GW: Return report summary preview
    GW-->>WEB: Display jurisdiction table with tax breakdown
    WEB-->>CO: Preview IFTA report data

    CO->>WEB: Click "Generate PDF Report"
    WEB->>GW: POST /compliance/ifta/{reportId}/generate-pdf
    GW->>CS: Trigger PDF generation

    CS->>PDF: Render IFTA report template with jurisdiction data
    PDF->>PDF: Generate table: state | miles | fuel purchased |<br/>fuel used | taxable gallons | rate | tax owed
    PDF-->>CS: Return PDF buffer (multi-page)

    CS->>S3: PUT compliance-exports/ifta/2024-Q3-{fleetGroupId}.pdf
    Note over CS,S3: Bucket: compliance-exports<br/>SSE-KMS encrypted, 7-year retention

    S3-->>CS: Return pre-signed download URL (valid 24h)
    CS->>PG: UPDATE ifta_reports SET pdf_url = ?, status = GENERATED

    CS->>EM: Send email to compliance officer<br/>{ subject: "IFTA Q3 2024 Report Ready", downloadUrl }
    EM-->>CO: Email delivered with download link

    CS-->>GW: 200 OK { reportId, downloadUrl, totalTaxOwed }
    GW-->>WEB: Show success banner with download button
    WEB-->>CO: "IFTA Q3 2024 report generated — 14 jurisdictions, $8,421.50 net tax owed"
```

---

## Sequence Diagram Coverage Summary

| Flow | Services Involved | Key Patterns |
|---|---|---|
| GPS Telemetry Processing | Telemetry, Redis, TimescaleDB, Geofence, Alert, Notification | Kafka fan-out, PostGIS eval, retry/DLQ |
| Pre-Trip DVIR Submission | DVIR, Vehicle, Notification | Offline form, S3 photo upload, conditional grounding |
| Predictive Maintenance | ML Service, Maintenance, Vehicle, Notification | ML anomaly trigger, work order lifecycle |
| Geofence Breach Alerting | Geofence, Alert, Notification, SMS/Email | Multi-channel dispatch, dedup suppression |
| IFTA Report Generation | Compliance, Trip, Fuel, PostgreSQL/PostGIS, S3 | GIS mileage split, tax calculation, PDF export |
