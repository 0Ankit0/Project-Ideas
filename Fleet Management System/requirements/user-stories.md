# Fleet Management System — User Stories

**Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-01  
**Total Stories:** 45  
**Roles Covered:** Fleet Manager, Driver, Dispatcher, Mechanic, Compliance Officer, Executive, Tenant Administrator

---

## Table of Contents

- [Vehicle Management Stories](#vehicle-management-stories) (US-01 – US-08)
- [Driver Management Stories](#driver-management-stories) (US-09 – US-15)
- [GPS Tracking & Geofencing Stories](#gps-tracking--geofencing-stories) (US-16 – US-22)
- [Maintenance Management Stories](#maintenance-management-stories) (US-23 – US-28)
- [Fuel Management Stories](#fuel-management-stories) (US-29 – US-32)
- [Compliance & HOS Stories](#compliance--hos-stories) (US-33 – US-38)
- [Incident Management Stories](#incident-management-stories) (US-39 – US-41)
- [Reporting & Analytics Stories](#reporting--analytics-stories) (US-42 – US-45)

---

## Vehicle Management Stories

---

### US-01: Register a New Vehicle

**As a** Fleet Manager, **I want** to register a new vehicle by entering its VIN and having the system auto-populate the vehicle details, **so that** I can add vehicles to the fleet quickly and accurately without manually looking up make, model, and specification data.

**Acceptance Criteria:**

- **Given** I am logged in as a Fleet Manager and navigate to "Add Vehicle",
  **When** I enter a valid 17-character VIN and click "Decode",
  **Then** the system calls the NHTSA VIN decoder API and populates make, model, year, GVWR, and fuel type fields within 3 seconds.

- **Given** I have decoded a VIN and filled in the remaining required fields (license plate, state, registration expiration),
  **When** I click "Register Vehicle",
  **Then** the vehicle is saved with status `active`, appears in my vehicle list, and I receive a success confirmation.

- **Given** I enter a VIN that is already registered in my tenant,
  **When** I attempt to decode it,
  **Then** the system displays an error: "This VIN is already registered. View existing vehicle?" with a link to the duplicate record.

- **Given** I enter a malformed VIN (not 17 characters, or containing invalid characters I/O/Q),
  **When** I click "Decode",
  **Then** the system rejects the input with a descriptive inline validation error before making any API call.

---

### US-02: Bulk Import Vehicles via CSV

**As a** Fleet Manager, **I want** to import a batch of vehicles from a CSV file, **so that** I can onboard a large fleet acquisition or annual renewal without entering each vehicle individually.

**Acceptance Criteria:**

- **Given** I download the CSV template from the import page,
  **When** I open it,
  **Then** it contains columns for: vin, license_plate, state, registration_expiry, insurance_policy, insurance_expiry, vehicle_class, and asset_group.

- **Given** I upload a CSV with 500 rows where 490 are valid and 10 have validation errors (e.g., malformed VIN, missing required field),
  **When** the import runs,
  **Then** none of the 500 vehicles are committed, and I receive a downloadable error report listing each failed row number, column name, and specific error message.

- **Given** I upload a valid CSV with all rows passing validation,
  **When** I confirm the import,
  **Then** all vehicles are created, I receive a summary showing the count of vehicles imported, and all new vehicles appear in my vehicle list within 30 seconds.

- **Given** I upload a CSV containing VINs that already exist in my tenant,
  **When** the validation runs,
  **Then** the duplicate rows are flagged as errors in the error report with the message "VIN already registered."

---

### US-03: Manage Vehicle Documents

**As a** Fleet Manager, **I want** to upload and track expiration dates for vehicle compliance documents, **so that** I am never caught with an expired registration or insurance policy during a roadside inspection.

**Acceptance Criteria:**

- **Given** I am on a vehicle's profile page,
  **When** I click "Add Document" and select the document type "Registration Certificate",
  **Then** I am prompted to upload a file (PDF or image, max 10 MB), enter the issuing authority, effective date, and expiration date.

- **Given** a vehicle has a registration document expiring in 45 days,
  **When** the daily compliance check runs,
  **Then** the fleet manager and any designated recipients receive an email alert: "Vehicle [ID] registration expires in 45 days. Renewal required."

- **Given** a vehicle document has expired,
  **When** a dispatcher attempts to assign that vehicle to a trip,
  **Then** a warning banner appears: "This vehicle has 1 expired document (Registration). Review before dispatching." The dispatcher can override with a justification note.

- **Given** I am viewing the compliance dashboard,
  **When** I filter by "Document Status: Expiring within 30 days",
  **Then** the table shows all vehicles and document types meeting that filter, sorted by days remaining (ascending).

---

### US-04: Change Vehicle Operational Status

**As a** Fleet Manager, **I want** to change a vehicle's operational status and have that change tracked, **so that** dispatchers see only available vehicles and I have an audit trail for compliance purposes.

**Acceptance Criteria:**

- **Given** a vehicle with status `active`,
  **When** I change its status to `in_maintenance` and enter the reason "Scheduled PM - oil change and tire rotation",
  **Then** the status updates immediately, the vehicle is removed from the available dispatch pool, and the change is recorded in the audit history with my user ID, timestamp, and reason.

- **Given** a vehicle with status `in_maintenance`,
  **When** I attempt to assign it to a trip in the dispatch board,
  **Then** the system blocks the assignment and displays: "Vehicle is currently in maintenance. Change status to active before dispatching."

- **Given** I am viewing the audit trail for a vehicle,
  **When** I filter by "Status Changes",
  **Then** I see all historical status transitions with previous status, new status, user, timestamp, and reason displayed chronologically.

---

### US-05: View Vehicle Assignment History

**As a** Fleet Manager, **I want** to see a chronological history of which drivers have operated a specific vehicle, **so that** I can investigate incidents, resolve disputes, and support compliance audits.

**Acceptance Criteria:**

- **Given** I am on a vehicle's profile page,
  **When** I click the "Assignment History" tab,
  **Then** I see a table listing every driver assignment record with: driver name, assignment start date/time, assignment end date/time, and mileage driven during the assignment period.

- **Given** I select a date range filter of "Last 90 days",
  **When** the filter is applied,
  **Then** only assignment records with any overlap in that range are shown, and the mileage column reflects only miles driven within the selected range.

- **Given** I click on a driver name in the assignment history,
  **Then** I navigate to that driver's profile page.

---

### US-06: Set Up Vehicle Asset Groups

**As a** Fleet Manager, **I want** to organize vehicles into named asset groups, **so that** I can view reports and apply policies at the group level rather than managing vehicles individually.

**Acceptance Criteria:**

- **Given** I create an asset group named "Refrigerated Trucks - Northeast" and add 35 vehicles to it,
  **When** I navigate to any standard report and filter by group "Refrigerated Trucks - Northeast",
  **Then** the report data includes only those 35 vehicles.

- **Given** I want to add a vehicle to a group,
  **When** I edit a vehicle profile and select a group from the dropdown,
  **Then** the vehicle is immediately associated with the group and appears in group-filtered views.

- **Given** a vehicle is in one group,
  **When** I assign it to a different group,
  **Then** it is removed from the previous group and the change is logged in the vehicle's audit trail.

---

### US-07: Track Vehicle Odometer

**As a** Fleet Manager, **I want** odometer readings to be captured automatically from telematics and validated against previous readings, **so that** maintenance schedules trigger at accurate mileage intervals without requiring manual data entry.

**Acceptance Criteria:**

- **Given** a telematics device reports an odometer value with each GPS ping,
  **When** the value is more than 500 miles higher than the last recorded reading in a single day,
  **Then** the system flags the reading as a potential odometer anomaly and queues it for manager review rather than automatically updating the odometer.

- **Given** a vehicle's telematics device is offline and a driver submits a manual odometer update via the mobile app,
  **When** the driver enters the reading and uploads an odometer photo,
  **Then** the reading is saved as "manual — pending review" and a notification is sent to the fleet manager to approve or reject it.

- **Given** a preventive maintenance schedule set to trigger at every 5,000-mile interval,
  **When** the vehicle's odometer crosses a 5,000-mile threshold,
  **Then** a maintenance work order is automatically created and the fleet manager and assigned mechanic are notified.

---

### US-08: Decommission a Vehicle

**As a** Fleet Manager, **I want** to decommission a vehicle that has been sold, totaled, or retired, **so that** it no longer appears in operational views but its historical data is preserved for compliance and reporting.

**Acceptance Criteria:**

- **Given** a vehicle with status `active` or `out_of_service`,
  **When** I select "Decommission" and confirm with a reason (sold, totaled, end of lease, retired),
  **Then** the vehicle status changes to `decommissioned`, it disappears from the dispatch board and live map, and a decommission record is saved with the date and reason.

- **Given** a decommissioned vehicle,
  **When** I run a historical mileage report for last year,
  **Then** the decommissioned vehicle's data is included in historical reports with a "decommissioned" label.

- **Given** a decommissioned vehicle,
  **When** I search for it by VIN or license plate,
  **Then** it appears in search results with a "Decommissioned" badge and I can view its full profile in read-only mode.

---

## Driver Management Stories

---

### US-09: Create a Driver Profile

**As a** Fleet Manager, **I want** to create a complete driver profile with CDL and medical certificate details, **so that** I can manage driver compliance and have all driver information in one place for DOT audits.

**Acceptance Criteria:**

- **Given** I navigate to "Add Driver" and fill in all required fields (full legal name, employee ID, CDL number, CDL class, CDL state, CDL expiration, medical certificate expiration, phone, email),
  **When** I click "Save",
  **Then** the driver profile is created, the driver receives an email invitation to set up their mobile app account, and the driver appears in my driver list.

- **Given** I enter a CDL expiration date that is already past,
  **When** I try to save the profile,
  **Then** the system saves the profile but marks the driver as "Non-compliant — CDL expired" and excludes them from available driver lists in the dispatch board.

- **Given** a driver profile has been created,
  **When** I upload their CDL document scan under the "Documents" tab,
  **Then** the document is stored and linked to the profile, visible to the driver in their mobile app.

---

### US-10: Assign a Driver to a Vehicle

**As a** Dispatcher, **I want** to assign an available driver to an available vehicle for a trip, **so that** the GPS tracking, HOS logging, and DVIR records are correctly linked to the right person-vehicle combination.

**Acceptance Criteria:**

- **Given** both the driver and vehicle are available (no conflicting active assignments),
  **When** I create an assignment with a start time and optional planned end time,
  **Then** the assignment is saved, the vehicle icon on the live map shows the driver's name, and the driver receives a push notification with the vehicle details.

- **Given** a driver already has an active assignment to another vehicle,
  **When** I attempt to assign them to a second vehicle,
  **Then** the system blocks the assignment and displays: "Driver [Name] is currently assigned to [Vehicle ID]. End that assignment before creating a new one."

- **Given** a vehicle has a critical open DVIR defect,
  **When** I attempt to assign any driver to that vehicle,
  **Then** the system blocks the assignment and displays: "Vehicle has an open out-of-service DVIR defect. Mechanic certification required before dispatch."

---

### US-11: View and Understand My Safety Score

**As a** Driver, **I want** to see my current safety score and the specific events that affected it, **so that** I can understand what behaviors I need to improve and track my progress over time.

**Acceptance Criteria:**

- **Given** I open the mobile app and navigate to "My Score",
  **When** the page loads,
  **Then** I see my overall score (0–100), a breakdown by category (speeding, harsh braking, rapid acceleration, cornering, phone usage), my score trend over the last 4 weeks, and my rank within my driver group.

- **Given** my score dropped 8 points this week,
  **When** I tap "What happened?",
  **Then** I see a list of specific driving events with: date, time, location on a map, event type, and the trip it occurred in — sorted by score impact (highest first).

- **Given** I achieve a score above 90 for the month,
  **When** the monthly score is calculated,
  **Then** I receive an in-app congratulations notification and a coaching card acknowledging my improvement.

---

### US-12: Conduct a Driver Performance Review

**As a** Fleet Manager, **I want** to review a driver's performance over the past month with a structured report, **so that** I can have an evidence-based coaching conversation and document the outcome.

**Acceptance Criteria:**

- **Given** I navigate to a driver's profile and select "Performance Review — Last 30 Days",
  **When** the report loads,
  **Then** I see: total miles driven, safety score (with prior month comparison), number of HOS violations, number of speeding events, fuel efficiency (MPG vs. fleet average), DVIR defect rate, and incident count.

- **Given** I am reviewing the report and want to add coaching notes,
  **When** I click "Add Review Note" and enter my observations,
  **Then** the note is saved with my name and timestamp, visible to me but not to the driver unless I check "Share with driver."

- **Given** I share a coaching note with the driver,
  **When** the driver opens the mobile app,
  **Then** they see the note in their "Feedback from Manager" section and can acknowledge it with a tap.

---

### US-13: Track Driver HOS in Real Time

**As a** Compliance Officer, **I want** to monitor the real-time HOS status of all drivers on duty, **so that** I can proactively intervene before a violation occurs and protect the company from FMCSA fines.

**Acceptance Criteria:**

- **Given** I navigate to the HOS dashboard,
  **When** the page loads,
  **Then** I see a list of all drivers currently on duty, each showing: current duty status, hours remaining in the 11-hour driving window, hours remaining in the 14-hour on-duty window, hours used in the 60/70-hour cycle, and a color indicator (green > 2 hours, yellow 1–2 hours, red < 1 hour).

- **Given** a driver has 30 minutes remaining in their 11-hour driving window,
  **When** the threshold is crossed,
  **Then** the driver's row turns yellow on my HOS dashboard, I receive a push notification, and the driver receives a warning in the mobile app.

- **Given** I click on a specific driver in the HOS dashboard,
  **When** the detail view opens,
  **Then** I see their duty status graph for the current 24-hour period and the previous 7 days, with any violations highlighted in red.

---

### US-14: Manage Required Driver Training

**As a** Fleet Manager, **I want** to assign and track mandatory training completions for all drivers, **so that** I can demonstrate due diligence in safety compliance and avoid liability.

**Acceptance Criteria:**

- **Given** I define a training type "Defensive Driving Refresher" with a 12-month recurrence,
  **When** I assign it to all drivers in the "Long-Haul" group,
  **Then** each driver gets a training record showing "due within 12 months of hire date or last completion," and the compliance dashboard shows 0% complete for newly assigned drivers.

- **Given** a driver's defensive driving training expires in 30 days,
  **When** the daily compliance check runs,
  **Then** the fleet manager receives an alert and the training item appears on the driver's compliance checklist.

- **Given** a driver completes a training and I mark it complete with the completion date,
  **When** the record is saved,
  **Then** the next due date is automatically calculated (completion date + 12 months) and the driver's compliance status updates to "compliant" for that training type.

---

### US-15: Invite a Driver to the Mobile App

**As a** Tenant Administrator, **I want** to invite drivers to activate their mobile app accounts, **so that** they can start logging HOS, completing DVIRs, and receiving dispatch notifications.

**Acceptance Criteria:**

- **Given** a driver profile exists with a valid email address,
  **When** I click "Send App Invitation",
  **Then** the driver receives an email with a deep link to download the app and a one-time activation code that expires in 72 hours.

- **Given** the driver clicks the link and enters the activation code,
  **When** they set their password and complete onboarding,
  **Then** their app account is linked to their driver profile, and I can see "App: Active" on their profile page.

- **Given** a driver did not receive or lost the invitation email,
  **When** I click "Resend Invitation",
  **Then** a new activation code is generated (invalidating the previous one), and a new invitation email is sent.

---

## GPS Tracking & Geofencing Stories

---

### US-16: Monitor All Vehicles on the Live Map

**As a** Dispatcher, **I want** to see all active vehicles on a real-time map with their current status, **so that** I can quickly identify the nearest available vehicle for a new pickup and monitor for any issues requiring intervention.

**Acceptance Criteria:**

- **Given** I open the dispatch map with 120 vehicles active,
  **When** the map loads,
  **Then** all 120 vehicles appear as icons with color coding by status (green = driving, blue = idling, grey = stopped/ignition off), updating positions without page refresh.

- **Given** I want to find the nearest available vehicle to a specific address,
  **When** I enter the address in the "Find Nearest" search box,
  **Then** the top 5 nearest available vehicles are highlighted on the map with their distance (straight-line), driver name, and current activity.

- **Given** I click on a specific vehicle icon on the map,
  **When** the popup appears,
  **Then** I see: vehicle ID, driver name, speed, heading, last update time, address (reverse geocoded), battery level (if telematics reports it), and quick-action buttons to send a message or view vehicle details.

---

### US-17: Create a Customer Delivery Geofence

**As a** Fleet Manager, **I want** to create a geofence around a customer's warehouse, **so that** arrival and departure times are automatically recorded for proof-of-delivery without requiring driver action.

**Acceptance Criteria:**

- **Given** I navigate to "Geofences" and click "Create New",
  **When** I draw a polygon around the customer's warehouse on the map and enter a name and associated vehicles,
  **Then** the geofence is saved and immediately active for the selected vehicles.

- **Given** a vehicle assigned to the geofence enters the defined area,
  **When** the entry event is detected (within 30 seconds),
  **Then** a timestamped entry event is logged with vehicle ID, driver ID, geofence name, and GPS coordinates, and the customer can receive an automated webhook notification if configured.

- **Given** the same vehicle subsequently exits the geofence,
  **When** the exit event is detected,
  **Then** an exit event is logged and a delivery record is created showing arrival time, departure time, and time spent at the location.

- **Given** I view the geofence event log filtered by "Last 7 Days" and a specific customer geofence,
  **Then** I see all entry/exit pairs with timestamps, enabling me to create an accurate billing report for the customer.

---

### US-18: Set Up an After-Hours Movement Alert

**As a** Fleet Manager, **I want** to receive an alert when a vehicle moves outside of my business's operating hours, **so that** I can immediately detect unauthorized vehicle use or theft.

**Acceptance Criteria:**

- **Given** I define operating hours for my fleet as Monday–Friday 06:00–20:00 and Saturday 07:00–14:00,
  **When** a vehicle's GPS reports movement (speed > 5 km/h) outside those hours,
  **Then** I receive a push notification and email within 2 minutes identifying the vehicle, driver (if assigned), current location, and the time the movement was detected.

- **Given** I receive an after-hours alert,
  **When** I click "View on Map" in the alert notification,
  **Then** I am taken directly to that vehicle on the live map, centered and zoomed on its current location.

- **Given** the vehicle is an authorized exception (e.g., overnight delivery),
  **When** I acknowledge the alert and add a note "Authorized — overnight delivery for Order #45231",
  **Then** the alert is marked as "Reviewed — No Action Required" and is dismissed from the active alert queue.

---

### US-19: Replay a Trip to Investigate a Speeding Complaint

**As a** Fleet Manager, **I want** to replay the GPS breadcrumb trail of a specific trip, **so that** I can investigate a speeding complaint from a member of the public and determine whether disciplinary action is warranted.

**Acceptance Criteria:**

- **Given** I navigate to a driver's trip history and select a specific trip,
  **When** I click "Replay Trip",
  **Then** a map loads with the full trip route drawn, and a playback control bar with play, pause, speed selector (1×, 5×, 10×, 30×), and a timeline scrubber.

- **Given** the trip had a speeding event,
  **When** I play the trip back and the vehicle icon reaches the speeding event marker,
  **Then** the vehicle icon changes color to red and the speed shown in the info panel reflects the recorded speed at that moment.

- **Given** I click on a speeding event marker on the timeline,
  **When** the detail popup opens,
  **Then** I see: exact timestamp, recorded speed, posted speed limit, street address, and the duration of the speeding event.

---

### US-20: Configure Speed Limit Alerts

**As a** Fleet Manager, **I want** to set custom speed alert thresholds, **so that** I receive alerts for driving that exceeds my company policy even when a driver is technically within the posted speed limit.

**Acceptance Criteria:**

- **Given** I configure a fleet-wide policy: alert when speed exceeds posted limit by more than 10 mph OR exceeds 75 mph regardless of posted limit,
  **When** a vehicle reaches 76 mph on a 65 mph highway,
  **Then** a speeding event is recorded (vehicle exceeded 75 mph absolute threshold) and logged on the driver's safety score.

- **Given** I configure vehicle-group-specific thresholds for "School Zone vehicles" set to alert at any speed exceeding 25 mph,
  **When** a vehicle in that group is recorded at 28 mph,
  **Then** a speeding event is generated using the group-level threshold, overriding the fleet-wide threshold.

- **Given** a speeding event is generated,
  **When** the alert notification is sent,
  **Then** it includes: vehicle ID, driver name, recorded speed, threshold exceeded, street address, and a link to the trip replay at the exact moment.

---

### US-21: Track a Vehicle in Real Time During a High-Value Delivery

**As a** Dispatcher, **I want** to lock focus on a single vehicle's movement during a high-value delivery run, **so that** I can immediately respond if the vehicle deviates from the planned route.

**Acceptance Criteria:**

- **Given** I click "Follow Vehicle" on a vehicle's map popup,
  **When** the vehicle moves,
  **Then** the map automatically pans to keep the vehicle centered without any manual interaction on my part, updating every 15 seconds.

- **Given** I have defined a route corridor geofence for the delivery,
  **When** the vehicle exits the corridor,
  **Then** I receive an immediate in-app alert and the vehicle icon turns orange on the map.

- **Given** I am following a vehicle and want to stop,
  **When** I click "Stop Following",
  **Then** the map returns to its previous view and no longer auto-pans for that vehicle.

---

### US-22: Archive and Export GPS History

**As a** Compliance Officer, **I want** to export the full GPS history for a vehicle for a specified date range, **so that** I can provide it as evidence in a legal proceeding or insurance claim.

**Acceptance Criteria:**

- **Given** I request a GPS history export for a vehicle for a 30-day date range,
  **When** I click "Export",
  **Then** the system generates a CSV file containing: timestamp, latitude, longitude, speed, heading, ignition state, and address (reverse geocoded) for every position record in that range, and emails me a download link within 10 minutes.

- **Given** I request a GPS history export for data older than 90 days (stored in cold storage),
  **When** I submit the request,
  **Then** the system informs me the data is in cold storage and will be available within 12 hours, sending an email notification when the export file is ready.

- **Given** the exported CSV file is opened,
  **When** I verify the data,
  **Then** timestamps are in ISO 8601 format with UTC timezone, and coordinates have 6 decimal places of precision.

---

## Maintenance Management Stories

---

### US-23: Schedule Preventive Maintenance

**As a** Fleet Manager, **I want** to create recurring preventive maintenance schedules for each vehicle, **so that** maintenance work orders are automatically generated before vehicles exceed service intervals and break down on the road.

**Acceptance Criteria:**

- **Given** I create a PM schedule for "Engine Oil Change" with triggers of every 5,000 miles OR every 90 days (whichever comes first),
  **When** I save the schedule and assign it to a vehicle with current odometer 47,200 miles,
  **Then** the system calculates the next due date as the earlier of: (current date + 90 days) or (52,200 miles), and displays the upcoming maintenance on the vehicle's profile.

- **Given** the vehicle's odometer reaches 52,100 miles (100 miles before the trigger),
  **When** the odometer threshold pre-alert fires,
  **Then** a work order is created with status "open" and priority "normal", and the assigned mechanic receives a notification.

- **Given** I want to apply the same PM schedule to all 35 vehicles in an asset group,
  **When** I select "Apply to Group" from the schedule configuration,
  **Then** all 35 vehicles get individual PM schedules with next-due dates calculated from each vehicle's current odometer and last service date.

---

### US-24: Complete a DVIR on the Mobile App

**As a** Driver, **I want** to complete my pre-trip DVIR on my phone in under 2 minutes, **so that** I meet FMCSA requirements without delaying my departure.

**Acceptance Criteria:**

- **Given** I open the mobile app and tap "Start Pre-Trip Inspection" for my assigned vehicle,
  **When** the inspection checklist loads,
  **Then** it shows all FMCSA Part 396.11 required items organized into logical sections (Engine, Cab, Lights, Tires, Brakes, Coupling Devices if applicable), with each item having a "Pass" / "Defect" toggle.

- **Given** I mark a brake light as defective,
  **When** I tap "Defect",
  **Then** I am prompted to add a note (mandatory) and optionally take a photo of the defect, and the item is categorized as "Minor" or "Major" (out-of-service) based on the pre-configured severity rules for that item type.

- **Given** I have marked all items and tapped "Complete Inspection",
  **When** I provide my digital signature,
  **Then** the DVIR is submitted with a timestamp, my digital signature, and the vehicle ID, and the fleet manager is notified of any defects immediately.

- **Given** I marked no defects,
  **When** the DVIR is submitted,
  **Then** the vehicle remains available for dispatch and the DVIR record shows "No defects noted" with my signature.

---

### US-25: Certify a DVIR Defect Repair

**As a** Mechanic, **I want** to certify that a defect identified in a DVIR has been repaired, **so that** the vehicle can be returned to service and the next driver's DVIR reflects the corrected condition.

**Acceptance Criteria:**

- **Given** a vehicle has an open DVIR defect (brake light out — minor),
  **When** I navigate to my work queue and open the linked DVIR,
  **Then** I see the defect details, the driver's note, and any attached photo.

- **Given** I have repaired the brake light,
  **When** I tap "Certify Repair" and provide my mechanic credentials (digital signature),
  **Then** the defect status changes to "Repaired — Certified", the vehicle is unlocked for dispatch, and the next driver's DVIR will show the previously repaired item for their confirmation.

- **Given** a vehicle has a major defect (out-of-service),
  **When** I certify the repair,
  **Then** the vehicle remains locked until the next driver completes a new pre-trip DVIR and confirms the item as "Pass" — satisfying the FMCSA requirement for driver co-certification of repairs.

---

### US-26: Create and Track a Work Order

**As a** Mechanic, **I want** to create a corrective maintenance work order when I identify a vehicle problem, **so that** the repair is tracked from discovery to completion with a full cost record.

**Acceptance Criteria:**

- **Given** I create a work order for vehicle VIN-XXXX with type "Corrective", description "Front left tie rod end worn — handling issue", priority "High", and parts list "1x Tie Rod End (Part #TR-4521) @ $89.00",
  **When** I save the work order,
  **Then** it appears in the open work order queue for the fleet manager, the vehicle is flagged on the dispatch board, and I receive a confirmation with the work order number.

- **Given** I have completed the repair and want to close the work order,
  **When** I update the status to "Completed" and enter actual labor hours (2.5 hrs) and parts consumed,
  **Then** the work order total cost is calculated (parts + labor at the tenant's configured labor rate), the vehicle's maintenance cost record is updated, and the fleet manager is notified of the completion.

- **Given** a fleet manager tries to dispatch a vehicle with an open "High" priority work order,
  **When** they attempt the assignment,
  **Then** the system presents a warning with the work order details and requires the manager to type "OVERRIDE" and provide a written justification before proceeding.

---

### US-27: Request Service from an External Provider

**As a** Fleet Manager, **I want** to route a work order to an approved external service provider when the vehicle breaks down outside my service area, **so that** the repair is tracked and costed within the system even when performed by a third party.

**Acceptance Criteria:**

- **Given** a vehicle breaks down and I create a corrective work order,
  **When** I assign it to an external service provider from my approved provider directory,
  **Then** the provider receives an email with the work order details, vehicle information, and my contact information.

- **Given** the external provider completes the repair and I enter the actual cost and invoice number,
  **When** I close the work order,
  **Then** the external cost is reflected in the vehicle's maintenance cost record, labeled as "External Service — [Provider Name]."

---

### US-28: View Maintenance History for a Vehicle

**As a** Fleet Manager, **I want** to see the complete maintenance history of a vehicle, **so that** I can make informed decisions about vehicle retention, resale, and upcoming maintenance needs.

**Acceptance Criteria:**

- **Given** I navigate to a vehicle's profile and click "Maintenance History",
  **When** the page loads,
  **Then** I see a chronological list of all completed work orders (preventive and corrective) with: date, work order type, description, labor hours, parts cost, labor cost, total cost, and the mechanic or service provider who performed the work.

- **Given** I filter by "Work Order Type: Preventive Maintenance",
  **When** the filter is applied,
  **Then** only PM records are shown, and I can confirm compliance with the scheduled service intervals.

- **Given** I click the "Export" button,
  **When** the export runs,
  **Then** I receive a PDF formatted as a vehicle service history report suitable for inclusion in a vehicle resale package.

---

## Fuel Management Stories

---

### US-29: Log a Fuel Transaction Manually

**As a** Driver, **I want** to log a fuel fill-up from the mobile app immediately after fueling, **so that** my fleet manager has accurate fuel consumption data and I have a record of the transaction.

**Acceptance Criteria:**

- **Given** I tap "Log Fuel" in the mobile app,
  **When** the form loads,
  **Then** it pre-populates the current date/time and GPS location (converted to address), and I enter: fuel type, quantity (gallons), total cost, and optionally the station name and pump number.

- **Given** I submit the fuel record,
  **When** it is saved,
  **Then** the fuel transaction appears in the vehicle's fuel log, the MPG for the trip since the last fill is calculated (if previous odometer is known), and the transaction is included in the next IFTA report calculation.

- **Given** the quantity I entered would imply more fuel than the vehicle's tank capacity,
  **When** I submit the record,
  **Then** the system prompts: "This quantity (65 gal) exceeds the tank capacity for this vehicle (50 gal). Please verify. [Edit] [Submit Anyway]."

---

### US-30: Detect Potential Fuel Theft

**As a** Fleet Manager, **I want** the system to automatically flag suspicious fuel transactions, **so that** I can investigate and stop fuel card misuse before it becomes a significant cost.

**Acceptance Criteria:**

- **Given** a fuel card transaction is imported showing 55 gallons charged to vehicle XYZ-001,
  **When** the tank-level sensor recorded only a 40-gallon fill event at the same timestamp,
  **Then** the system generates a fuel discrepancy alert: "15-gallon discrepancy on [Date] at [Location] for Vehicle XYZ-001. Card charge: 55 gal. Sensor fill: 40 gal." assigned to the fleet manager.

- **Given** I receive the alert and click "Investigate",
  **When** the investigation detail view opens,
  **Then** I see side-by-side: the fuel card transaction data and the tank sensor event data, plus the vehicle's GPS track showing whether the vehicle was at the fueling location at the time of the transaction.

- **Given** I determine the discrepancy is a sensor calibration error,
  **When** I close the alert with reason "Sensor error — calibration scheduled",
  **Then** the alert is resolved, and the fuel records are marked as reviewed.

---

### US-31: Analyze Fleet Fuel Efficiency

**As a** Fleet Manager, **I want** to compare fuel efficiency across vehicles and drivers, **so that** I can identify vehicles due for engine servicing and drivers who need eco-driving coaching.

**Acceptance Criteria:**

- **Given** I navigate to the Fuel Efficiency report and set the date range to "Last Quarter",
  **When** the report loads,
  **Then** I see a ranked table of all vehicles by MPG (ascending, worst first), each row showing: vehicle ID, vehicle type, total miles, total gallons, MPG, fleet average MPG, and variance from average.

- **Given** I switch the dimension to "By Driver",
  **When** the report updates,
  **Then** the same MPG analysis is shown per driver, enabling me to identify drivers whose behavior (heavy acceleration, speeding) reduces fuel efficiency regardless of which vehicle they drive.

- **Given** a vehicle's MPG drops more than 15% compared to its 3-month rolling average,
  **When** the weekly efficiency analysis runs,
  **Then** an alert is generated recommending an engine inspection, as the efficiency drop may indicate a developing mechanical issue.

---

### US-32: Generate an IFTA Quarterly Report

**As a** Compliance Officer, **I want** to generate a complete IFTA quarterly report, **so that** I can calculate our fuel tax obligations by jurisdiction and submit the return on time without manual mileage calculations.

**Acceptance Criteria:**

- **Given** I navigate to Compliance > IFTA Reports and select Q3 2025 and my IFTA license number,
  **When** I click "Generate Report",
  **Then** the system calculates miles driven per state/province for all qualified vehicles by cross-referencing GPS trip data with jurisdiction boundary maps, and fuel gallons purchased per jurisdiction from fuel transaction records.

- **Given** the report is generated,
  **When** I view it,
  **Then** it shows a jurisdiction table with: jurisdiction code, miles driven, taxable miles, gallons purchased, net taxable gallons, tax rate, and tax due/credit, totaling to a net balance for the quarter.

- **Given** I have reviewed and approved the report,
  **When** I click "Export",
  **Then** I can download it as a print-ready PDF and as an IFTA XML file for electronic submission to my base jurisdiction.

---

## Compliance & HOS Stories

---

### US-33: Change Duty Status from the Mobile App

**As a** Driver, **I want** to change my duty status (driving, on-duty not driving, off-duty, sleeper berth) from a single tap in the mobile app, **so that** my HOS log is always current and I avoid accidental violations.

**Acceptance Criteria:**

- **Given** my current status is "Off Duty" and I start the truck engine,
  **When** the ELD detects engine start and vehicle movement,
  **Then** my status automatically changes to "Driving" after the vehicle has moved for 60 seconds, and the app displays a notification confirming the automatic status change.

- **Given** I stop the truck and need to go on-duty not driving (pre-trip inspection),
  **When** I tap "On-Duty Not Driving" in the status selector,
  **Then** my status updates immediately, the duty status change is logged with the timestamp and GPS location, and my driving time stops accumulating.

- **Given** I need to edit a previous duty status entry because I forgot to change it,
  **When** I tap the entry in my log and select "Edit",
  **Then** I am required to enter a reason for the edit (mandatory field), the edited entry shows both original and revised values with my reason and a timestamp, and the edit is flagged for compliance officer review.

---

### US-34: Handle a DOT Roadside Inspection

**As a** Driver, **I want** to display my HOS logs to a DOT officer directly from the mobile app and transfer them electronically, **so that** I can comply with an inspection quickly and confidently without printing paper logs.

**Acceptance Criteria:**

- **Given** I am stopped for a DOT inspection and tap "DOT Inspection Mode",
  **When** the mode activates,
  **Then** the app displays the current 24-hour duty status graph and the previous 7 days of logs in the standard DOT-approved graph grid format, with no ability for me to edit records while in this mode.

- **Given** the officer requests an electronic transfer of my logs,
  **When** I select the transfer method (Bluetooth, USB, Web, or email) as instructed by the officer,
  **Then** the app transmits the required data file in the FMCSA-specified format, and I receive an on-screen confirmation that the transfer was successful.

- **Given** the officer identifies a violation in my logs,
  **When** I exit DOT Inspection Mode after the inspection,
  **Then** the inspection event is logged in the system with timestamp, location, and transfer method used, and the compliance officer receives a notification.

---

### US-35: Review and Certify Daily HOS Logs

**As a** Driver, **I want** to review and certify my daily HOS log at the end of each 24-hour period, **so that** I confirm my records are accurate and meet the FMCSA certification requirement.

**Acceptance Criteria:**

- **Given** my 24-hour log period ends (midnight recalculation),
  **When** I open the app,
  **Then** I see a prompt: "Please review and certify your log for [Date]." with the full duty status graph displayed.

- **Given** I review my log and confirm it is accurate,
  **When** I tap "Certify Log" and provide my digital signature,
  **Then** the log is certified and locked from further edits by me (only the compliance officer can subsequently annotate it with a reason).

- **Given** I find an error in my log before certifying,
  **When** I make an edit with a reason,
  **Then** the edit is logged, and I can then certify the corrected log; the original and corrected versions are both preserved.

---

### US-36: Prepare a DOT Audit Package

**As a** Compliance Officer, **I want** to generate a complete compliance audit package for a specific fleet and date range in one click, **so that** I can respond to a DOT audit notice within 24 hours without scrambling to gather records from multiple systems.

**Acceptance Criteria:**

- **Given** I receive a DOT audit request for all vehicles and drivers for the past 6 months,
  **When** I navigate to Compliance > Audit Package and enter the date range and scope,
  **Then** the system generates a package containing: certified HOS logs for all drivers, DVIR records, vehicle inspection records, driver document status summary, IFTA reports for the covered quarters, and a violation summary.

- **Given** the audit package generation is complete (within 5 minutes),
  **When** I download it,
  **Then** it is a single ZIP file containing organized PDF reports and underlying data in CSV format, with a manifest document listing all included records and any records that have gaps.

- **Given** a gap is identified (e.g., a driver's logs are missing for 3 days),
  **When** the manifest lists the gap,
  **Then** it specifies the driver, date range, and reason (if known: ELD malfunction, non-ELD exempt operation, etc.) so I can address it proactively.

---

### US-37: Apply HOS Exemptions for Eligible Drivers

**As a** Compliance Officer, **I want** to configure eligible drivers for HOS exemptions (short-haul, adverse driving conditions, construction), **so that** the system does not generate false violations for exempt operations.

**Acceptance Criteria:**

- **Given** a driver qualifies for the short-haul exemption (operates within 150 air miles of reporting location),
  **When** I enable the short-haul exemption on their profile,
  **Then** the system applies the 14-hour/11-hour short-haul rules and does not require a 30-minute break for that driver, and the exemption is noted on their log.

- **Given** a driver invokes the adverse driving conditions exemption in the app,
  **When** they submit the exemption with their reason,
  **Then** their driving window is extended by 2 hours for that day, the exemption is recorded on their log, and the compliance officer receives a notification.

- **Given** a driver uses an exemption that does not apply to their operation (e.g., they drove more than 150 miles but used the short-haul exemption),
  **When** the nightly compliance check runs,
  **Then** a compliance alert is raised for the compliance officer to review and address.

---

### US-38: Configure and Review HOS Violation Reports

**As a** Compliance Officer, **I want** to review a weekly summary of all HOS violations across the fleet, **so that** I can identify systemic patterns (e.g., a specific route causing consistent 14-hour violations) and propose operational changes.

**Acceptance Criteria:**

- **Given** I navigate to Compliance > HOS Violations and set the date range to "Last 7 Days",
  **When** the report loads,
  **Then** I see a violations table with: driver name, violation date, violation type (11-hour, 14-hour, 30-minute break, cycle limit), hours over limit, and the route/assignment active at the time of violation.

- **Given** I group the violations by "Violation Type",
  **When** the grouping is applied,
  **Then** I see that 80% of violations are 30-minute break violations occurring on the I-95 corridor route, identifying it as the systemic issue to address with dispatch.

- **Given** I want to export the violations for a legal review,
  **When** I click "Export to PDF",
  **Then** the report is formatted as a formal compliance report with my company name, date range, total violations by type, and a per-driver detail section.

---

## Incident Management Stories

---

### US-39: Report a Collision from the Mobile App

**As a** Driver, **I want** to quickly report a collision from the mobile app immediately after the incident, **so that** the fleet manager and insurance team are notified right away and I don't have to remember details later.

**Acceptance Criteria:**

- **Given** I open the app and tap "Report Incident",
  **When** the form opens,
  **Then** the current date/time and GPS location are pre-populated, and I select incident type "Collision."

- **Given** I fill in the required fields (severity, description, whether emergency services were contacted) and attach 4 photos of the damage,
  **When** I tap "Submit Report",
  **Then** the incident is submitted, I receive a confirmation with an incident reference number, and the fleet manager and safety officer receive a push notification within 2 minutes.

- **Given** I submitted the report while offline (no data signal),
  **When** my phone regains connectivity,
  **Then** the report automatically syncs and submits with the original offline timestamp, and I receive a confirmation notification.

---

### US-40: Manage an Incident Investigation

**As a** Fleet Manager, **I want** to track the progress of an incident investigation from initial report to final resolution, **so that** every incident is properly documented, insurance claims are filed on time, and we capture lessons learned.

**Acceptance Criteria:**

- **Given** I receive an incident notification and open the incident record,
  **When** I assign an investigator and set the status to "Under Investigation",
  **Then** the assigned investigator receives a notification with the incident details and a link to the investigation workspace.

- **Given** the investigation reveals vehicle damage requiring repair,
  **When** I click "Create Linked Work Order" from the incident record,
  **Then** a corrective maintenance work order is created pre-populated with the vehicle ID and a reference to the incident number, so repair costs are automatically associated with the incident.

- **Given** the insurance claim has been filed,
  **When** I update the incident record with the claim number and set status to "Awaiting Insurance",
  **Then** the claim number is stored on the incident record and the incident appears in the "Awaiting Insurance" filtered view, which I review weekly.

---

### US-41: Run a Monthly Safety Incident Review

**As a** Fleet Manager, **I want** to generate a monthly incident summary report, **so that** I can identify unsafe drivers, dangerous routes, and recurring incident types to target for safety interventions.

**Acceptance Criteria:**

- **Given** I navigate to Reports > Incident Summary and select "Last Month",
  **When** the report loads,
  **Then** I see: total incidents by type, total incidents by severity, top 5 drivers by incident count, top 5 locations by incident count, and trend comparison vs. the prior month.

- **Given** a driver has 3 incidents in the past 90 days,
  **When** the monthly report runs,
  **Then** that driver is flagged in the "High Incident" category and a recommended action (coaching session, mandatory training, suspension pending review) appears based on the configured safety policy thresholds.

---

## Reporting & Analytics Stories

---

### US-42: View the Executive Fleet Dashboard

**As an** Executive, **I want** to see a single-page KPI dashboard that gives me an immediate read on fleet health, safety, and cost, **so that** I can quickly identify areas requiring my attention without digging through detailed reports.

**Acceptance Criteria:**

- **Given** I log in to the web dashboard with my Executive role,
  **When** the homepage loads,
  **Then** I see: total active vehicles, vehicles in maintenance (with trend arrow vs. last month), fleet-wide safety score (with trend), average fuel efficiency (MPG, with trend), cost per mile (last 30 days), open critical alerts count, and on-time delivery rate if dispatch integration is active.

- **Given** I click on the "Vehicles in Maintenance" KPI tile,
  **When** the drill-down opens,
  **Then** I see a list of vehicles currently in maintenance with: vehicle ID, maintenance reason, days in maintenance, and estimated return-to-service date.

- **Given** I want to see trend data for cost per mile over the past 12 months,
  **When** I click "View Trend" on the cost per mile tile,
  **Then** a line chart opens showing monthly cost per mile for the past 12 months with fleet average and a reference line for the industry benchmark if configured.

---

### US-43: Analyze Total Cost of Ownership per Vehicle

**As an** Executive, **I want** to see the total cost of ownership for each vehicle, **so that** I can make data-driven decisions about vehicle replacement and fleet composition.

**Acceptance Criteria:**

- **Given** I navigate to Reports > Total Cost of Ownership and set the date range to "Current Year",
  **When** the report loads,
  **Then** I see each vehicle with: fuel cost, maintenance cost (parts + labor), insurance cost (if entered), depreciation (if configured), and total cost, plus a cost-per-mile column.

- **Given** I sort the table by "Total Cost (Descending)",
  **When** the table re-sorts,
  **Then** the highest-cost vehicles are at the top, enabling me to identify candidates for early replacement.

- **Given** I click on a specific vehicle's total cost,
  **When** the cost breakdown opens,
  **Then** I see a monthly trend chart for each cost category (fuel, maintenance, insurance, depreciation) for the selected year.

---

### US-44: Schedule a Weekly Performance Report via Email

**As a** Fleet Manager, **I want** to schedule the driver performance report to be emailed to me and my operations manager every Monday morning, **so that** I start each week with up-to-date performance data without having to remember to log in and run the report.

**Acceptance Criteria:**

- **Given** I navigate to the Driver Performance report and configure the filters (all drivers, last 7 days),
  **When** I click "Schedule Report" and set "Every Monday at 07:00" with recipient emails,
  **Then** a scheduled job is created, and I receive a confirmation email.

- **Given** the scheduled time arrives (Monday 07:00),
  **When** the job runs,
  **Then** recipients receive an email with the report as a PDF attachment and a "View in Dashboard" link, reflecting data from the prior 7 days.

- **Given** I want to cancel the scheduled report,
  **When** I navigate to Settings > Scheduled Reports and delete the entry,
  **Then** no further emails are sent, and the deletion is logged in the audit trail.

---

### US-45: Export Fleet Data for External Analysis

**As an** Executive, **I want** to export raw fleet data (trips, fuel, maintenance, incidents) to Excel, **so that** our finance team can incorporate it into our quarterly business review without needing access to the FMS platform.

**Acceptance Criteria:**

- **Given** I navigate to Reports > Data Export and select "Trips", date range "Last Quarter", all vehicles,
  **When** I click "Export to XLSX",
  **Then** a multi-sheet Excel file is generated with: a summary sheet, a trips sheet (one row per trip with all trip fields), and a metadata sheet explaining each column, downloadable within 2 minutes.

- **Given** the dataset contains more than 100,000 rows,
  **When** I initiate the export,
  **Then** the system starts the export job in the background and emails me a download link when it is ready (within 10 minutes), rather than making me wait on screen.

- **Given** the downloaded file is opened in Excel,
  **When** I inspect the data,
  **Then** date columns are formatted as Excel date types (not text), numeric columns are formatted as numbers (not text), and currency columns include the unit (USD) in the column header.
