# Data Flow Diagram — Fleet Management System

## Overview

This document presents a structured, multi-level decomposition of how data flows through the Fleet Management System. Three levels of detail are provided: a high-level context view (Level 0), a functional decomposition (Level 1), and a deep-dive into the highest-throughput subsystem — telemetry processing (Level 2).

Data flow diagrams focus on **what** data moves between processes and stores, without prescribing implementation order or service boundaries (those are covered in `architecture-diagram.md`).

---

## Level 0 — Context Data Flow Diagram

Level 0 shows the FMS as a single process ("black box") and identifies all external entities that exchange data with the system.

```mermaid
flowchart LR
    subgraph External["External Entities"]
        DEV["📡 GPS / ELD Devices"]
        DRVAPP["📱 Driver Mobile App"]
        DISPWEB["🖥️ Dispatcher Web App"]
        MGMTWEB["🖥️ Fleet Manager Web App"]
        COMPOFF["🖥️ Compliance Officer Web App"]
        MAPAPI["🗺️ Mapping API\n(Google Maps / HERE)"]
        FUELCARD["💳 Fuel Card Networks\n(WEX / Fleetcor)"]
        NOTIFY["📧 Notification Providers\n(SendGrid / Twilio)"]
        ELDVEND["🔌 ELD Vendor APIs\n(Samsara / Geotab)"]
        DOTFMCSA["🏛️ DOT / FMCSA Portal"]
        WEATHER["⛈️ Weather API"]
    end

    FMS["⚙️ Fleet Management System"]

    DEV -- "GPS pings: lat/lon/speed/heading/odometer/timestamp" --> FMS
    DEV -- "ELD duty status events, fault codes, engine data" --> FMS
    FMS -- "Device config updates, firmware version" --> DEV

    DRVAPP -- "DVIR submission, HOS edits, trip start/end" --> FMS
    FMS -- "Assigned trips, work orders, DVIR checklists, alerts" --> DRVAPP

    DISPWEB -- "Dispatch commands, route assignments, alert acknowledgement" --> FMS
    FMS -- "Live vehicle positions, trip status, alert feed, work orders" --> DISPWEB

    MGMTWEB -- "Vehicle/driver CRUD, rule configuration, report requests" --> FMS
    FMS -- "Fleet KPIs, utilization reports, cost analytics, driver scores" --> MGMTWEB

    COMPOFF -- "IFTA/HOS report requests, document management" --> FMS
    FMS -- "Compliance reports, HOS violations, IFTA PDFs, DOT documents" --> COMPOFF

    FMS -- "Route optimization requests: waypoints, constraints" --> MAPAPI
    MAPAPI -- "Optimized routes, ETAs, geocoded addresses, traffic data" --> FMS

    FUELCARD -- "Fuel transaction records: gallons, cost, merchant, location" --> FMS
    FMS -- "Authorized vehicle/driver pairs for card validation" --> FUELCARD

    FMS -- "Email/SMS/push notification payloads" --> NOTIFY
    NOTIFY -- "Delivery receipts, bounce events" --> FMS

    ELDVEND -- "ELD event stream: duty status, drive events, unidentified" --> FMS
    FMS -- "Driver assignments, company config for ELD sync" --> ELDVEND

    FMS -- "Driver qualification files, safety records exports" --> DOTFMCSA
    DOTFMCSA -- "Audit requests, inspection results" --> FMS

    FMS -- "Location queries for weather-aware route planning" --> WEATHER
    WEATHER -- "Conditions, road hazard data, severe weather alerts" --> FMS
```

---

## Level 1 — Functional Decomposition DFD

Level 1 decomposes the FMS into its major processing subsystems and shows the primary data flows between processes and persistent stores.

