# Use Case Descriptions — Fleet Management System

This document provides detailed structured descriptions for eight core use cases of the Fleet Management System. Each description follows a standard template covering actors, preconditions, main flow, alternative flows, exception flows, and postconditions.

---

## UC-01: Track Vehicle in Real-Time

| Field        | Value |
|--------------|-------|
| **ID**       | UC-01 |
| **Name**     | Track Vehicle in Real-Time |
| **Actors**   | Fleet Manager (primary), Dispatcher (primary), GPS Device (secondary), System (secondary) |
| **Priority** | Critical |
| **Frequency**| Continuous — polled on dashboard load and refreshed every 30 seconds |

### Preconditions
1. The vehicle has been registered in the system with a linked GPS device serial number.
2. The GPS device is powered on, has an active cellular or satellite data connection, and is transmitting telemetry.
3. The user (Fleet Manager or Dispatcher) is authenticated and has been granted the `VEHICLE_TRACKING` permission.
4. The live map dashboard has been loaded in a supported browser or the mobile application.

### Main Flow
1. The user navigates to the Live Map dashboard.
2. The system queries the vehicle location cache (Redis) and retrieves the last known position for all vehicles assigned to the user's organisation.
3. The system renders vehicle markers on the map tile layer, colour-coded by status: green (moving), amber (idling), red (stopped > 30 minutes), grey (offline).
4. The GPS device transmits a telemetry packet every 30 seconds containing: latitude, longitude, altitude, speed (km/h), heading (degrees), ignition state, odometer reading, and a timestamp.
5. The system ingests the telemetry packet via the GPS Ingestion API, validates the device token, and writes the record to the time-series location store.
6. The system updates the vehicle's cached position and pushes the updated marker coordinates to the dashboard via WebSocket.
7. The system evaluates the new GPS ping against all active geofence zones associated with the vehicle's organisation.
8. If a geofence entry or exit event is detected, the system creates a geofence event record and triggers the configured alert rules (push notification, email, or SMS).
9. The user can click on a vehicle marker to open a detail panel showing: driver name, current speed, ignition state, last update timestamp, and today's trip summary.

### Alternative Flows
- **AF-01 GPS Signal Lost:** If no telemetry packet is received for a vehicle within 90 seconds, the system marks the vehicle as "Signal Lost" and displays the last known location with a timestamp tooltip reading "Last seen [X] minutes ago". The marker changes to grey. The system continues retrying and automatically restores the live marker when the signal resumes.
- **AF-02 Vehicle Not Assigned:** If a vehicle has no active driver assignment, the tracking panel omits the driver field and shows "Unassigned" instead. Tracking continues normally.
- **AF-03 Map Tiles Unavailable:** If the mapping API returns a 5xx error, the system falls back to a secondary tile provider (HERE Maps) and logs a warning. The user sees a banner: "Using backup map provider."

### Exception Flows
- **EF-01 Invalid Device Token:** If the GPS device transmits with an expired or unrecognised token, the system rejects the packet, increments a rejection counter, and sends an alert to the Fleet Manager after 5 consecutive rejections.
- **EF-02 Duplicate Packet:** If a packet with an identical device ID and timestamp is received within a 60-second deduplication window, it is discarded silently.

### Postconditions
1. The vehicle's position in the location cache has been updated to the latest telemetry reading.
2. All geofence entry/exit events generated during the tracking session have been persisted to the events log.
3. The trip waypoint sequence has been updated in the active trip record.

---

## UC-02: Record Trip

| Field        | Value |
|--------------|-------|
| **ID**       | UC-02 |
| **Name**     | Record Trip |
| **Actors**   | Driver (primary), GPS Device (secondary), System (secondary) |
| **Priority** | Critical |
| **Frequency**| Every time a vehicle is driven |

### Preconditions
1. The driver is authenticated in the mobile application and has an active vehicle assignment.
2. The vehicle has passed the pre-trip DVIR inspection (no critical defects outstanding).
3. The GPS device installed in the vehicle is online and transmitting telemetry.

