# Fleet Management System — Requirements Document

**Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-01  
**Stakeholders:** Product Management, Engineering, Compliance, Operations

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Functional Requirements](#2-functional-requirements)
   - [2.1 Vehicle Management](#21-vehicle-management)
   - [2.2 Driver Management](#22-driver-management)
   - [2.3 GPS & Tracking](#23-gps--tracking)
   - [2.4 Maintenance Management](#24-maintenance-management)
   - [2.5 Fuel Management](#25-fuel-management)
   - [2.6 Compliance](#26-compliance)
   - [2.7 Incident Management](#27-incident-management)
   - [2.8 Reporting & Analytics](#28-reporting--analytics)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Constraints](#4-constraints)
5. [Assumptions](#5-assumptions)

---

## 1. System Overview

### 1.1 Purpose

The Fleet Management System (FMS) is a multi-tenant SaaS platform that provides logistics companies, freight carriers, municipal fleets, and enterprise vehicle fleets with end-to-end operational visibility and control over their vehicle assets and drivers. The system consolidates GPS tracking, driver management, regulatory compliance, preventive maintenance, fuel tracking, incident reporting, and executive analytics into a single platform.

### 1.2 Scope

The system covers the full lifecycle of fleet operations, from vehicle procurement onboarding through daily dispatch operations, driver compliance monitoring, and asset retirement. The platform does not include freight marketplace functionality, third-party driver hiring workflows, or cargo tracking beyond vehicle-level visibility.

### 1.3 Target Users

| Role | Description | Primary Interactions |
|---|---|---|
| Fleet Manager | Oversees fleet operations and performance | Vehicles, drivers, reports, alerts |
| Dispatcher | Assigns vehicles and routes to drivers daily | Dispatch, live map, driver communication |
| Driver | Operates vehicles and logs activity via mobile app | DVIRs, HOS logs, trip start/end, incidents |
| Mechanic | Performs and records vehicle maintenance | Work orders, DVIRs, inspection results |
| Compliance Officer | Ensures regulatory adherence | HOS logs, IFTA reports, DOT audit exports |
| Executive | Reviews cost, safety, and performance KPIs | Dashboards, cost reports, trend analytics |
| Tenant Administrator | Manages users, roles, and account settings | User management, billing, API keys |

### 1.4 Business Context

Fleet operators face the following core operational challenges that this system addresses:

- **Visibility gap:** Dispatchers lack real-time knowledge of vehicle location and driver status, leading to missed pickups and customer complaints.
- **Compliance risk:** FMCSA HOS violations and IFTA under-reporting expose carriers to fines up to $16,000 per violation.
- **Maintenance cost overruns:** Reactive maintenance costs 3–5× more than preventive maintenance and causes unplanned downtime.
- **Fuel fraud and waste:** Fuel theft and excessive idling account for 15–25% of avoidable fleet operating costs.
- **Data fragmentation:** Most fleets use 4–7 separate tools, creating manual reconciliation work and reporting delays.

---

## 2. Functional Requirements

Requirements are marked with priority: **[P1]** = Must Have, **[P2]** = Should Have, **[P3]** = Nice to Have.

---

### 2.1 Vehicle Management

**FR-01** [P1] — The system shall allow fleet managers to register vehicles by entering or scanning the 17-character VIN, which the system validates against NHTSA's VIN decoder API to auto-populate make, model, year, GVWR, and fuel type.

**FR-02** [P1] — The system shall maintain a vehicle profile for each registered vehicle containing: VIN, license plate number and state, registration expiration date, insurance policy number and expiration date, vehicle class (passenger, light-duty, heavy-duty, trailer), assigned tenant, and current operational status.

**FR-03** [P1] — The system shall track vehicle operational status with the following states: `active`, `in_maintenance`, `out_of_service`, `decommissioned`. Status transitions must be logged with the acting user, timestamp, and optional reason note.

**FR-04** [P1] — The system shall record and display current odometer reading for each vehicle. Odometer updates are accepted from: OBD-II telematics devices (automatic), driver manual entry via mobile app (with photo verification), and mechanic entry after service events.

**FR-05** [P1] — The system shall store and manage vehicle documents including: registration certificate, insurance certificate, state inspection certificate, IFTA decal, and any custom document types defined by the tenant. Each document record includes: document type, issuing authority, effective date, expiration date, file attachment (PDF/image), and upload timestamp.

**FR-06** [P1] — The system shall send automated alerts to fleet managers and designated recipients when vehicle documents are 60 days, 30 days, and 7 days from expiration.

**FR-07** [P2] — The system shall support bulk vehicle import via CSV upload with a defined column schema. The import process validates all rows before committing, returns per-row error details on validation failure, and provides a downloadable import result report.

**FR-08** [P2] — The system shall maintain a full change history (audit trail) for vehicle profile fields, recording the previous value, new value, changed-by user ID, and timestamp for every modification.

**FR-09** [P2] — The system shall support assignment of vehicles to asset groups (e.g., "Refrigerated Trucks - Northeast", "Sedans - HQ Pool") for organizational filtering and group-level reporting.

**FR-10** [P3] — The system shall track vehicle purchase cost, financing details, depreciation schedule (straight-line or declining balance), and calculate current book value per vehicle for asset management reporting.

---

### 2.2 Driver Management

**FR-11** [P1] — The system shall maintain a driver profile containing: full legal name, employee ID, date of birth, contact information (phone, email, emergency contact), CDL number and class, CDL state of issuance, CDL expiration date, medical certificate expiration date, and hire date.

**FR-12** [P1] — The system shall support driver document management for: commercial driver's license, medical examiner's certificate, drug test results, background check acknowledgment, and custom document types. Document expiration tracking and automated alerts follow the same pattern as vehicle documents (FR-06).

**FR-13** [P1] — The system shall enforce driver-vehicle assignment, ensuring a driver can only be the active operator of one vehicle at a time. Assigning a driver to a second vehicle without ending the prior assignment must return a validation error with the conflicting assignment details.

**FR-14** [P1] — The system shall calculate a driver safety score (0–100) updated after each completed trip, based on the weighted average of: speeding events (30%), harsh braking (25%), rapid acceleration (20%), sharp cornering (15%), and mobile phone usage while driving (10%). Weights are configurable per tenant.

**FR-15** [P1] — The system shall track driver Hours of Service (HOS) in accordance with FMCSA 49 CFR Part 395, recording duty status changes (driving, on-duty not driving, off-duty, sleeper berth) with timestamps accurate to the nearest minute.

**FR-16** [P1] — The system shall alert drivers via the mobile app when they are 30 minutes, 15 minutes, and 5 minutes away from an HOS violation, specifying the applicable rule (11-hour driving limit, 14-hour on-duty window, 60/70-hour limit).

**FR-17** [P2] — The system shall support driver groups (e.g., regional teams, vehicle type specializations) for batch assignment of policies, training requirements, and HOS rule sets.

**FR-18** [P2] — The system shall generate individual driver performance reports on a weekly and monthly basis, including: safety score trend, HOS violations, DVIR defect rate, fuel efficiency contribution, and incident history. Reports are accessible to the driver via the mobile app and to their manager via the web dashboard.

**FR-19** [P2] — The system shall track required training and certification completions per driver. Fleet managers can define training types with expiration periods; the system alerts managers when retraining is due.

**FR-20** [P3] — The system shall support driver self-service profile updates for contact information and emergency contacts, subject to manager approval workflow before the changes are committed to the primary record.

---

### 2.3 GPS & Tracking

**FR-21** [P1] — The system shall ingest GPS position reports from telematics devices via a UDP/TCP binary protocol and HTTP JSON API. Each position report must contain: device ID, timestamp (Unix milliseconds, UTC), latitude, longitude, heading (degrees), speed (km/h), altitude (meters), ignition state, and optional HDOP accuracy indicator.

**FR-22** [P1] — The system shall display the live position of all active vehicles on an interactive map in the web dashboard and dispatcher app, with positions updated within 15 seconds of the device reporting. Each vehicle icon shows: vehicle identifier, driver name, speed, heading, and last-update timestamp.

**FR-23** [P1] — The system shall store all GPS position records in a time-series database with retention of full-resolution data for 90 days and hourly aggregates for 2 years. Data older than 2 years is archived to cold storage (AWS S3 Glacier) and retrievable within 12 hours on request.

**FR-24** [P1] — The system shall detect and alert on the following GPS-derived events in real time:
- Speeding: vehicle exceeds posted speed limit or tenant-defined limit by a configurable threshold (default: 10 mph over)
- Excessive idle: engine running with zero speed for more than a configurable duration (default: 10 minutes)
- After-hours movement: vehicle moving outside the tenant-defined operating schedule
- GPS signal loss: no position report received for more than 5 minutes while ignition is on

**FR-25** [P1] — The system shall allow fleet managers to define geofences as circular areas (center point + radius), polygons (up to 200 vertices), or travel corridors (route path + buffer width). Each geofence has a name, associated vehicles or vehicle groups, and configurable entry/exit actions.

**FR-26** [P1] — The system shall generate geofence entry and exit events within 30 seconds of the vehicle crossing the boundary. Each event includes: vehicle ID, driver ID, geofence ID, event type (entry/exit), timestamp, and vehicle coordinates at time of detection.

**FR-27** [P1] — The system shall automatically record trips, defining trip start as ignition-on with speed > 5 km/h sustained for 60 seconds, and trip end as ignition-off or speed = 0 sustained for 5 minutes. Each trip record includes: start/end timestamps, start/end addresses (reverse geocoded), total distance, duration, maximum speed, average speed, fuel consumed (if available from telematics), and all associated driving events.

**FR-28** [P2] — The system shall provide a trip replay function allowing users to play back the GPS breadcrumb trail of any historical trip at 1×, 5×, 10×, or 30× speed on the map, with a timeline scrubber showing driving events (speeding, harsh braking, geofence crossings) as markers on the timeline.

---

### 2.4 Maintenance Management

**FR-29** [P1] — The system shall support creation of recurring preventive maintenance schedules per vehicle, triggering work orders based on: calendar interval (e.g., every 90 days), odometer interval (e.g., every 5,000 miles), engine hours interval, or whichever condition occurs first (compound trigger).

**FR-30** [P1] — The system shall create maintenance work orders containing: vehicle ID, work order type (preventive, corrective, DVIR-triggered, recall), description, priority (critical, high, normal, low), assigned mechanic, parts required with estimated cost, labor hours estimated, target completion date, and current status (open, in_progress, awaiting_parts, completed, cancelled).

**FR-31** [P1] — The system shall prevent dispatch assignment of a vehicle with an open critical or high-priority work order unless explicitly overridden by a fleet manager, who must provide a written justification that is stored with the work order record.

**FR-32** [P1] — The system shall support Driver Vehicle Inspection Reports (DVIR) in the mobile app, covering FMCSA Part 396.11 required inspection items for tractors, trailers, and non-CDL vehicles. Drivers mark each item as satisfactory or defective, add notes, and capture photos for defective items.

**FR-33** [P1] — The system shall classify DVIR defects as minor (vehicle is safe to operate) or major (out-of-service condition). A vehicle with an open major DVIR defect must be locked from dispatch assignment until a mechanic certifies the repair and the next driver signs the certified DVIR.

**FR-34** [P2] — The system shall maintain a service provider directory with contact information, service categories, rate schedules, and performance ratings. Fleet managers can route work orders to external service providers for vehicles without in-house service capability.

**FR-35** [P2] — The system shall track parts inventory for in-house maintenance, recording parts received, consumed in work orders, and current stock levels. Alerts are raised when parts stock falls below a configurable reorder threshold.

---

### 2.5 Fuel Management

**FR-36** [P1] — The system shall record fuel transactions for each vehicle including: transaction date/time, location (address and GPS coordinates), fuel type (diesel, gasoline, DEF, CNG, electric charge), quantity (gallons/kWh), unit cost, total cost, odometer at fill, and recording method (manual entry, fuel card integration, tank sensor).

**FR-37** [P1] — The system shall integrate with fleet fuel card providers (WEX, Comdata, Fleetcor) via their published APIs to automatically import card transaction data daily. Imported transactions are matched to vehicles by card number and flagged for manual review if the card is not assigned to a known vehicle.

**FR-38** [P1] — The system shall detect suspected fuel fraud by comparing tank-sensor fill events against fuel card transaction amounts. A discrepancy exceeding a configurable threshold (default: 5 gallons or 15%) generates a fraud alert assigned to the fleet manager for investigation.

**FR-39** [P1] — The system shall calculate fuel efficiency (miles per gallon or km/L) per vehicle per trip and aggregate it by vehicle, driver, vehicle group, and fleet, with trend comparison across configurable time periods.

**FR-40** [P2] — The system shall generate IFTA (International Fuel Tax Agreement) quarterly reports per IFTA license, calculating total miles and fuel gallons per jurisdiction from GPS mileage data and fuel transaction records. Reports are exportable in PDF and in the IFTA XML schema for electronic filing.

---

### 2.6 Compliance

**FR-41** [P1] — The system shall function as an FMCSA-compliant ELD (Electronic Logging Device) when the driver mobile app is paired with a certified telematics device, meeting all technical specifications in 49 CFR Part 395 Subpart B, including: automatic duty status recording from engine data, edit/annotation workflows, data transfer to enforcement officers via Bluetooth, USB, Web, and email.

**FR-42** [P1] — The system shall detect and log HOS rule violations automatically, categorizing them by violation type (daily driving limit, daily on-duty limit, 30-minute break, weekly hours, 34-hour restart), and present them in a violations log accessible to the compliance officer.

**FR-43** [P1] — The system shall support DOT inspection mode in the driver mobile app, allowing a driver to display their current HOS logs on screen and transfer logs electronically to a DOT officer without fleet manager involvement.

**FR-44** [P1] — The system shall generate an audit-ready compliance report package that includes: HOS logs with all edits and annotations, DVIR records, vehicle inspection history, driver document status, and IFTA fuel reports for a specified date range and set of vehicles/drivers.

**FR-45** [P2] — The system shall track regulatory document compliance coverage, displaying a compliance dashboard showing percentage of vehicles and drivers with all required documents current, with drill-down to identify specific expiring or expired items.

**FR-46** [P2] — The system shall maintain an immutable audit trail for all compliance-related records (HOS logs, DVIR records, IFTA reports), storing the original record, each subsequent edit, the editing user, timestamp, and stated reason. Audit trail records cannot be deleted through any user interface or API endpoint.

---

### 2.7 Incident Management

**FR-47** [P1] — The system shall allow drivers to report incidents from the mobile app, capturing: incident type (collision, theft, cargo damage, vehicle damage, near-miss, injury), date/time (defaulting to current), GPS location (auto-populated), description, severity (minor, moderate, major), and whether emergency services were contacted.

**FR-48** [P1] — The system shall support photo and video attachment to incident reports, accepting up to 20 files per incident (max 50 MB per file), stored in AWS S3 with access restricted to authorized users within the tenant.

**FR-49** [P1] — The system shall route incident notifications to configurable recipients by incident type and severity. Major incidents must notify the fleet manager and safety officer within 5 minutes of submission via push notification and email.

**FR-50** [P2] — The system shall support an incident investigation workflow with status tracking (reported, under_investigation, awaiting_insurance, resolved, closed), task assignment, comments thread, linked maintenance work orders (for vehicle damage), and final disposition documentation including insurance claim reference numbers.

---

### 2.8 Reporting & Analytics

**FR-51** [P1] — The system shall provide a real-time executive dashboard displaying: total active vehicles, vehicles in maintenance, drivers on duty, open critical alerts, fleet-wide fuel efficiency (last 30 days), and on-time delivery rate (when dispatch integration is enabled), all updated without page refresh.

**FR-52** [P1] — The system shall provide standard pre-built reports that can be run for any time period and exported as CSV, PDF, or XLSX:
- Vehicle utilization report (active days, idle hours, mileage by vehicle)
- Driver performance report (safety scores, violations, mileage by driver)
- Maintenance cost report (parts + labor cost by vehicle, group, or fleet)
- Fuel efficiency report (MPG trend, cost per mile by vehicle and driver)
- Geofence compliance report (entry/exit events, time in zone by vehicle)
- Incident summary report (counts by type, severity, and vehicle/driver)

**FR-53** [P1] — The system shall calculate total cost of ownership (TCO) per vehicle including: fuel cost, maintenance cost (parts + labor), insurance cost (if entered), tolls (if integrated), and depreciation. TCO is reportable per vehicle, group, or fleet for any date range.

**FR-54** [P2] — The system shall provide a custom report builder allowing users to select metrics, dimensions, filters, and time groupings from the available data model. Custom reports can be saved, scheduled for email delivery (daily/weekly/monthly), and shared with other users in the same tenant.

**FR-55** [P2] — The system shall provide a predictive analytics module that uses historical maintenance records and telematics data to estimate the remaining useful life of high-cost components (engine, transmission, brakes) with a confidence interval, triggering early maintenance recommendations when the estimated remaining life falls below a configurable threshold.

---

## 3. Non-Functional Requirements

### 3.1 Performance

**NFR-01** [P1] — The GPS ingestion service must process and persist incoming position reports with a median latency of less than 100 milliseconds, and a 99th percentile latency of less than 500 milliseconds, measured from message receipt at the load balancer to successful write to TimescaleDB, at a sustained throughput of 10,000 GPS messages per second.

**NFR-02** [P1] — The REST API must respond to 95% of requests within 200 milliseconds and 99% of requests within 500 milliseconds under normal operating load (defined as 5,000 concurrent active users). This excludes report generation endpoints, which may take up to 30 seconds.

**NFR-03** [P1] — The live map WebSocket feed must deliver position updates to connected dispatcher clients within 15 seconds of the GPS device reporting, including ingestion, processing, alert evaluation, and WebSocket push time.

**NFR-04** [P1] — The system must support 10,000 concurrently tracked vehicles per tenant and a minimum of 50 tenants operating simultaneously without degraded performance for any individual tenant.

**NFR-05** [P2] — Report generation for datasets of up to 1 million records (e.g., 12 months of GPS trips for a 500-vehicle fleet) must complete within 30 seconds for pre-built reports and within 120 seconds for custom report queries.

**NFR-06** [P2] — The mobile app must render the current HOS log and initiate a duty status change within 3 seconds on a 4G LTE connection. Offline actions (DVIR, duty status change) must sync within 10 seconds of network restoration.

### 3.2 Availability & Reliability

**NFR-07** [P1] — The platform must achieve 99.9% monthly uptime for all P1 services (GPS ingestion, live tracking API, HOS logging), measured as the percentage of minutes in a calendar month during which the service correctly processes requests. Planned maintenance windows are excluded from the uptime calculation.

**NFR-08** [P1] — The system must achieve a Recovery Point Objective (RPO) of 1 hour, meaning that in the event of a catastrophic failure, no more than 1 hour of transactional data is lost. This is achieved through continuous WAL shipping to AWS RDS Aurora read replicas and Kafka topic replication factor of 3.

**NFR-09** [P1] — The system must achieve a Recovery Time Objective (RTO) of 4 hours for full service restoration following a catastrophic failure of the primary AWS region, using a warm standby configuration in the secondary region.

**NFR-10** [P2] — The GPS ingestion service must degrade gracefully under partial outages. If the primary TimescaleDB instance becomes unavailable, ingested position reports must be buffered in Kafka for up to 24 hours and replayed to the database upon recovery, with no data loss.

### 3.3 Scalability

**NFR-11** [P1] — The system architecture must support horizontal scaling of the GPS ingestion service by adding Kubernetes pods, with linear throughput scaling demonstrated up to 100,000 GPS messages per second in load tests before initial production deployment.

**NFR-12** [P1] — The database schema and query patterns must support a TimescaleDB hypertable containing 100 billion GPS position rows without requiring architectural changes, achieved through time-based chunk partitioning and automatic data tiering.

**NFR-13** [P2] — The platform must support onboarding a new tenant with up to 10,000 vehicles within 4 hours of account provisioning, without manual intervention from the engineering team.

### 3.4 Security

**NFR-14** [P1] — All data in transit must be encrypted using TLS 1.3. All data at rest must be encrypted using AES-256 (AWS KMS managed keys). Customer-specific encryption keys are supported for enterprise tier tenants.

**NFR-15** [P1] — Multi-tenant data isolation must be enforced at the database layer using PostgreSQL Row Level Security (RLS) policies. Application-layer tenant filtering alone is insufficient; every query against shared tables must automatically scope results to the authenticated tenant.

**NFR-16** [P1] — The system must enforce Role-Based Access Control (RBAC) with a minimum of seven predefined roles (Tenant Admin, Fleet Manager, Dispatcher, Driver, Mechanic, Compliance Officer, Read-Only Analyst) plus support for custom roles with permission-level granularity.

**NFR-17** [P1] — API authentication must use short-lived JWTs (15-minute expiry) with refresh token rotation. Machine-to-machine integrations (telematics devices, third-party systems) must use scoped API keys with per-key rate limits and IP allowlist capability.

**NFR-18** [P2] — The system must comply with SOC 2 Type II controls, with annual third-party audit. Evidence collection for access management, change management, and availability controls must be automated and exportable.

### 3.5 Compliance & Data

**NFR-19** [P1] — The ELD module must satisfy all FMCSA 49 CFR Part 395 Subpart B technical specifications to achieve FMCSA self-certification, including: tamper detection for duty status records, engine synchronization, graph grid display format, and all required data elements.

**NFR-20** [P1] — The system must retain HOS log data for a minimum of 6 months in the active database and 6 additional months in accessible cold storage, in accordance with 49 CFR Part 395.8(k).

**NFR-21** [P2] — GPS position history must be subject to configurable tenant-level retention policies with a minimum of 90 days full-resolution and a maximum of 7 years (for jurisdictions requiring extended vehicle activity records). Data deletion requests under GDPR/CCPA must be fulfilled within 30 days, excluding records required for regulatory compliance.

**NFR-22** [P2] — The system must be deployable in a GDPR-compliant configuration where all personal data for EU-based drivers (location history, HOS logs, driver profiles) is stored and processed exclusively in AWS EU (Frankfurt) or AWS EU (Ireland) regions, with no cross-region replication of personal data.

---

## 4. Constraints

**C-01** — The ELD-certified telematics device integration is limited to devices on the FMCSA-registered ELD list. The system cannot claim ELD compliance for devices not meeting hardware certification requirements.

**C-02** — IFTA reporting covers US states and Canadian provinces only. International operations (Mexico, EU) require a separate jurisdiction data package not included in the initial release.

**C-03** — Real-time traffic integration for route optimization is provided by HERE Maps API. Route optimization accuracy is subject to HERE Maps data coverage quality, which may be limited in rural or remote areas.

**C-04** — Fuel card integrations are limited to WEX, Comdata, and Fleetcor in the initial release. Additional fuel card providers require custom integration development estimated at 3–6 weeks per provider.

**C-05** — The system requires vehicles to be equipped with a compatible telematics device (OBDII, J1939 heavy-duty, or an approved hardwired unit) for GPS tracking. Vehicles without telematics devices can be registered and managed administratively but will not appear on the live map.

**C-06** — The mobile app requires iOS 16+ or Android 12+ due to the background location APIs and Bluetooth Low Energy requirements for ELD device pairing.

---

## 5. Assumptions

**A-01** — Fleet managers and dispatchers have reliable internet access (minimum 10 Mbps) at their office locations. The web dashboard is not designed for offline use.

**A-02** — Drivers have company-issued or personally owned smartphones meeting the minimum OS requirements (iOS 16+ / Android 12+) and an active data plan covering their operating territory.

**A-03** — The customer is responsible for procuring and installing telematics devices in their vehicles. The system provides a device configuration portal but does not manage physical device installation logistics.

**A-04** — GPS data from telematics devices is assumed to be accurate within 5 meters under open-sky conditions. Accuracy degradation in urban canyons, tunnels, and underground parking is expected and does not constitute a system defect.

**A-05** — IFTA quarterly reporting calculations are based on GPS mileage data and may differ from odometer-based mileage by up to 2% due to GPS sampling intervals and signal loss events. Tenants are responsible for reconciling and certifying their IFTA submissions.

**A-06** — The customer's HR or payroll system is responsible for maintaining authoritative employee records. The FMS driver profiles are operational records and are not considered the system of record for employment data.

**A-07** — All monetary values in the system are stored and displayed in USD. Currency conversion for international operations is not supported in the initial release.