```mermaid
flowchart TD
    %% ─── External Inputs ─────────────────────────────────────
    DEV["📡 GPS/ELD Device"]
    DRIVER["📱 Driver App"]
    DISPATCH["🖥️ Dispatcher"]
    MANAGER["🖥️ Fleet Manager"]
    OFFICER["🖥️ Compliance Officer"]
    FUELCARD["💳 Fuel Card Network"]
    MAPAPI["🗺️ Mapping API"]
    ELDVEND["🔌 ELD Vendor API"]

    %% ─── Processing Subsystems ───────────────────────────────
    P1["P1\nTelemetry\nProcessing"]
    P2["P2\nTrip\nManagement"]
    P3["P3\nDriver & HOS\nManagement"]
    P4["P4\nMaintenance\nManagement"]
    P5["P5\nGeofence\nEvaluation"]
    P6["P6\nCompliance\nReporting"]
    P7["P7\nAlert & Notification\nEngine"]
    P8["P8\nRoute\nOptimization"]
    P9["P9\nFuel\nManagement"]
    P10["P10\nDVIR\nProcessing"]
    P11["P11\nAnalytics &\nScoring"]

    %% ─── Data Stores ─────────────────────────────────────────
    DS1[("DS1\nVehicle DB\nPostgreSQL")]
    DS2[("DS2\nDriver DB\nPostgreSQL")]
    DS3[("DS3\nTrip DB\nPostgreSQL")]
    DS4[("DS4\nTelemetry Store\nTimescaleDB")]
    DS5[("DS5\nGeofence DB\nPostgreSQL + PostGIS")]
    DS6[("DS6\nMaintenance DB\nPostgreSQL")]
    DS7[("DS7\nFuel DB\nPostgreSQL")]
    DS8[("DS8\nCompliance DB\nPostgreSQL")]
    DS9[("DS9\nReports Store\nS3")]
    DS10[("DS10\nLive State Cache\nRedis")]
    DS11[("DS11\nEvent Bus\nApache Kafka")]

    %% ─── Telemetry Flow ──────────────────────────────────────
    DEV -- "Raw GPS ping\n{lat,lon,speed,ts}" --> P1
    P1 -- "Validated ping record" --> DS4
    P1 -- "Live position {vehicleId,lat,lon,ts}" --> DS10
    P1 -- "Telemetry event" --> DS11
    P1 -- "Odometer update" --> DS1

    %% ─── Trip Flow ───────────────────────────────────────────
    DRIVER -- "Trip start/end signal" --> P2
    P2 -- "Trip record {vehicleId,driverId,odometer}" --> DS3
    P2 -- "Distance/fuel aggregates" --> DS3
    DS4 -- "GPS pings for trip window" --> P2
    DS1 -- "Vehicle fuel efficiency" --> P2
    DS11 -- "Trip events" --> P2

    %% ─── Driver & HOS Flow ───────────────────────────────────
    DRIVER -- "HOS duty status change" --> P3
    ELDVEND -- "ELD duty events" --> P3
    P3 -- "HOS log entry" --> DS8
    P3 -- "Driver status update" --> DS2
    P3 -- "HOS violation event" --> DS11

    %% ─── Maintenance Flow ────────────────────────────────────
    MANAGER -- "Work order commands" --> P4
    DS11 -- "Anomaly detected event" --> P4
    P4 -- "Work order record" --> DS6
    P4 -- "Vehicle status update" --> DS1
    P4 -- "Work order event" --> DS11

    %% ─── Geofence Flow ───────────────────────────────────────
    DS11 -- "Telemetry ping event" --> P5
    DS5 -- "Active geofence rules" --> P5
    P5 -- "Geofence event {ENTER/EXIT}" --> DS5
    P5 -- "Geofence breach event" --> DS11

    %% ─── Compliance Flow ─────────────────────────────────────
    OFFICER -- "Report request {quarter,year}" --> P6
    DS8 -- "HOS log data" --> P6
    DS3 -- "Trip mileage data" --> P6
    DS4 -- "GPS mileage by jurisdiction" --> P6
    DS7 -- "Fuel purchase by jurisdiction" --> P6
    P6 -- "IFTA report record" --> DS8
    P6 -- "Report PDF" --> DS9
    P6 -- "Report ready event" --> DS11

    %% ─── Alert & Notification Flow ───────────────────────────
    DS11 -- "All domain events" --> P7
    DS5 -- "Alert rules" --> P7
    P7 -- "Alert record" --> DS8
    P7 -- "Notification payload {email/SMS/push}" --> DISPATCH
    P7 -- "Notification payload" --> MANAGER
    P7 -- "Notification payload" --> DRIVER

    %% ─── Route Optimization Flow ─────────────────────────────
    DISPATCH -- "Dispatch request {stops,vehicle,constraints}" --> P8
    P8 -- "Optimization request" --> MAPAPI
    MAPAPI -- "Optimized route {waypoints,eta,polyline}" --> P8
    P8 -- "Route record" --> DS3
    P8 -- "Assigned route" --> DISPATCH

    %% ─── Fuel Management Flow ────────────────────────────────
    FUELCARD -- "Transaction feed {gallons,cost,merchant}" --> P9
    DRIVER -- "Manual fuel entry" --> P9
    P9 -- "Fuel record" --> DS7
    P9 -- "Odometer sync" --> DS1
    P9 -- "Fuel anomaly event" --> DS11

    %% ─── DVIR Flow ───────────────────────────────────────────
    DRIVER -- "Inspection checklist submission" --> P10
    P10 -- "DVIR record + defects" --> DS6
    P10 -- "Vehicle status update" --> DS1
    P10 -- "DVIR event {fit/unfit}" --> DS11

    %% ─── Analytics Flow ──────────────────────────────────────
    DS3 -- "Trip data for scoring" --> P11
    DS4 -- "Telemetry events for scoring" --> P11
    DS2 -- "Driver profiles" --> P11
    DS1 -- "Fleet inventory" --> P11
    P11 -- "Driver score records" --> DS2
    P11 -- "KPI metrics" --> DS8
    P11 -- "Analytics dashboard data" --> MANAGER
```