### Main Flow
1. The driver taps **Start Trip** in the mobile application.
2. The system creates a new `Trip` record in `ACTIVE` state, recording: driver ID, vehicle ID, start timestamp, and start odometer reading sourced from the GPS device's last telemetry packet.
3. The system activates enhanced waypoint recording for this vehicle, ensuring GPS pings are stored as ordered waypoint records linked to the trip.
4. Every 30 seconds, the GPS device transmits a telemetry packet. The system appends a waypoint record to the trip containing: sequence number, latitude, longitude, speed, heading, timestamp, and engine RPM if available via OBD-II.
5. The system continuously evaluates speed data against posted speed limits (sourced from the mapping API's road segment data) and records speeding events when the vehicle exceeds the limit by more than 10 km/h for more than 5 consecutive seconds.
6. The system detects harsh driving events using accelerometer data: harsh braking (deceleration > 0.4g), harsh acceleration (acceleration > 0.3g), and sharp cornering (lateral force > 0.3g). Each event is stored as a driving behaviour record linked to the trip.
7. The driver taps **End Trip** in the mobile application upon completing the journey.
8. The system sets the trip status to `COMPLETED`, records the end timestamp and end odometer reading.
9. The system calculates trip metrics: total distance (haversine sum of waypoints), driving duration (ignition-on to ignition-off), idle duration, average speed, maximum speed, fuel consumed (if OBD-II data available).
10. The system invokes the Driver Score calculation engine, which processes all driving behaviour events for this trip and generates a trip-level score (0–100).
11. The system updates the driver's rolling 30-day performance score using an exponential weighted moving average.
12. The trip record transitions to `ARCHIVED` state and becomes available in the trip history view.

### Alternative Flows
- **AF-01 GPS Loss Mid-Trip:** If GPS signal is lost for up to 5 minutes, the system interpolates the gap using dead reckoning (last known heading and speed) and marks the interpolated waypoints with a `ESTIMATED` flag. If signal loss exceeds 5 minutes, the gap is recorded as a `SIGNAL_LOSS` segment.
- **AF-02 App Crash / Unexpected Disconnect:** If the driver's mobile app disconnects without ending the trip, the system sets the trip to `PENDING_CLOSURE` after 15 minutes of inactivity. The next time the driver opens the app, they are prompted to confirm trip end.

### Exception Flows
- **EF-01 DVIR Defect Outstanding:** If the driver attempts to start a trip with a critical defect flagged on the vehicle, the system blocks the start and displays the defect details with a message to contact their dispatcher.

### Postconditions
1. A completed trip record exists with full waypoint sequence, behaviour events, and calculated metrics.
2. The driver's performance score has been updated.
3. Trip distance has been added to the vehicle's total mileage for maintenance threshold monitoring.

---

## UC-03: Schedule Maintenance

| Field        | Value |
|--------------|-------|
| **ID**       | UC-03 |
| **Name**     | Schedule Maintenance |
| **Actors**   | System (primary trigger), Dispatcher (primary responder), Fleet Manager (secondary), Mechanic (secondary) |
| **Priority** | High |
| **Frequency**| Continuous monitoring; work order creation as needed |

### Preconditions
1. The vehicle has at least one maintenance schedule rule configured (e.g., oil change every 8,000 km or 6 months, whichever comes first).
2. The vehicle's current odometer reading is up to date in the system.

### Main Flow
1. The system's maintenance monitoring process runs every hour, comparing each vehicle's current odometer reading and last service date against all configured maintenance rules.
2. When a vehicle's mileage or time threshold is within 500 km or 14 days of the service due point, the system creates a `MaintenanceSchedule` record with status `DUE_SOON` and sends an alert to the Dispatcher and Fleet Manager.
3. The Dispatcher reviews the maintenance due alert in the Maintenance module and confirms the service is needed.
4. The Dispatcher selects a service provider from the approved vendors list (or enters a new one) and assigns the work order target date.
5. The system creates a `WorkOrder` record linked to the vehicle and maintenance schedule, with status `OPEN`, and notifies the assigned service provider via email.
6. The Mechanic (at the service provider) receives the work order, performs the required maintenance, and records: service date, services performed, parts replaced (with part numbers and costs), labour hours, and the updated odometer reading.
7. The Mechanic marks the work order as `COMPLETE` in the system.
8. The system updates the vehicle's `lastServiceDate` and `lastServiceOdometer` fields, and calculates the next due threshold for each maintenance rule.
9. The vehicle's maintenance status returns to `UP_TO_DATE` and the Fleet Manager receives a completion notification.

### Alternative Flows
- **AF-01 Manual Scheduling:** A Fleet Manager can manually create a maintenance schedule for unscheduled repairs (e.g., tyre replacement) by specifying the vehicle, service type, and target date directly, bypassing the threshold monitoring trigger.
- **AF-02 DVIR-Triggered Work Order:** If a Driver flags a defect during a pre-trip or post-trip DVIR, the system automatically creates a `WorkOrder` with `DVIR_DEFECT` type and priority `HIGH`, notifying the Dispatcher immediately.

### Exception Flows
- **EF-01 No Approved Vendors Available:** If no service providers are configured for the vehicle's location region, the system alerts the Fleet Manager to add a vendor before the work order can be assigned.

### Postconditions
1. The work order is marked complete and linked to the maintenance schedule record.
2. The vehicle's next maintenance thresholds have been recalculated and stored.
3. The vehicle is cleared for continued operation unless a new defect was discovered during servicing.

---

## UC-04: Log Fuel Record

| Field        | Value |
|--------------|-------|
| **ID**       | UC-04 |
| **Name**     | Log Fuel Record |
| **Actors**   | Driver (primary), Fleet Manager (primary), System (secondary), External Integrations/Fuel Card Provider (secondary) |
| **Priority** | High |
| **Frequency**| Every fuel fill-up event |

### Preconditions
1. The vehicle and driver are registered in the system.
2. At least one fuel card has been issued and linked to the driver or vehicle.

### Main Flow
1. The Driver or Fleet Manager opens the Fuel module and selects **Log Fill-Up**.
2. The user enters: vehicle, fuel card number (or selects from linked cards), fuel station name and location, fuel type (diesel, petrol, AdBlue), volume (litres), unit price, total cost, and current odometer reading.
3. The system validates the fuel card number against the active fuel card register. If the card is issued by an integrated provider (WEX or Fleetcor), the system submits a transaction verification request to the fuel card API and awaits confirmation.
4. Upon successful validation, the system creates a `FuelRecord` linked to the vehicle, driver, and trip (if a trip is currently active or was completed within the last 2 hours).
5. The system recalculates the vehicle's fuel efficiency metrics: litres per 100 km based on the distance driven since the previous fill-up and the volume of fuel added.
6. The system updates the fleet-wide fuel analytics dashboard: monthly spend, average fuel efficiency by vehicle class, and cost-per-km trends.
7. If the calculated fuel efficiency deviates by more than 20% from the vehicle's baseline (trailing 90-day average), the system flags the record for Fleet Manager review and sends an anomaly alert.

### Alternative Flows
- **AF-01 Fuel Card Not Integrated:** If the fuel card provider is not integrated, the system accepts manual entry without API verification and marks the record as `MANUALLY_VERIFIED`.
- **AF-02 Bulk Import:** A Fleet Manager can upload a CSV export from a fuel card provider's portal. The system parses each row, matches records to vehicles by card number, and bulk-creates fuel records.

### Exception Flows
- **EF-01 Fuel Card Declined:** If the fuel card API returns a decline status, the system blocks record creation and displays the decline reason (e.g., card suspended, over limit). The Fleet Manager is notified.
- **EF-02 Odometer Regression:** If the entered odometer reading is lower than the previous logged reading for the vehicle, the system rejects the entry and prompts the user to verify the reading.

### Postconditions
1. A validated `FuelRecord` exists in the system linked to the vehicle and driver.
2. Fuel efficiency metrics for the vehicle have been recalculated.
3. If applicable, a fuel anomaly alert has been generated for Fleet Manager review.

---

## UC-05: Manage Geofence

| Field        | Value |
|--------------|-------|
| **ID**       | UC-05 |
| **Name**     | Manage Geofence |
| **Actors**   | Fleet Manager (primary), System (secondary), GPS Device (secondary) |
| **Priority** | High |
| **Frequency**| Zone creation is infrequent; event monitoring is continuous |

### Preconditions
1. The Fleet Manager is authenticated and holds the `GEOFENCE_ADMIN` permission.
2. At least one vehicle with an active GPS device is registered in the organisation.

### Main Flow
1. The Fleet Manager navigates to the Geofencing module and selects **Create Zone**.
2. The Fleet Manager draws the zone boundary on the interactive map either by: (a) clicking to place polygon vertices, or (b) clicking a centre point and entering a radius in metres to define a circle.
3. The Fleet Manager enters zone metadata: name, description, zone type (Depot, Customer Site, Restricted Area, Service Boundary), and colour.
4. The Fleet Manager configures alert rules for the zone: trigger on entry, trigger on exit, or both; notification channels (push notification, email, SMS); recipient user groups; and quiet hours (time-of-day window during which alerts are suppressed).
5. The Fleet Manager optionally restricts the rule to specific vehicles or vehicle groups rather than the entire fleet.
6. The Fleet Manager saves the zone. The system persists the geofence geometry (stored as GeoJSON) and the associated alert rules to the database and loads the zone into the in-memory geofence evaluation cache.
7. From this point, every incoming GPS ping for vehicles in the applicable scope is evaluated against the zone using a point-in-polygon algorithm. If a state transition is detected (outside → inside, or inside → outside), the system creates a `GeofenceEvent` record containing: vehicle ID, driver ID, zone ID, event type (ENTER/EXIT), timestamp, and GPS coordinates.
8. The system dispatches notifications according to the alert rule configuration.

### Alternative Flows
- **AF-01 Edit Existing Zone:** The Fleet Manager selects an existing zone, modifies the boundary or alert rules, and saves. The system reloads the updated geometry into cache within 5 seconds.
- **AF-02 Deactivate Zone:** Zones can be deactivated without deletion, preserving historical event data while stopping new event generation.

### Postconditions
1. The geofence zone is active and monitored in real time.
2. All vehicles within scope have their GPS pings evaluated against the new zone.
3. Historical geofence events are queryable in the Alerts log.

---

## UC-06: Process Incident Report

| Field        | Value |
|--------------|-------|
| **ID**       | UC-06 |
| **Name**     | Process Incident Report |
| **Actors**   | Driver (primary), Fleet Manager (secondary), Compliance Officer (secondary), System (secondary), External Integrations/Insurance API (secondary) |
| **Priority** | High |
| **Frequency**| As incidents occur |

### Preconditions
1. The Driver is authenticated in the mobile application and has an active or recently completed vehicle assignment.
2. The incident has occurred and the driver is in a safe location to report it.

### Main Flow
1. The Driver opens the mobile app and taps **Report Incident**.
2. The Driver selects the incident type from a predefined list: Collision, Near-Miss, Cargo Damage, Mechanical Failure, Theft, Traffic Infringement, or Other.
3. The Driver completes the incident form: date and time (auto-populated), location (auto-populated from GPS), description, third-party details (if collision), police report number (if applicable), and injury status.
4. The Driver uploads one or more photos of the scene, vehicle damage, and any third-party vehicles using the device camera or photo library. Photos are uploaded to secure cloud storage (S3) and linked to the incident record.
5. The Driver submits the report. The system creates an `IncidentRecord` with status `SUBMITTED`, persists all attachments, and sends an immediate push notification and email to the Fleet Manager.
6. The Fleet Manager reviews the submitted incident in the Compliance module and assigns a severity level: Low, Medium, High, or Critical. They add internal notes and acknowledge the report, transitioning its status to `UNDER_REVIEW`.
7. The Compliance Officer reviews the incident for regulatory implications. For High or Critical severity incidents, they assess whether an insurance claim needs to be filed.
8. If an insurance claim is required, the Compliance Officer initiates the claim by completing the insurance filing form within the FMS. The system submits the claim data to the integrated insurance API, attaching the photos and incident description.
9. The insurance API returns a claim reference number, which the system stores on the incident record.
10. The Compliance Officer updates the incident status to `CLAIM_FILED` or `CLOSED` (if no claim is needed), adding a resolution summary.
11. The system notifies the Driver of the outcome via push notification.

### Exception Flows
- **EF-01 Photo Upload Failure:** If a photo fails to upload due to network issues, the system queues it for retry and allows the driver to submit the report without the attachment. The driver is notified when the photo uploads successfully in the background.
- **EF-02 Insurance API Unavailable:** If the insurance API is unreachable, the system saves the claim data locally and retries submission every 15 minutes, alerting the Compliance Officer.

### Postconditions
1. A complete incident record exists with all attachments, notes, and severity classification.
2. If applicable, an insurance claim has been filed and the claim reference number is stored.
3. All involved parties have been notified of the incident outcome.

---

## UC-07: Generate IFTA Report

| Field        | Value |
|--------------|-------|
| **ID**       | UC-07 |
| **Name**     | Generate IFTA Report |
| **Actors**   | Compliance Officer (primary), System (secondary) |
| **Priority** | Medium |
| **Frequency**| Quarterly |

### Preconditions
1. The Compliance Officer is authenticated and holds the `COMPLIANCE_REPORTING` permission.
2. Trip data for the requested quarter exists in the system with complete GPS waypoint records for all vehicles subject to IFTA (vehicles with a gross vehicle weight rating > 26,000 lbs or having 3 or more axles).
3. Fuel records for the quarter have been entered and reconciled.

### Main Flow
1. The Compliance Officer navigates to the Compliance module and selects **Generate IFTA Report**.
2. The Compliance Officer selects the reporting quarter (Q1–Q4) and tax year, and chooses the home jurisdiction (base state/province).
3. The system retrieves all completed trips for IFTA-applicable vehicles within the selected quarter.
4. For each trip, the system traces the GPS waypoint sequence against a jurisdiction boundary dataset to determine the distance driven in each state or province. Boundary crossings are identified by evaluating each consecutive waypoint pair against jurisdiction polygon boundaries.
5. The system aggregates total miles driven per jurisdiction across all qualifying vehicles and all trips in the quarter.
6. The system retrieves total fuel purchased per jurisdiction (from fuel records where the fill-up location falls within that jurisdiction's boundary).
7. The system calculates the IFTA tax owed or refund due per jurisdiction using the formula:
   - **Taxable Gallons per Jurisdiction** = (Total Fleet Miles in Jurisdiction / Total Fleet Miles) × Total Fuel Consumed
   - **Tax Due** = (Taxable Gallons − Fuel Purchased in Jurisdiction) × Jurisdiction Tax Rate
8. The system renders the IFTA quarterly return in the standard IFTA schedule format, listing each jurisdiction, miles, fuel purchased, taxable gallons, tax rate, and net tax due/credit.
9. The system generates a PDF of the completed return and makes it available for download.
10. The Compliance Officer reviews the report, and if satisfied, marks it as `FILED` and records the submission date.

### Alternative Flows
- **AF-01 Missing Trip Data:** If any IFTA-applicable vehicle has trips with incomplete waypoint sequences for the quarter (GPS gaps > 10% of total distance), the system flags those trips in a data quality warning and calculates the report using available data, noting the estimated figures.

### Postconditions
1. The IFTA quarterly return PDF has been generated and archived in the compliance document store.
2. The report record is marked as filed with the submission date recorded.
3. Per-jurisdiction mileage and fuel data used to calculate the report is retained for 4 years per IFTA record-keeping requirements.

---

## UC-08: Score Driver Performance

| Field        | Value |
|--------------|-------|
| **ID**       | UC-08 |
| **Name**     | Score Driver Performance |
| **Actors**   | System (primary), Fleet Manager (secondary), Driver (secondary) |
| **Priority** | Medium |
| **Frequency**| After every completed trip; rolling score recalculated daily |

### Preconditions
1. A trip has been completed and its status is `ARCHIVED`.
2. The trip contains at least one waypoint with speed data.

### Main Flow
1. Upon a trip transitioning to `ARCHIVED` status, the system enqueues a driver score calculation job for the associated driver and trip.
2. The scoring engine retrieves all driving behaviour events recorded during the trip: speeding events, harsh braking events, harsh acceleration events, and sharp cornering events.
3. The system calculates a **Trip Score** (0–100) using a weighted deduction model:
   - Base score: 100
   - Each speeding event: −3 points (capped at −30 total for speeding)
   - Each harsh braking event: −5 points (capped at −25 total)
   - Each harsh acceleration event: −3 points (capped at −15 total)
   - Each sharp cornering event: −2 points (capped at −10 total)
   - Score cannot go below 0.
4. The system stores the Trip Score on the trip record.
5. The system retrieves all trip scores for the driver over the trailing 30-day window.
6. The system calculates the driver's **Rolling 30-Day Score** as an exponential weighted moving average, where more recent trips are weighted more heavily (decay factor λ = 0.1).
7. The system updates the `driverScore` field on the driver profile with the new rolling score.
8. If the rolling score drops below the configured threshold (default: 70), the system creates a performance alert and notifies the Fleet Manager, recommending coaching intervention.
9. If a single trip score falls below 50 (high-risk trip), the system creates an immediate high-priority alert regardless of the rolling score threshold.
10. The updated score is immediately visible to the Fleet Manager in the Driver Management module and to the Driver in their mobile app profile.

### Alternative Flows
- **AF-01 Insufficient Trip Data:** If a trip is very short (< 2 km) or contains fewer than 5 waypoints, the system calculates a trip score but applies a low-confidence flag and excludes the trip from the rolling average calculation to prevent distortion.

### Postconditions
1. The completed trip record contains a calculated Trip Score.
2. The driver's rolling 30-day performance score has been updated.
3. Any performance threshold alerts have been created and dispatched.