### Level 1 Data Stores Reference

| Store | Technology | Contents | Retention |
|---|---|---|---|
| DS1 Vehicle DB | PostgreSQL | Vehicles, registration, insurance | Indefinite |
| DS2 Driver DB | PostgreSQL | Drivers, scores, license data | Indefinite |
| DS3 Trip DB | PostgreSQL | Trips, routes, waypoints | 7 years (DOT) |
| DS4 Telemetry Store | TimescaleDB | GPS pings, OBD-II data | 2 years hot, S3 archive |
| DS5 Geofence DB | PostgreSQL + PostGIS | Geofences, events, rules | Indefinite |
| DS6 Maintenance DB | PostgreSQL | Work orders, DVIR, maintenance records | 7 years (DOT) |
| DS7 Fuel DB | PostgreSQL | Fuel records, card transactions | 5 years (IFTA) |
| DS8 Compliance DB | PostgreSQL | HOS logs, IFTA reports, alerts | 7 years (DOT) |
| DS9 Reports Store | AWS S3 | PDF reports, document files | 7 years |
| DS10 Live Cache | Redis | Vehicle live positions, online status | TTL 120s |
| DS11 Event Bus | Apache Kafka | All domain events | 7-day retention |

---

## Level 2 — Telemetry Processing Deep Dive

This diagram expands Process P1 (Telemetry Processing) into its internal sub-processes, showing the detailed step-by-step data transformation from raw GPS ping to stored record and downstream events.

```mermaid
flowchart TD
    START(["📡 GPS Ping Arrives\nvia MQTT"])

    P1_1["P1.1\nMQTT Broker\nMessage Receipt\n(EMQ X)"]
    P1_2["P1.2\nPayload Deserialization\n& Schema Validation"]
    P1_3["P1.3\nVehicle Identity\nResolution"]
    P1_4["P1.4\nCoordinate Sanity\nCheck"]
    P1_5["P1.5\nSpeed Violation\nDetection"]
    P1_6["P1.6\nIdle Detection\n(speed=0, ignition=ON)"]
    P1_7["P1.7\nOdometer\nReconciliation"]
    P1_8["P1.8\nLive Position\nCache Update"]
    P1_9["P1.9\nTimescaleDB\nPersistence"]
    P1_10["P1.10\nTrip Correlation\n(open trip lookup)"]
    P1_11["P1.11\nGeofence Evaluation\nEvent Publish"]
    P1_12["P1.12\nWebSocket\nFanout"]

    DLQ["💀 Dead Letter Queue\n(Kafka: telemetry.dlq)"]
    DS_REDIS[("Redis\nLive Position Cache")]
    DS_TSDB[("TimescaleDB\nGPS Pings Hypertable")]
    DS_KAFKA_PING(["Kafka\ntelemetry.ping"])
    DS_KAFKA_SPD(["Kafka\ntelemetry.speed-violation"])
    DS_KAFKA_IDLE(["Kafka\ntelemetry.idle-event"])
    DS_KAFKA_GEO(["Kafka\ngeofence.evaluation-request"])
    DS_TRIP[("PostgreSQL\nTrips")]
    DS_WS(["WebSocket\nGateway"])

    START --> P1_1
    P1_1 -- "Raw JSON payload" --> P1_2

    P1_2 -- "Validation FAILED\n(malformed/missing fields)" --> DLQ
    P1_2 -- "Valid payload\n{vehicleId, lat, lon, speed,\nheading, ts, odometer}" --> P1_3

    P1_3 -- "vehicleId not found\nin Vehicle DB" --> DLQ
    P1_3 -- "Enriched ping\n+ company metadata" --> P1_4

    P1_4 -- "lat/lon outside valid\nbounds or GPS jump > 200mph" --> DLQ
    P1_4 -- "Validated coordinates" --> P1_5

    P1_5 -- "speed > vehicle\nspeed limit threshold" --> DS_KAFKA_SPD
    P1_5 -- "Ping with speed flag" --> P1_6

    P1_6 -- "ignition=ON AND speed=0\nfor > 3 consecutive pings" --> DS_KAFKA_IDLE
    P1_6 -- "Ping with idle flag" --> P1_7

    P1_7 -- "Odometer delta\n(reconcile reported vs calculated)" --> P1_8

    P1_8 -- "SET vehicle:live:{id}\n{lat,lon,speed,ts} EX 120" --> DS_REDIS
    DS_REDIS -- "OK" --> P1_9

    P1_9 -- "INSERT INTO gps_pings\n(vehicle_id, lat, lon, speed,\nheading, altitude, odometer, ts)" --> DS_TSDB
    DS_TSDB -- "INSERT confirmed" --> P1_10

    P1_10 -- "Lookup: open trip\nfor vehicleId" --> DS_TRIP
    DS_TRIP -- "tripId (if active trip)" --> P1_10
    P1_10 -- "Publish enriched ping\n{vehicleId, tripId?, lat, lon, speed, ts}" --> DS_KAFKA_PING

    DS_KAFKA_PING -- "Consumed by\nGeofence Service" --> P1_11
    P1_11 -- "Geofence evaluation\nrequest {vehicleId, lat, lon}" --> DS_KAFKA_GEO

    DS_KAFKA_PING -- "Consumed by\nWebSocket Gateway" --> P1_12
    P1_12 -- "Socket.IO push:\nvehicle:position event" --> DS_WS

    style DLQ fill:#ff6b6b,color:#fff
    style DS_REDIS fill:#DC382D,color:#fff
    style DS_TSDB fill:#336791,color:#fff
    style DS_KAFKA_PING fill:#231F20,color:#fff
    style DS_KAFKA_SPD fill:#231F20,color:#fff
    style DS_KAFKA_IDLE fill:#231F20,color:#fff
    style DS_KAFKA_GEO fill:#231F20,color:#fff
```

### Level 2 Processing Notes

| Sub-process | Throughput Expectation | Error Handling |
|---|---|---|
| P1.1 MQTT Receipt | 1,000–50,000 msgs/sec (fleet scale) | QoS 1 ensures at-least-once delivery |
| P1.2 Schema Validation | < 1ms per message | Invalid messages to DLQ, logged with raw payload |
| P1.3 Identity Resolution | < 2ms (Redis vehicle lookup) | Unknown device IDs quarantined; ops team alerted |
| P1.4 Coordinate Check | < 0.5ms | GPS jumps filtered; previous position retained |
| P1.5 Speed Violation | < 0.5ms | Per-vehicle configurable threshold |
| P1.9 TimescaleDB Write | Batched inserts every 500ms | Retry with exponential backoff on DB errors |
| P1.10 Trip Correlation | < 3ms (Redis trip lookup) | Pings without active trip still stored; correlated post-hoc |

### Data Volumes at Scale

| Data Element | Rate | Daily Volume |
|---|---|---|
| GPS Pings (500 vehicles, 30s interval) | ~17 msgs/sec | ~1.44M rows |
| Speed violation events | ~0.5% of pings | ~7,200/day |
| Idle events | ~2% of pings | ~28,800/day |
| Geofence evaluations | ~1.44M/day | Depends on fence count |
| Live cache operations | ~34 ops/sec | — |
| WebSocket pushes | ~17 events/sec | — |

---

## Data Flow Summary

The following table maps key data elements to their sources, transformations, and sinks across the full system:

| Data Element | Source | Key Transformations | Primary Sink |
|---|---|---|---|
| GPS Ping | GPS/ELD Device | Validate → Enrich → Correlate to trip | TimescaleDB, Redis, Kafka |
| Fuel Transaction | Fuel Card Network / Driver App | Normalize → Reconcile with odometer | PostgreSQL Fuel DB |
| HOS Status Change | Driver App / ELD Vendor | Validate 30-min rounding → Detect violations | PostgreSQL Compliance DB |
| DVIR Submission | Driver Mobile App | Validate completeness → Determine vehicle status | PostgreSQL Maintenance DB |
| Geofence Event | Geofence Evaluation (PostGIS) | Classify ENTER/EXIT → Match alert rules | PostgreSQL Geofence DB, Kafka |
| Work Order | Maintenance Service / ML Model | Prioritize → Assign → Track to completion | PostgreSQL Maintenance DB |
| IFTA Report | Compliance Service | Aggregate mileage by jurisdiction → Calculate tax | PostgreSQL Compliance DB, S3 |
| Driver Score | Analytics Service | Aggregate events over period → Weight & normalize | PostgreSQL Driver DB |
| Alert | Alert Engine | Match event to rules → Deduplicate → Route | PostgreSQL Compliance DB, Notification |
